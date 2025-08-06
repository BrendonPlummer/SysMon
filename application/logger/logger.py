"""
Logger
======

This module provides a centralised logging setup for Python applications. It includes a
custom JSON formatter (`json_formatter`) designed for structured logging, and a `setup_logger()`
function that loads and applies configuration from a JSON file. It also includes a filter class for
controlling which log levels are processed.

-----------------------
How It Works
-----------------------
- This logger setup is built around Python's `logging.config.dictConfig` system.
- The logging configuration is expected to be defined in a JSON file located at `/etc/local_I/logger.json`.
- The configuration includes handlers for stderr output and rotating JSON file logs, using a queue handler
  for asynchronous logging.
- A custom formatter (`json_formatter`) formats log records into structured JSON using a set of
  provided key mappings (`fmt_keys`).
- A filter (`NonErrorFilter`) is also included to allow inclusion of only logs up to a certain severity.

-----------------------
How to Use
-----------------------

1. Import and call `setup_logger()` at the start of your main entrypoint (before any loggers are used):

    ```python
    from logger.logger import setup_logger
    setup_logger()
    ```

    NOTE: You will need to have the logger availble in your PYTHONPATH environment variable.

2. Once configured, you can safely fetch loggers anywhere in your application:

    ```python
    import logging
    logger = logging.getLogger("my.module")
    logger.info("This message will be formatted and handled as configured.")
    ```

3. The formatter (`json_formatter`) extracts standard attributes from log records and
   outputs them as a structured JSON string, including timestamp, module, function name,
   and any exception info.

4. The `NonErrorFilter` can be attached to handlers to allow only `INFO`-and-below log messages
   (excluding `WARNING`, `ERROR`, etc.).

-----------------------
Key Requirements
-----------------------

- The `setup_logger()` function **must be called once per process** before any logging occurs to ensure
  all configuration is applied correctly.
- The file `/etc/local_I/logger.json` must be present and contain valid `logging.config.dictConfig` JSON.
- This module is compatible with Python 3.12+ due to the use of `@override` from the `typing` module.


-----------------------
Authors
-----------------------
- Author: Brendon Plummer
- Version: 0.1.0.2025.08.06
"""

__author__ = "Brendon Plummer"
__version__ = "0.1.0.2025.08.06"
import atexit  # type: ignore
import datetime as dt
import json
import logging
import logging.config
import pathlib
import traceback
from typing import override


# Sets up the root logger
def setup_logger() -> None:
    config_file = pathlib.Path("/etc/local_I/logger.json")
    with open(config_file) as f_in:
        dict_config = json.load(f_in)
    #
    logging.config.dictConfig(config=dict_config)
    logger_queue_handler: logging.handlers.QueueHandler = logging.getHandlerByName(
        "logger_queue_handler"
    )  # type: ignore
    #
    if logger_queue_handler is not None:
        logger_queue_handler.listener.start()  # type: ignore
        atexit.register(logger_queue_handler.listener.stop)  # type: ignore


LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class json_formatter(logging.Formatter):
    def __init__(self, fmt_keys: dict[str, str] | None = None):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    @override
    def format(self, record: logging.LogRecord) -> str:
        #
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)  # type: ignore

    def _prepare_log_dict(self, record: logging.LogRecord):
        # These will be present in ALL logs printed to file
        constant_fields = {
            "message": record.getMessage(),
            "timestamp": dt.datetime.fromtimestamp(record.created, tz=dt.timezone.utc),  # type: ignore     .isoformat()
        }
        # Adds any exception data to the message
        if record.exc_info is not None:
            constant_fields["exc_info"] = self.formatException(record.exc_info)
        #
        if record.stack_info is not None:
            constant_fields["stack_info"] = self.formatStack(record.stack_info)
        #
        level_aliases = {
            "DEBUG": "[DBG]",
            "INFO": "[INF]",
            "WARNING": "[WRN]",
            "ERROR": "[ERR]",
            "EXCEPTION": "[EXC]",
            "CRITICAL": "[CRT]",
        }
        level = record.levelname
        fmt_level = level_aliases.get(level.upper(), f"[{level[:3].upper()}]")  # type: ignore
        constant_fields["levelname"] = fmt_level
        #
        message = {
            key: msg_value
            if (msg_value := constant_fields.pop(val, None)) is not None
            else getattr(record, val)
            for key, val in self.fmt_keys.items()
        }
        #
        message.update(constant_fields)
        # Adds in any extras tacked onto the log call
        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val
        #
        return message


class NonErrorFilter(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return record.levelno <= logging.INFO
