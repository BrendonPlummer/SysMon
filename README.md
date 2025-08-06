# SysMon - System Monitoring Tool

A lightweight and configurable system monitoring tool written in Python. It periodically collects and logs key system metrics, providing insights into your system's performance and health.

## Features

- **Comprehensive Metrics:** Monitors CPU usage, memory consumption, disk space, and network I/O statistics.
- **Process Monitoring:** Lists the top 5 running processes by memory usage.
- **Temperature Sensing:** Reports hardware temperatures if sensors are available on the system.
- **Configurable Alerts:** Set custom thresholds for CPU, memory, and disk usage in a simple configuration file. The application will log a `WARNING` when any metric exceeds its threshold.
- **Dual Logging:** Outputs information to both the console and a persistent log file (`sys_mon.log`).
- **Reusable Threading:** Built on a generic, reusable threading module (`app_threading.py`) for clean and reliable background operation.

## Getting Started

### Prerequisites

- Python 3.x

### Installation

1.  **Clone the repository:**

    ```sh
    git clone https://github.com/BrendonPlummer/SysMon.git
    cd SysMon
    ```

2.  **Install the required dependency:** The project relies on the `psutil` library to gather system metrics. Install it using pip:
    ```sh
    pip install psutil
    ```

## Usage

1.  **Configure the Monitor (Optional):** Before running, you can adjust the monitoring settings by editing the `config.ini` file:

    - `loop_interval`: The time in seconds between each metric collection.
    - `cpu_usage`, `memory_usage`, `disk_usage`: The percentage thresholds at which to trigger a warning.

2.  **Run the Application:** Execute the main script from the project's root directory:

    ```sh
    python sys_mon.py
    ```

3.  **View Output:**

    - Real-time logs will be printed to your console.
    - A complete history is saved in the `sys_mon.log` file.

4.  **Stop the Application:** Press `Ctrl+C` in the terminal to gracefully shut down the monitor.

## Project Structure

```
SysMon/
├── app_threading.py    # Reusable class for managing the background worker thread.
├── config.ini          # Configuration file for thresholds and settings.
├── sys_mon.py          # Main application logic and entry point.
├── sys_mon.log         # Log file where metrics and alerts are stored.
└── README.md           # This file.
```

## License

This project is licensed under the terms of the LICENSE file.
