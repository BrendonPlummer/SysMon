#!/usr/bin/python3 -u

import logging
import time
from datetime import datetime
from pprint import pprint
from signal import SIGINT, signal

import psutil  # pip install psutil

from application.app_threading import Application

# Setup logger
# sysmon_logger = logging.getLogger("application.sys_mon")

# Constants
CPU_USAGE_PERCENT = 85.0
MEMORY_USAGE_PERCENT = 80.0
DISK_USAGE_PERCENT = 90.0
#
LOGFILE_PATH = "/etc/etl/logs/system_monitoring.log"


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
        #
        self.metrics: dict | None = None
        self.log("\n\nStarting new SysMon instance...")

    #
    def log(self, log_dict: dict | str):
        #
        with open(LOGFILE_PATH, "a") as logf:
            print(f"{log_dict}", file=logf)

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
        if self.metrics["system_info"]["cpu_usage"] > CPU_USAGE_PERCENT:
            self.log(
                f"ALERT: CPU usage ({self.metrics['cpu_usage']}%) exceeds threshold of {CPU_USAGE_PERCENT}%"
            )
        #
        if self.metrics["memory_usage"]["percent"] > MEMORY_USAGE_PERCENT:
            self.log(
                f"ALERT: Memory usage ({self.metrics['memory_usage']['percent']}%) exceeds threshold of {MEMORY_USAGE_PERCENT}%"
            )
        #
        for disk, disk_data in self.metrics["disk_usage"].items():
            if disk_data["percent"] > DISK_USAGE_PERCENT:
                self.log(
                    f"ALERT: Disk usage ({self.metrics['disk_usage'][disk]['percent']}%) exceeds threshold of {DISK_USAGE_PERCENT}%"
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

        /dev/nvme0n1p1  ->  /boot/efi
        /dev/nvme0n1p2  ->  /
        /dev/nvme0n1p3  ->  /var
        /dev/nvme0n1p5  ->  /tmp
        /dev/nvme0n1p6  ->  /home
        """
        #
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu_usage_avg = [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]
        memory_info = psutil.virtual_memory()
        net_info = psutil.net_io_counters()
        #
        disk_info = {}
        for partition in psutil.disk_partitions():
            try:
                disk_usage = psutil.disk_usage(partition.mountpoint)
                disk_info[partition.device] = {
                    "total": f"{disk_usage.total / 1024 / 1024 / 1024:.2f} Gb",
                    "used": f"{disk_usage.used / 1024 / 1024 / 1024:.2f} Gb",
                    "free": f"{disk_usage.free / 1024 / 1024 / 1024:.2f} Gb",
                    "percent": disk_usage.percent,
                    "mountpoint": partition.mountpoint,
                }
            #
            except PermissionError as pe:
                self.log(f"Permission Denied: {pe}")
                continue
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
        process_data: dict = {}
        for proc in processes[:5]:
            proc_entry: dict = {}
            #
            proc_entry = {
                proc["pid"]: [f"Name: {proc['name']}", f"Memory: {proc['memory_percent']:.2f}%"]
            }
            process_data.update(proc_entry)
        #
        # Sensor Temperatures (if available)
        #
        temp_data: dict = {}
        if hasattr(psutil, "sensors_temperatures"):
            #
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        temp_entry: dict = {}
                        #
                        temp_entry = {f"{name} - {entry.label}": entry.current}
                        temp_data.update(temp_entry)
            else:
                self.log("Temperature sensors not found.")
        else:
            self.log("Temperature monitoring not supported on this system.")
        #
        #
        #
        self.metrics = {
            "system_info": {
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
                "cpu_usage": cpu_usage,
                "cpu_usage_avg": f"{cpu_usage_avg}",
                "temperature_data": temp_data,
                "top_processes": process_data,
            },
            "memory_usage": {
                "percent": memory_info.percent,
                "used_mb": f"{memory_info.used / 1024 / 1024:.2f}",
                "total_mb": f"{memory_info.total / 1024 / 1024:.2f}",
            },
            "disk_usage": disk_info,
            "net_usage": {
                "bytes_sent": net_info.bytes_sent,
                "bytes_received": net_info.bytes_recv,
                "error_in": net_info.errin,
                "error_out": net_info.errout,
                "drop_in": net_info.dropin,
                "drop_out": net_info.dropout,
            },
        }
        #
        self.log(f"System Metrics: {self.metrics}")


def main():
    """
    Main function to run the system monitor.
    """
    #
    main_module = SysMon(Shareables())
    #
    app = Application(main_module.__class__.__name__, worker_loop=main_module.run, loop_interval=300)
    app.start()
    #
    signal(SIGINT, app.signal_handler)
    print("System monitor is running. Press Ctrl+C to stop.")
    #
    while app.worker_thread.is_alive():
        time.sleep(1)


if __name__ == "__main__":
    main()
