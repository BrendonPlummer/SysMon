#!/usr/bin/python3 -u
import logging
import threading
import typing

from logger.logger import setup_logger

setup_logger()
application_logger = logging.getLogger("application")


class Application:
    """
    Base Application class that handles threading for any module.
    """

    def __init__(self, module_name: str, worker_loop: typing.Callable, loop_interval: int = 5):
        #
        self.shutdown_event: threading.Event = threading.Event()
        self.worker_thread: threading.Thread | None = None
        self.worker_loop: typing.Callable = worker_loop
        self.loop_interval: int = loop_interval
        #
        self.module_name: str = module_name

    def start(self):
        """
        Starts the worker thread.
        """
        if self.worker_thread is None or not self.worker_thread.is_alive():
            #
            self.worker_thread = threading.Thread(target=self._loop, name="WorkerThread")
            self.worker_thread.start()
            #
            application_logger.debug(
                f"{self.module_name} :: {self.worker_loop.__name__} {self.worker_loop.__name__} :: Starting main worker thread."
            )

    def stop(self):
        """
        Signals the worker thread to stop.
        """
        if self.worker_thread and self.worker_thread.is_alive():
            #
            self.shutdown_event.set()
            self.worker_thread.join()
            #
            application_logger.debug(
                f"{self.module_name} :: {self.worker_loop.__name__} :: Stopping main worker thread."
            )

    def _loop(self):
        """
        The main loop for the worker thread.
        """
        while not self.shutdown_event.is_set():
            #
            try:
                self.worker_loop()
                self.shutdown_event.wait(self.loop_interval)
            #
            except Exception as e:
                application_logger.exception(e)
                self.stop()
                # raise e  # Raise for Python interpreter to post

    def signal_handler(self, frame, sig):
        """
        Will take a SIGINT signal and terminates the main thread.
        """
        #
        print("\nCtrl+C detected. Shutting down...")
        self.stop()
