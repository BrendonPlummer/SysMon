#!/usr/bin/python3 -u

import logging
import time
from signal import SIGINT, signal

import psutil  # pip install psutil

from application.app_threading import Application

# Setup logger
sysmon_logger = logging.getLogger("application.sys_mon")

# Constants
CPU_USAGE_PERCENT = 85.0
MEMORY_USAGE_PERCENT = 80.0
DISK_USAGE_PERCENT = 90.0


class Shareables:
    """
    Values to share throughout the Deamon.
    """

    def __init__(self):
        """Constructor, invoke the Thread constructor."""
        ...


class SysMon:
    #
    def __init__(self, shareables: Shareables):
        #
        self.shareables = shareables
        sysmon_logger.info("Finished initialising :: Application.SysMon")
        #
        self.metrics: dict | None = None
        #
        # [TODO]: Implement the below configuration
        #
        # config = configparser.ConfigParser()
        # config.read("config.ini")

        # # Read settings from config file
        # loop_interval = config.getint("Settings", "loop_interval", fallback=10)
        # Thresholds.CPU_USAGE_PERCENT = config.getfloat(
        #     "Thresholds", "cpu_usage", fallback=85.0
        # )
        # Thresholds.MEMORY_USAGE_PERCENT = config.getfloat(
        #     "Thresholds", "memory_usage", fallback=80.0
        # )
        # Thresholds.DISK_USAGE_PERCENT = config.getfloat(
        #     "Thresholds", "disk_usage", fallback=90.0
        # )

    #
    def run(self):
        #
        self.monitor_system_metrics()
        self.check_thresholds()

    #
    def check_thresholds(self) -> None:
        """
        Checks metrics against predefined constants and logs a warning.
        """
        if self.metrics is None:
            return
        #
        if self.metrics["cpu_usage"] > CPU_USAGE_PERCENT:
            sysmon_logger.warning(
                f"ALERT: CPU usage ({self.metrics['cpu_usage']}%) exceeds threshold of {CPU_USAGE_PERCENT}%"
            )
        #
        if self.metrics["memory_usage"]["percent"] > MEMORY_USAGE_PERCENT:
            sysmon_logger.warning(
                f"ALERT: Memory usage ({self.metrics['memory_usage']['percent']}%) exceeds threshold of {MEMORY_USAGE_PERCENT}%"
            )
        #
        if self.metrics["disk_usage"]["percent"] > DISK_USAGE_PERCENT:
            sysmon_logger.warning(
                f"ALERT: Disk usage ({self.metrics['disk_usage']['percent']}%) exceeds threshold of {DISK_USAGE_PERCENT}%"
            )

    def monitor_system_metrics(self) -> None:
        """
        Monitors a variety of system metrics and logs relevant information about them.

        Metrics tracked:
            - CPU Usage
            - Memory Information
            - Disk Information
            - Network Information
            - Sensor Information (*If available*)
        """
        #
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage("/")
        net_info = psutil.net_io_counters()
        #
        self.metrics = {
            "cpu_usage": cpu_usage,
            "memory_usage": {
                "percent": memory_info.percent,
                "used_mb": f"{memory_info.used / 1024 / 1024:.2f}",
                "total_mb": f"{memory_info.total / 1024 / 1024:.2f}",
            },
            "disk_usage": {
                "percent": disk_info.percent,
                "used_gb": f"{disk_info.used / 1024 / 1024 / 1024:.2f}",
                "total_gb": f"{disk_info.total / 1024 / 1024 / 1024:.2f}",
            },
            "net_usage": {
                "bytes_sent": net_info.bytes_sent,
                "bytes_received": net_info.bytes_recv,
            },
        }
        #
        sysmon_logger.info(
            f"CPU: {self.metrics['cpu_usage']}% | "
            f"Memory: {self.metrics['memory_usage']['percent']}% ({self.metrics['memory_usage']['used_mb']}MB / {self.metrics['memory_usage']['total_mb']}MB) | "
            f"Disk: {self.metrics['disk_usage']['percent']}% ({self.metrics['disk_usage']['used_gb']}GB / {self.metrics['disk_usage']['total_gb']}GB)"
        )
        #
        # Running Processes (Top 5 by memory)
        #
        processes = sorted(
            [
                p.info
                for p in psutil.process_iter(["pid", "name", "memory_percent"])
                if p.info["memory_percent"] is not None
            ],
            key=lambda p: p["memory_percent"],
            reverse=True,
        )
        sysmon_logger.info("Top 5 processes by memory:")
        for proc in processes[:5]:
            sysmon_logger.info(
                f"  - PID: {proc['pid']}, Name: {proc['name']}, Memory: {proc['memory_percent']:.2f}%"
            )
        #
        # Sensor Temperatures (if available)
        #
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        sysmon_logger.info(f"Temperature - {name} ({entry.label}): {entry.current}°C")
            else:
                sysmon_logger.info("Temperature sensors not found.")
        else:
            sysmon_logger.info("Temperature monitoring not supported on this system.")


def main():
    """
    Main function to run the system monitor.
    """
    #
    main_module = SysMon(Shareables())
    #
    app = Application(main_module.__class__.__name__, worker_loop=main_module.run, loop_interval=5)
    app.start()
    #
    signal(SIGINT, app.signal_handler)
    print("System monitor is running. Press Ctrl+C to stop.")
    #
    while app.worker_thread.is_alive():
        time.sleep(1)


if __name__ == "__main__":
    main()
