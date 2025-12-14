# scheduler.py

# scheduler.py
import schedule
import time
import signal
import sys
import logging
import threading
import yaml
import json
import os
from datetime import datetime
from scraper import scrape_site, load_config as load_scraper_config
from monitor import SystemMonitor
from emailer import send_email

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = threading.Event()

class TaskScheduler:
    def __init__(self, config_path="config.yaml"):
        """
        Initialize task scheduler with configuration.
        """
        self.config = self.load_config(config_path)
        self.scheduler_config = self.config.get('scheduler', {})
        self.task_history = []
        self.running = False
        
        # Set default values from config or use sensible defaults
        self.check_interval = self.scheduler_config.get('check_interval', 60)  # seconds
        self.log_file = self.scheduler_config.get('log_file', 'scheduler.log')
        
        # Initialize signal handlers
        self.setup_signal_handlers()
        
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
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle graceful shutdown on SIGINT (Ctrl+C) or SIGTERM."""
        logger.info("Received shutdown signal. Gracefully stopping scheduler...")
        shutdown_flag.set()
        self.running = False
    
    def log_task_execution(self, task_name, status, details=""):
        """Log task execution details."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task': task_name,
            'status': status,
            'details': details
        }
        self.task_history.append(log_entry)
        
        # Keep only last 100 entries
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-100:]
        
        logger.info(f"Task '{task_name}' {status}: {details}")
    
    # Task 1: Web Scraping Task
    def web_scraping_task(self):
        """Scheduled task for web scraping."""
        try:
            logger.info("Starting web scraping task...")
            
            # Get configuration for scraping
            scraper_config = self.config.get('scraper', {})
            target_url = scraper_config.get('target_url', 'https://news.ycombinator.com')
            output_file = scraper_config.get('output_file', 'scraped_data.json')
            
            if not target_url.startswith('http'):
                target_url = 'https://' + target_url
            
            # Perform scraping
            scraped_data = scrape_site(target_url, output_file, self.config)
            
            if scraped_data:
                self.log_task_execution("web_scraping", "SUCCESS", 
                                      f"Scraped {len(scraped_data.get('headings', []))} headings from {target_url}")
                
                # Send notification email if configured
                if self.config.get('email') and self.config['email'].get('enable_notifications', False):
                    self.send_scraping_notification(target_url, len(scraped_data.get('headings', [])))
            else:
                self.log_task_execution("web_scraping", "FAILED", "Failed to scrape website")
                
        except Exception as e:
            logger.error(f"Error in web scraping task: {e}")
            self.log_task_execution("web_scraping", "ERROR", str(e))
    
    # Task 2: System Monitoring Task
    def system_monitoring_task(self):
        """Scheduled task for system monitoring."""
        try:
            logger.info("Starting system monitoring task...")
            
            # Get system stats using the monitor module
            monitor = SystemMonitor()
            stats = monitor.get_system_stats()
            
            if stats:
                # Log critical system information
                if stats['cpu_percent'] > 80:
                    self.log_task_execution("system_monitoring", "WARNING", 
                                          f"High CPU usage: {stats['cpu_percent']}%")
                
                if stats['memory_percent'] > 85:
                    self.log_task_execution("system_monitoring", "WARNING", 
                                          f"High memory usage: {stats['memory_percent']}%")
                
                if stats['disk_percent'] > 90:
                    self.log_task_execution("system_monitoring", "CRITICAL", 
                                          f"High disk usage: {stats['disk_percent']}%")
                
                self.log_task_execution("system_monitoring", "SUCCESS", 
                                      f"CPU: {stats['cpu_percent']}%, Mem: {stats['memory_percent']}%, Disk: {stats['disk_percent']}%")
            else:
                self.log_task_execution("system_monitoring", "FAILED", "Could not get system stats")
                
        except Exception as e:
            logger.error(f"Error in system monitoring task: {e}")
            self.log_task_execution("system_monitoring", "ERROR", str(e))
    
    # Task 3: File Organization Task
    def file_organization_task(self):
        """Scheduled task for file organization."""
        try:
            logger.info("Starting file organization task...")
            
            # Get configuration for organization
            organize_config = self.config.get('organize', {})
            source_dir = organize_config.get('source_dir', '/Users/ritvik/Downloads/Developers Arena')
            
            # Check if organize.py exists and import it
            if os.path.exists('organize.py'):
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("organize", "organize.py")
                    organize_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(organize_module)
                    
                    # Call organization function if it exists
                    if hasattr(organize_module, 'organize_files'):
                        organize_module.organize_files(source_dir)
                        self.log_task_execution("file_organization", "SUCCESS", f"Organized files in {source_dir}")
                    else:
                        self.log_task_execution("file_organization", "SKIPPED", "No organize function found")
                except Exception as e:
                    self.log_task_execution("file_organization", "ERROR", f"Error importing organize module: {e}")
            else:
                self.log_task_execution("file_organization", "SKIPPED", "organize.py not found")
                
        except Exception as e:
            logger.error(f"Error in file organization task: {e}")
            self.log_task_execution("file_organization", "ERROR", str(e))
    
    # Task 4: Email Report Task
    def email_report_task(self):
        """Scheduled task for sending email reports."""
        try:
            logger.info("Starting email report task...")
            
            email_config = self.config.get('email', {})
            
            # Check if email is configured
            if not all([email_config.get('smtp_server'), email_config.get('username'), 
                       email_config.get('password')]):
                self.log_task_execution("email_report", "SKIPPED", "Email configuration incomplete")
                return
            
            # Generate report summary
            report_data = self.generate_task_report()
            
            # Send email
            send_email(
                to_addrs=[email_config.get('to_address', email_config.get('username'))],
                subject="Automated System Report",
                body=report_data,
                smtp_server=email_config.get('smtp_server'),
                smtp_port=email_config.get('smtp_port', 587),
                username=email_config.get('username'),
                password=email_config.get('password')
            )
            
            self.log_task_execution("email_report", "SUCCESS", "Report email sent")
            
        except Exception as e:
            logger.error(f"Error in email report task: {e}")
            self.log_task_execution("email_report", "ERROR", str(e))
    
    def send_scraping_notification(self, url, heading_count):
        """Send notification email about scraping results."""
        try:
            email_config = self.config.get('email', {})
            if not email_config.get('enable_notifications', False):
                return
            
            subject = f"Web Scraping Completed: {heading_count} headings found"
            body = f"Scraping completed successfully.\n\nURL: {url}\nHeadings found: {heading_count}\nTime: {datetime.now()}"
            
            send_email(
                to_addrs=[email_config.get('to_address', email_config.get('username'))],
                subject=subject,
                body=body,
                smtp_server=email_config.get('smtp_server'),
                smtp_port=email_config.get('smtp_port', 587),
                username=email_config.get('username'),
                password=email_config.get('password')
            )
        except Exception as e:
            logger.error(f"Failed to send scraping notification: {e}")
    
    def generate_task_report(self):
        """Generate a summary report of all tasks."""
        report = "Automated System Report\n"
        report += "=" * 30 + "\n\n"
        
        # Summary statistics
        total_tasks = len(self.task_history)
        successful_tasks = len([t for t in self.task_history if t['status'] == 'SUCCESS'])
        failed_tasks = len([t for t in self.task_history if t['status'] in ['FAILED', 'ERROR']])
        
        report += f"Total Tasks: {total_tasks}\n"
        report += f"Successful: {successful_tasks}\n"
        report += f"Failed: {failed_tasks}\n\n"
        
        # Recent tasks (last 10)
        report += "Recent Task History:\n"
        report += "-" * 20 + "\n"
        for task in self.task_history[-10:]:
            report += f"{task['timestamp']} - {task['task']}: {task['status']}\n"
            if task['details']:
                report += f"  Details: {task['details']}\n"
        
        return report
    
    def setup_scheduled_tasks(self):
        """Setup scheduled tasks based on configuration."""
        logger.info("Setting up scheduled tasks...")
        
        # Web scraping task
        scraping_schedule = self.scheduler_config.get('scraping_schedule', 'hourly')
        if scraping_schedule == 'hourly':
            schedule.every().hour.do(self.web_scraping_task)
        elif scraping_schedule == 'daily':
            schedule.every().day.at("09:00").do(self.web_scraping_task)
        elif scraping_schedule == 'weekly':
            schedule.every().week.do(self.web_scraping_task)
        
        # System monitoring task
        monitoring_schedule = self.scheduler_config.get('monitoring_schedule', 'every_30_minutes')
        if monitoring_schedule == 'every_15_minutes':
            schedule.every(15).minutes.do(self.system_monitoring_task)
        elif monitoring_schedule == 'every_30_minutes':
            schedule.every(30).minutes.do(self.system_monitoring_task)
        elif monitoring_schedule == 'hourly':
            schedule.every().hour.do(self.system_monitoring_task)
        
        # File organization task
        organization_schedule = self.scheduler_config.get('organization_schedule', 'daily')
        if organization_schedule == 'daily':
            schedule.every().day.at("02:00").do(self.file_organization_task)
        elif organization_schedule == 'weekly':
            schedule.every().week.do(self.file_organization_task)
        
        # Email report task
        email_schedule = self.scheduler_config.get('email_schedule', 'daily')
        if email_schedule == 'daily':
            schedule.every().day.at("08:00").do(self.email_report_task)
        elif email_schedule == 'weekly':
            schedule.every().week.do(self.email_report_task)
        
        logger.info("Scheduled tasks setup completed")
    
    def save_task_history(self):
        """Save task history to file."""
        try:
            history_file = self.scheduler_config.get('history_file', 'task_history.json')
            with open(history_file, 'w') as f:
                json.dump(self.task_history, f, indent=2)
            logger.info(f"Task history saved to {history_file}")
        except Exception as e:
            logger.error(f"Failed to save task history: {e}")
    
    def run_scheduler(self):
        """Run the scheduler with graceful shutdown support."""
        try:
            self.running = True
            self.setup_scheduled_tasks()
            
            logger.info("Task scheduler started")
            logger.info("Press Ctrl+C to stop gracefully")
            logger.info(f"Check interval: {self.check_interval} seconds")
            
            while not shutdown_flag.is_set() and self.running:
                try:
                    schedule.run_pending()
                    time.sleep(self.check_interval)
                    
                    # Save task history periodically (every 50 iterations)
                    if len(self.task_history) % 50 == 0 and len(self.task_history) > 0:
                        self.save_task_history()
                        
                except Exception as e:
                    logger.error(f"Error in scheduler loop: {e}")
                    if not shutdown_flag.is_set():
                        logger.info("Waiting 10 seconds before retrying...")
                        time.sleep(10)
            
        except KeyboardInterrupt:
            logger.info("Scheduler interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error in scheduler: {e}")
        finally:
            self.save_task_history()
            schedule.clear()
            logger.info("Task scheduler stopped")

def start_scheduler(config_path="config.yaml"):
    """
    Convenience function to start the task scheduler.
    
    Args:
        config_path (str): Path to configuration file
    """
    try:
        scheduler = TaskScheduler(config_path)
        scheduler.run_scheduler()
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        sys.exit(1)

# Example usage:
if __name__ == "__main__":
    start_scheduler()
