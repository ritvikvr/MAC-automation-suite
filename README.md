# MAC Automation Suite

MAC Automation Suite is a lightweight, modular Python toolkit that helps automate common tasks on macOS such as file organization, system monitoring, scheduled jobs, and notification/email workflows.

## Overview

MAC Automation Suite is designed as a collection of focused scripts that can be combined to build powerful automation pipelines on a Mac. It is ideal for developers and power users who want scriptable control over file management, monitoring, scheduling, and data collection without heavyweight dependencies.

## Features

- File organization of downloads or work directories based on rules (type, date, or custom logic) via `organize.py`.
- Lightweight system or directory monitoring with hooks for triggering other actions via `monitor.py`.
- Job scheduling to run automations at fixed times or intervals using `scheduler.py`.
- Email notifications or reports for automation events via `emailer.py`.
- Simple GUI launcher for common actions through `gui.py`.
- Data scraping or routine data collection through `scraper.py`.
- Central orchestration entrypoint using `main.py` to wire modules together.

## Project Structure

```text
MAC-automation-suite/
├─ main.py        # Main entrypoint and orchestrator
├─ gui.py         # GUI for triggering workflows
├─ monitor.py     # Monitoring logic
├─ organize.py    # File organization utilities
├─ scheduler.py   # Job scheduling module
├─ emailer.py     # Email notification helpers
├─ scraper.py     # Web/data scraping utilities
└─ README.md
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ritvikvr/MAC-automation-suite.git
   cd MAC-automation-suite
   ```

2. (Recommended) Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies once a `requirements.txt` or `pyproject.toml` is added:
   ```bash
   pip install -r requirements.txt
   ```
   If there is no dependency file yet, install only the packages required by the modules you use.

## Usage

### Run from terminal

- Start the main automation suite:
  ```bash
  python main.py
  ```
  This entrypoint is intended to configure and run the available modules together.

- Run individual modules directly during development:
  ```bash
  python organize.py      # Test file organization rules
  python monitor.py       # Test monitoring logic
  python scheduler.py     # Test scheduling
  python emailer.py       # Test email configuration
  python scraper.py       # Test scraping routines
  python gui.py           # Launch the GUI
  ```

### Typical workflows

- Automatically sort your Downloads folder into subfolders by file type or project using `organize.py` on a schedule managed by `scheduler.py`.
- Monitor a directory or condition with `monitor.py` and send an email notification via `emailer.py` when a rule fires.
- Periodically scrape a website or API using `scraper.py` and deliver results or alerts through the GUI or email.

## Configuration

Each module is intended to be configurable via constants, environment variables, or simple configuration files (for example, paths, email credentials, and scheduling intervals). Adjust module-level settings inside the corresponding `.py` files as needed until a unified configuration system is added.

Suggested configuration points:

- `organize.py`: Source and target directories, file-type rules, naming schemes.
- `monitor.py`: Paths or metrics to watch, thresholds, and callbacks.
- `scheduler.py`: Cron-like schedules or interval settings.
- `emailer.py`: SMTP server, sender address, and app-specific passwords or tokens.
- `scraper.py`: Target URLs, parsing logic, and output format.

## Roadmap

Planned improvements for the MAC Automation Suite:

- Add a shared configuration file (YAML or TOML) for all modules.
- Provide a `requirements.txt` and simple installer script.
- Enhance the GUI to toggle automations and view logs.
- Add logging, error reporting, and unit tests.

## Contributing

Contributions are welcome. Open an issue to discuss ideas or create a pull request with:

- A clear description of the change.
- Relevant tests or usage examples when applicable.

## License

Choose and add a license file (for example, MIT, Apache-2.0, or GPL-3.0) to define how others may use and contribute to this project. Until then, usage rights remain implicit and should be treated conservatively to respect intellectual property.
