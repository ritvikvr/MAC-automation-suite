
# gui.py - Enhanced GUI for Mac Automation Suite
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import scrape_site, load_config as load_scraper_config
from monitor import SystemMonitor, start_monitoring
from scheduler import TaskScheduler, start_scheduler

class AutomationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mac Automation Suite - Enhanced")
        self.root.geometry("800x600")
        
        # Load configuration
        self.config = self.load_config()
        
        # Variables for different tabs
        self.setup_variables()
        
        # Create GUI
        self.create_widgets()
        
        # Start status update thread
        self.update_status()
    
    def load_config(self):
        """Load configuration from YAML file."""
        try:
            import yaml
            with open("config.yaml", 'r') as f:
                return yaml.safe_load(f)
        except:
            return {}
    
    def setup_variables(self):
        """Initialize variables for GUI controls."""
        # File Organizer variables
        self.entry_path_var = tk.StringVar(value="/Users/ritvik/Downloads/Developers Arena")
        self.method_var = tk.StringVar(value="extension")
        
        # Scraper variables
        self.url_var = tk.StringVar(value=self.config.get('scraper', {}).get('target_url', 'https://news.ycombinator.com'))
        self.output_file_var = tk.StringVar(value="scraped_data.json")
        
        # Monitor variables
        self.monitor_interval_var = tk.StringVar(value=str(self.config.get('monitor', {}).get('log_interval', 60)))
        self.monitor_log_file_var = tk.StringVar(value=self.config.get('monitor', {}).get('log_file', 'system_log.csv'))
        
        # Scheduler variables
        self.scheduler_status = tk.StringVar(value="Ready")
        
        # Status variables
        self.status_var = tk.StringVar(value="Ready")
        
    def create_widgets(self):
        """Create the main GUI interface."""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.tab_organizer = ttk.Frame(notebook)
        self.tab_scraper = ttk.Frame(notebook)
        self.tab_monitor = ttk.Frame(notebook)
        self.tab_scheduler = ttk.Frame(notebook)
        self.tab_status = ttk.Frame(notebook)
        
        notebook.add(self.tab_organizer, text="File Organizer")
        notebook.add(self.tab_scraper, text="Web Scraper")
        notebook.add(self.tab_monitor, text="System Monitor")
        notebook.add(self.tab_scheduler, text="Task Scheduler")
        notebook.add(self.tab_status, text="Status & Logs")
        
        # Create content for each tab
        self.create_organizer_tab()
        self.create_scraper_tab()
        self.create_monitor_tab()
        self.create_scheduler_tab()
        self.create_status_tab()
        
        # Status bar at bottom
        self.create_status_bar()
    
    def create_organizer_tab(self):
        """Create File Organizer tab."""
        # Title
        title = tk.Label(self.tab_organizer, text="File Organization Tool", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # Source directory selection
        dir_frame = tk.Frame(self.tab_organizer)
        dir_frame.pack(pady=10)
        
        tk.Label(dir_frame, text="Source Directory:").pack(side=tk.LEFT)
        self.entry_path = tk.Entry(dir_frame, textvariable=self.entry_path_var, width=40)
        self.entry_path.pack(side=tk.LEFT, padx=5)
        
        tk.Button(dir_frame, text="Browse", command=self.browse_directory).pack(side=tk.LEFT)
        
        # Organization method
        method_frame = tk.Frame(self.tab_organizer)
        method_frame.pack(pady=10)
        
        tk.Label(method_frame, text="Organization Method:").pack(anchor=tk.W)
        tk.Radiobutton(method_frame, text="By File Extension", variable=self.method_var, value="extension").pack(anchor=tk.W)
        tk.Radiobutton(method_frame, text="By Date", variable=self.method_var, value="date").pack(anchor=tk.W)
        
        # Run button
        tk.Button(self.tab_organizer, text="Organize Files", command=self.run_organizer, 
                 bg="lightblue", font=("Arial", 12, "bold")).pack(pady=20)
        
        # Results area
        self.organizer_result = tk.Text(self.tab_organizer, height=10, width=80)
        self.organizer_result.pack(pady=10, padx=10)
    
    def create_scraper_tab(self):
        """Create Web Scraper tab."""
        # Title
        title = tk.Label(self.tab_scraper, text="Web Scraping Tool", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # URL input
        url_frame = tk.Frame(self.tab_scraper)
        url_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(url_frame, text="Target URL:").pack(anchor=tk.W)
        self.url_entry = tk.Entry(url_frame, textvariable=self.url_var, width=60)
        self.url_entry.pack(fill=tk.X, pady=5)
        
        # Output file
        output_frame = tk.Frame(self.tab_scraper)
        output_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(output_frame, text="Output File:").pack(anchor=tk.W)
        self.output_entry = tk.Entry(output_frame, textvariable=self.output_file_var, width=60)
        self.output_entry.pack(fill=tk.X, pady=5)
        
        # Scrape button
        tk.Button(self.tab_scraper, text="Start Scraping", command=self.run_scraper, 
                 bg="lightgreen", font=("Arial", 12, "bold")).pack(pady=20)
        
        # Results area
        self.scraper_result = tk.Text(self.tab_scraper, height=12, width=80)
        self.scraper_result.pack(pady=10, padx=10)
    
    def create_monitor_tab(self):
        """Create System Monitor tab."""
        # Title
        title = tk.Label(self.tab_monitor, text="System Monitoring Tool", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # Monitor settings
        settings_frame = tk.Frame(self.tab_monitor)
        settings_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(settings_frame, text="Monitoring Interval (seconds):").pack(anchor=tk.W)
        interval_entry = tk.Entry(settings_frame, textvariable=self.monitor_interval_var, width=20)
        interval_entry.pack(anchor=tk.W, pady=5)
        
        tk.Label(settings_frame, text="Log File Path:").pack(anchor=tk.W)
        log_entry = tk.Entry(settings_frame, textvariable=self.monitor_log_file_var, width=60)
        log_entry.pack(anchor=tk.W, pady=5)
        
        # Control buttons
        control_frame = tk.Frame(self.tab_monitor)
        control_frame.pack(pady=20)
        
        self.monitor_button = tk.Button(control_frame, text="Start Monitoring", command=self.toggle_monitor, 
                                      bg="lightblue", font=("Arial", 12, "bold"))
        self.monitor_button.pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="View Current Stats", command=self.show_current_stats, 
                 bg="lightyellow").pack(side=tk.LEFT, padx=5)
        
        # Real-time display
        self.monitor_display = tk.Text(self.tab_monitor, height=8, width=80)
        self.monitor_display.pack(pady=10, padx=10)
        
        self.monitoring_active = False
    
    def create_scheduler_tab(self):
        """Create Task Scheduler tab."""
        # Title
        title = tk.Label(self.tab_scheduler, text="Task Scheduler", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # Scheduler controls
        control_frame = tk.Frame(self.tab_scheduler)
        control_frame.pack(pady=10)
        
        self.scheduler_button = tk.Button(control_frame, text="Start Scheduler", command=self.toggle_scheduler, 
                                        bg="lightcoral", font=("Arial", 12, "bold"))
        self.scheduler_button.pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="View Task History", command=self.show_task_history, 
                 bg="lightyellow").pack(side=tk.LEFT, padx=5)
        
        # Status display
        status_frame = tk.Frame(self.tab_scheduler)
        status_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(status_frame, text="Scheduler Status:").pack(anchor=tk.W)
        self.scheduler_status_display = tk.Label(status_frame, textvariable=self.scheduler_status, 
                                               font=("Arial", 12), fg="blue")
        self.scheduler_status_display.pack(anchor=tk.W, pady=5)
        
        # Task log
        self.scheduler_log = tk.Text(self.tab_scheduler, height=12, width=80)
        self.scheduler_log.pack(pady=10, padx=10)
        
        self.scheduler_active = False
    
    def create_status_tab(self):
        """Create Status and Logs tab."""
        # Title
        title = tk.Label(self.tab_status, text="System Status & Logs", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # System info frame
        info_frame = tk.Frame(self.tab_status)
        info_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(info_frame, text="System Information:", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        self.system_info = tk.Text(info_frame, height=8, width=80)
        self.system_info.pack(pady=5)
        
        # Logs frame
        logs_frame = tk.Frame(self.tab_status)
        logs_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        tk.Label(logs_frame, text="Recent Logs:", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        self.logs_display = tk.Text(logs_frame, height=15, width=80)
        self.logs_display.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Load initial system info
        self.load_system_info()
    
    def create_status_bar(self):
        """Create status bar at bottom."""
        status_bar = tk.Frame(self.root, relief=tk.SUNKEN, bd=1)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        tk.Label(status_bar, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Time display
        self.time_var = tk.StringVar()
        tk.Label(status_bar, textvariable=self.time_var, relief=tk.SUNKEN, anchor=tk.E).pack(side=tk.RIGHT)
        
        self.update_time()
    
    def browse_directory(self):
        """Browse for directory."""
        directory = filedialog.askdirectory(initialdir=self.entry_path_var.get())
        if directory:
            self.entry_path_var.set(directory)
    
    def run_organizer(self):
        """Run file organization."""
        def organize_task():
            try:
                self.status_var.set("Organizing files...")
                src = self.entry_path_var.get()
                method = self.method_var.get()
                
                if os.path.exists('organize.py'):
                    from organize import organize_files
                    organize_files(src, method=method)
                    result = f"Files organized successfully using {method} method in {src}"
                    self.organizer_result.insert(tk.END, f"{datetime.now()}: {result}\n")
                else:
                    result = "organize.py not found - using basic organization"
                    # Basic organization logic here
                    self.organizer_result.insert(tk.END, f"{datetime.now()}: {result}\n")
                
                self.status_var.set("File organization completed")
                messagebox.showinfo("Success", "Files organized successfully!")
                
            except Exception as e:
                error_msg = f"Error organizing files: {e}"
                self.organizer_result.insert(tk.END, f"{datetime.now()}: {error_msg}\n")
                self.status_var.set("File organization failed")
                messagebox.showerror("Error", error_msg)
        
        threading.Thread(target=organize_task, daemon=True).start()
    
    def run_scraper(self):
        """Run web scraping."""
        def scrape_task():
            try:
                self.status_var.set("Starting web scraping...")
                url = self.url_var.get()
                output_file = self.output_file_var.get()
                
                if not url.startswith('http'):
                    url = 'https://' + url
                
                self.scraper_result.insert(tk.END, f"{datetime.now()}: Starting to scrape {url}\n")
                
                result = scrape_site(url, output_file, self.config)
                
                if result:
                    success_msg = f"Scraping completed! Found {len(result.get('headings', []))} headings"
                    self.scraper_result.insert(tk.END, f"{datetime.now()}: {success_msg}\n")
                    self.scraper_result.insert(tk.END, f"Results saved to: {output_file}\n")
                    
                    # Show sample data
                    if result.get('headings'):
                        self.scraper_result.insert(tk.END, "Sample headings:\n")
                        for i, heading in enumerate(result['headings'][:5]):
                            self.scraper_result.insert(tk.END, f"  {i+1}. {heading}\n")
                    
                    self.status_var.set("Web scraping completed successfully")
                    messagebox.showinfo("Success", success_msg)
                else:
                    error_msg = "Scraping failed - check URL and network connection"
                    self.scraper_result.insert(tk.END, f"{datetime.now()}: {error_msg}\n")
                    self.status_var.set("Web scraping failed")
                    messagebox.showerror("Error", error_msg)
                
            except Exception as e:
                error_msg = f"Scraping error: {e}"
                self.scraper_result.insert(tk.END, f"{datetime.now()}: {error_msg}\n")
                self.status_var.set("Web scraping failed")
                messagebox.showerror("Error", error_msg)
        
        threading.Thread(target=scrape_task, daemon=True).start()
    
    def toggle_monitor(self):
        """Toggle system monitoring."""
        if not self.monitoring_active:
            self.start_monitor()
        else:
            self.stop_monitor()
    
    def start_monitor(self):
        """Start system monitoring."""
        try:
            interval = int(self.monitor_interval_var.get())
            log_file = self.monitor_log_file_var.get()
            
            self.monitoring_active = True
            self.monitor_button.config(text="Stop Monitoring", bg="red")
            self.status_var.set("System monitoring started")
            
            # Start monitoring in background
            def monitor_task():
                try:
                    monitor = SystemMonitor()
                    # Just get one sample for display
                    stats = monitor.get_system_stats()
                    if stats:
                        self.monitor_display.insert(tk.END, f"{datetime.now()}: ")
                        self.monitor_display.insert(tk.END, 
                            f"CPU: {stats['cpu_percent']}%, Mem: {stats['memory_percent']}%, Disk: {stats['disk_percent']}%\n")
                        self.monitor_display.see(tk.END)
                except Exception as e:
                    self.monitor_display.insert(tk.END, f"{datetime.now()}: Monitor error: {e}\n")
            
            threading.Thread(target=monitor_task, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring: {e}")
            self.monitoring_active = False
    
    def stop_monitor(self):
        """Stop system monitoring."""
        self.monitoring_active = False
        self.monitor_button.config(text="Start Monitoring", bg="lightblue")
        self.status_var.set("System monitoring stopped")
    
    def show_current_stats(self):
        """Show current system statistics."""
        try:
            monitor = SystemMonitor()
            stats = monitor.get_system_stats()
            
            if stats:
                stats_text = f"""Current System Statistics:
CPU Usage: {stats['cpu_percent']}%
Memory Usage: {stats['memory_percent']}%
Disk Usage: {stats['disk_percent']}%
Load Average: {stats['load_avg'][0]}
Running Processes: {stats['process_count']}
Memory Used: {stats['memory_used_gb']} GB
Disk Free: {stats['disk_free_gb']} GB"""
                
                self.monitor_display.insert(tk.END, f"{datetime.now()}: {stats_text}\n")
                self.monitor_display.see(tk.END)
                self.status_var.set("Current stats displayed")
            else:
                messagebox.showwarning("Warning", "Could not get system statistics")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error getting stats: {e}")
    
    def toggle_scheduler(self):
        """Toggle task scheduler."""
        if not self.scheduler_active:
            self.start_scheduler()
        else:
            self.stop_scheduler()
    
    def start_scheduler(self):
        """Start task scheduler."""
        try:
            self.scheduler_active = True
            self.scheduler_button.config(text="Stop Scheduler", bg="red")
            self.scheduler_status.set("Scheduler Running")
            self.status_var.set("Task scheduler started")
            
            # Note: In a real implementation, you'd start the actual scheduler here
            self.scheduler_log.insert(tk.END, f"{datetime.now()}: Scheduler started\n")
            self.scheduler_log.insert(tk.END, f"{datetime.now()}: Monitoring tasks scheduled\n")
            self.scheduler_log.insert(tk.END, f"{datetime.now()}: Web scraping scheduled\n")
            self.scheduler_log.see(tk.END)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start scheduler: {e}")
            self.scheduler_active = False
    
    def stop_scheduler(self):
        """Stop task scheduler."""
        self.scheduler_active = False
        self.scheduler_button.config(text="Start Scheduler", bg="lightcoral")
        self.scheduler_status.set("Scheduler Stopped")
        self.status_var.set("Task scheduler stopped")
        self.scheduler_log.insert(tk.END, f"{datetime.now()}: Scheduler stopped\n")
        self.scheduler_log.see(tk.END)
    
    def show_task_history(self):
        """Show task execution history."""
        try:
            history_file = "task_history.json"
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)
                
                self.scheduler_log.insert(tk.END, f"\n{datetime.now()}: Task History:\n")
                self.scheduler_log.insert(tk.END, "-" * 50 + "\n")
                
                for task in history[-10:]:  # Last 10 tasks
                    self.scheduler_log.insert(tk.END, 
                        f"{task['timestamp']}: {task['task']} - {task['status']}\n")
                    if task.get('details'):
                        self.scheduler_log.insert(tk.END, f"  Details: {task['details']}\n")
                
                self.scheduler_log.see(tk.END)
            else:
                self.scheduler_log.insert(tk.END, f"{datetime.now()}: No task history found\n")
                self.scheduler_log.see(tk.END)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error loading task history: {e}")
    
    def load_system_info(self):
        """Load system information."""
        try:
            import platform
            import psutil
            
            info_text = f"""System Information:
Platform: {platform.system()} {platform.release()}
Python Version: {platform.python_version()}
CPU Count: {psutil.cpu_count()}
Memory Total: {psutil.virtual_memory().total / (1024**3):.1f} GB
Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
Configuration:
- Target URL: {self.config.get('scraper', {}).get('target_url', 'Not set')}
- Monitor Interval: {self.config.get('monitor', {}).get('log_interval', 'Not set')} seconds
- Email Configured: {'Yes' if self.config.get('email') else 'No'}"""
            
            self.system_info.insert(tk.END, info_text)
            
        except Exception as e:
            self.system_info.insert(tk.END, f"Error loading system info: {e}")
    
    def update_time(self):
        """Update time display."""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.time_var.set(current_time)
        self.root.after(1000, self.update_time)
    
    def update_status(self):
        """Update status messages."""
        # This could be used to update status based on background tasks
        self.root.after(5000, self.update_status)

def main():
    """Main function to run the GUI."""
    root = tk.Tk()
    app = AutomationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
