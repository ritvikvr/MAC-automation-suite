
# monitor.py
import psutil
import time
import signal
import sys
import os
import logging
from datetime import datetime
import yaml
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = threading.Event()

class SystemMonitor:
    def __init__(self, config_path="config.yaml"):
        """
        Initialize system monitor with configuration.
        """
        self.config = self.load_config(config_path)
        self.monitor_config = self.config.get('monitor', {})
        
        # Set default values from config or use sensible defaults
        self.log_file = self.monitor_config.get('log_file', 'system_log.csv')
        self.log_interval = max(1, self.monitor_config.get('log_interval', 60))  # Minimum 1 second
        
        # Initialize file handle
        self.log_handle = None
        
    def load_config(self, config_path="config.yaml"):
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found. Using defaults.")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file: {e}")
            return {}
    
    def signal_handler(self, signum, frame):
        """Handle graceful shutdown on SIGINT (Ctrl+C) or SIGTERM."""
        logger.info("Received shutdown signal. Gracefully stopping monitor...")
        shutdown_flag.set()
    
    def validate_interval(self, interval):
        """Validate and sanitize interval parameter."""
        try:
            interval = int(interval)
            if interval < 1:
                logger.warning(f"Interval {interval}s is too low, setting to 1s")
                return 1
            elif interval > 86400:  # 24 hours max
                logger.warning(f"Interval {interval}s is too high, setting to 3600s")
                return 3600
            return interval
        except (ValueError, TypeError):
            logger.warning(f"Invalid interval {interval}, using default 60s")
            return 60
    
    def setup_file_handling(self):
        """Setup file handling with proper error handling."""
        try:
            # Check if file exists and has content
            file_exists = os.path.exists(self.log_file)
            
            if file_exists:
                # File exists, check if it has headers
                with open(self.log_file, 'r') as f:
                    first_line = f.readline().strip()
                    has_headers = "Timestamp,CPU_%,Mem_%,Disk_%" in first_line
            else:
                has_headers = False
            
            # Open file in append mode
            self.log_handle = open(self.log_file, 'a', buffering=1)  # Line buffering
            
            # Write headers if file is new or doesn't have them
            if not has_headers:
                self.log_handle.write("Timestamp,CPU_%,Mem_%,Disk_%,Load_Avg,Processes,Memory_Used_GB,Disk_Free_GB\n")
                self.log_handle.flush()
                logger.info(f"Created new log file: {self.log_file}")
            else:
                logger.info(f"Appending to existing log file: {self.log_file}")
                
        except IOError as e:
            logger.error(f"Failed to open log file {self.log_file}: {e}")
            raise
    
    def cleanup(self):
        """Cleanup resources."""
        if self.log_handle:
            try:
                self.log_handle.close()
                logger.info("Log file handle closed")
            except Exception as e:
                logger.error(f"Error closing log file: {e}")
    
    def get_system_stats(self):
        """
        Get comprehensive system statistics with error handling.
        
        Returns:
            dict: System statistics or None if failed
        """
        try:
            # CPU statistics
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            
            # Memory statistics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)  # Convert bytes to GB
            
            # Disk statistics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)  # Convert bytes to GB
            
            # Process count
            process_count = len(psutil.pids())
            
            return {
                'cpu_percent': round(cpu_percent, 2),
                'memory_percent': round(memory_percent, 2),
                'disk_percent': round(disk_percent, 2),
                'load_avg': [round(x, 2) for x in load_avg],
                'process_count': process_count,
                'memory_used_gb': round(memory_used_gb, 2),
                'disk_free_gb': round(disk_free_gb, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return None
    
    def log_system_stats(self, log_file=None, interval=None):
        """
        Logs CPU, memory, and disk usage to a CSV file every `interval` seconds.
        Supports graceful shutdown with Ctrl+C.
        
        Args:
            log_file (str): Path to log file (overrides config)
            interval (int): Log interval in seconds (overrides config)
        """
        # Override config if parameters provided
        if log_file:
            self.log_file = log_file
        if interval:
            self.log_interval = self.validate_interval(interval)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Setup file handling
            self.setup_file_handling()
            
            logger.info(f"Starting system monitoring (interval: {self.log_interval}s)")
            logger.info(f"Logging to: {self.log_file}")
            logger.info("Press Ctrl+C to stop gracefully")
            
            while not shutdown_flag.is_set():
                try:
                    # Get system statistics
                    stats = self.get_system_stats()
                    if stats is None:
                        logger.warning("Failed to get system stats, skipping this iteration")
                        time.sleep(self.log_interval)
                        continue
                    
                    # Format timestamp
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Create log line
                    line = (f"{timestamp},{stats['cpu_percent']},{stats['memory_percent']},{stats['disk_percent']},"
                           f"{stats['load_avg'][0]},{stats['process_count']},{stats['memory_used_gb']},{stats['disk_free_gb']}\n")
                    
                    # Write to file
                    self.log_handle.write(line)
                    self.log_handle.flush()
                    
                    # Print to console
                    print(f"{timestamp} - CPU: {stats['cpu_percent']}%, Mem: {stats['memory_percent']}%, "
                          f"Disk: {stats['disk_percent']}%, Load: {stats['load_avg'][0]}, "
                          f"Procs: {stats['process_count']}, Mem Used: {stats['memory_used_gb']}GB, "
                          f"Disk Free: {stats['disk_free_gb']}GB")
                    
                    # Wait for next interval or until shutdown
                    if shutdown_flag.wait(timeout=self.log_interval):
                        break  # Shutdown was requested
                        
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    if not shutdown_flag.is_set():
                        logger.info("Waiting 5 seconds before retrying...")
                        time.sleep(5)
            
        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error in monitoring: {e}")
        finally:
            self.cleanup()
            logger.info("System monitoring stopped")

def start_monitoring(config_path="config.yaml", log_file=None, interval=None):
    """
    Convenience function to start system monitoring.
    
    Args:
        config_path (str): Path to configuration file
        log_file (str): Path to log file (optional override)
        interval (int): Log interval in seconds (optional override)
    """
    try:
        monitor = SystemMonitor(config_path)
        monitor.log_system_stats(log_file=log_file, interval=interval)
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        sys.exit(1)

# Example usage:
if __name__ == "__main__":
    # Start monitoring with configuration
    start_monitoring()
