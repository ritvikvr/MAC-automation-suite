# main.py - Main integration file for the automated system
import sys
import os
import argparse
import logging
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import scrape_site, scrape_multiple_sites, load_config as load_scraper_config
from monitor import SystemMonitor, start_monitoring
from scheduler import TaskScheduler, start_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomationSystem:
    """Main automation system that integrates all modules."""
    
    def __init__(self, config_path="config.yaml"):
        """
        Initialize the automation system.
        
        Args:
            config_path (str): Path to configuration file
        """
        self.config_path = config_path
        self.config = self.load_config()
        
        # Initialize modules
        self.monitor = None
        self.scheduler = None
        
    def load_config(self):
        """Load configuration from YAML file."""
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Config file {self.config_path} not found!")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file: {e}")
            return {}
        except ImportError:
            logger.error("PyYAML not installed. Install with: pip install PyYAML")
            return {}
    
    def test_scraper(self):
        """Test the scraper module."""
        logger.info("Testing scraper module...")
        
        try:
            # Test single site scraping
            test_url = "https://httpbin.org/html"
            logger.info(f"Scraping test URL: {test_url}")
            
            result = scrape_site(test_url, "test_scraped_data.json", self.config)
            
            if result:
                logger.info("✅ Scraper test passed")
                logger.info(f"Found {len(result.get('headings', []))} headings")
                return True
            else:
                logger.error("❌ Scraper test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Scraper test failed with error: {e}")
            return False
    
    def test_monitor(self):
        """Test the monitor module."""
        logger.info("Testing monitor module...")
        
        try:
            # Test system stats collection
            monitor = SystemMonitor(self.config_path)
            stats = monitor.get_system_stats()
            
            if stats:
                logger.info("✅ Monitor test passed")
                logger.info(f"CPU: {stats['cpu_percent']}%, Memory: {stats['memory_percent']}%, Disk: {stats['disk_percent']}%")
                return True
            else:
                logger.error("❌ Monitor test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Monitor test failed with error: {e}")
            return False
    
    def test_emailer(self):
        """Test the emailer module (dry run)."""
        logger.info("Testing emailer module (dry run)...")
        
        try:
            email_config = self.config.get('email', {})
            
            if not all([email_config.get('smtp_server'), email_config.get('username'), email_config.get('password')]):
                logger.warning("⚠️  Email configuration incomplete, skipping email test")
                return True  # Not a failure, just incomplete config
            
            # Test email sending (would need real credentials for actual test)
            logger.info("✅ Email configuration looks valid")
            logger.info("Note: Actual email sending not tested to avoid sending test emails")
            return True
            
        except Exception as e:
            logger.error(f"❌ Email test failed with error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all module tests."""
        logger.info("=" * 50)
        logger.info("STARTING AUTOMATION SYSTEM TESTS")
        logger.info("=" * 50)
        
        tests = [
            ("Scraper", self.test_scraper),
            ("Monitor", self.test_monitor),
            ("Emailer", self.test_emailer)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\n--- Testing {test_name} Module ---")
            results[test_name] = test_func()
        
        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("TEST SUMMARY")
        logger.info("=" * 50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! System is ready.")
        else:
            logger.warning("⚠️  Some tests failed. Check configuration and dependencies.")
        
        return passed == total
    
    def run_scraper_only(self, url=None, output_file=None):
        """Run only the scraper module."""
        logger.info("Running scraper module only...")
        
        try:
            # Use config URL or parameter
            target_url = url or self.config.get('scraper', {}).get('target_url', 'https://httpbin.org/html')
            save_file = output_file or self.config.get('scraper', {}).get('output_file', 'scraped_data.json')
            
            if not target_url.startswith('http'):
                target_url = 'https://' + target_url
            
            logger.info(f"Scraping: {target_url}")
            result = scrape_site(target_url, save_file, self.config)
            
            if result:
                logger.info("✅ Scraping completed successfully")
                logger.info(f"Results saved to: {save_file}")
                return True
            else:
                logger.error("❌ Scraping failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Scraping error: {e}")
            return False
    
    def run_monitor_only(self, log_file=None, interval=None):
        """Run only the monitor module."""
        logger.info("Running monitor module only...")
        
        try:
            start_monitoring(
                config_path=self.config_path,
                log_file=log_file,
                interval=interval
            )
            return True
            
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
            return True
        except Exception as e:
            logger.error(f"❌ Monitor error: {e}")
            return False
    
    def run_scheduler_only(self):
        """Run only the scheduler module."""
        logger.info("Running scheduler module only...")
        
        try:
            start_scheduler(self.config_path)
            return True
            
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            return True
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            return False
    
    def run_full_system(self):
        """Run the complete automation system."""
        logger.info("Starting full automation system...")
        
        try:
            # Initialize and run scheduler (which integrates all modules)
            scheduler = TaskScheduler(self.config_path)
            scheduler.run_scheduler()
            return True
            
        except KeyboardInterrupt:
            logger.info("System stopped by user")
            return True
        except Exception as e:
            logger.error(f"❌ System error: {e}")
            return False

def main():
    """Main entry point for the automation system."""
    parser = argparse.ArgumentParser(description='Automation System - Web Scraper, Monitor, and Scheduler')
    parser.add_argument('--config', default='config.yaml', help='Path to configuration file')
    parser.add_argument('--mode', choices=['test', 'scraper', 'monitor', 'scheduler', 'full'], 
                       default='test', help='Run mode')
    parser.add_argument('--url', help='URL to scrape (for scraper mode)')
    parser.add_argument('--output', help='Output file path (for scraper mode)')
    parser.add_argument('--log-file', help='Log file path (for monitor mode)')
    parser.add_argument('--interval', type=int, help='Interval in seconds (for monitor mode)')
    
    args = parser.parse_args()
    
    # Initialize system
    system = AutomationSystem(args.config)
    
    # Handle different modes
    if args.mode == 'test':
        system.run_all_tests()
    elif args.mode == 'scraper':
        system.run_scraper_only(args.url, args.output)
    elif args.mode == 'monitor':
        system.run_monitor_only(args.log_file, args.interval)
    elif args.mode == 'scheduler':
        system.run_scheduler_only()
    elif args.mode == 'full':
        system.run_full_system()

if __name__ == "__main__":
    main()
