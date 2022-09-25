import datetime
import logging
import sys
import traceback
from copy import copy
from logging import _levelToName
from typing import Callable, Literal, Optional

import click

from .handlers import InterceptHandler
from .schemas import RequestResponseFields

TRACE_LOG_LEVEL = 5
EMPTY_VALUE = ""
FILE_DEFAULT_FORMAT = "%(asctime)s %(levelname)-8s %(response_status_code)-4s %(duration)-10d %(request_method)-4s %(thread)-10s %(request_path)-20s %(request_body)s %(message)s %(exceptions)s"
DATE_DEFAULT_FORMAT = "%Y-%m-%d %H:%M:%S"
LOGURU_DEFAULT_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> <level>{level: <8}</level> {extra[request_path]} <level>{extra[response_status_code]: <3} {message}</level>"
LOGGING_DEFAULT_FORMAT = "%(levelprefix)s %(asctime)s path: %(request_path)s %(response_status_code)-4s %(message)s request body: %(request_body)s"
LOGGING_ATTRIBUTES = {
    "name",
    "levelno",
    "levelname",
    "pathname",
    "filename",
    "module",
    "lineno",
    "funcName",
    "created",
    "asctime",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "process",
    "message",
}


class LoggingColoredLog(logging.Formatter):
    """
    A custom log formatter class that:

    * Outputs the LOG_LEVEL with an appropriate color.
    * If a log call includes an `extras={"color_message": ...}` it will be used
      for formatting the output, instead of the plain text message.
    """

    level_name_colors = {
        TRACE_LOG_LEVEL: lambda level_name: click.style(str(level_name), fg="blue"),
        logging.DEBUG: lambda level_name: click.style(str(level_name), fg="cyan"),
        logging.INFO: lambda level_name: click.style(str(level_name), fg="green"),
        logging.WARNING: lambda level_name: click.style(str(level_name), fg="yellow"),
        logging.ERROR: lambda level_name: click.style(str(level_name), fg="red"),
        logging.CRITICAL: lambda level_name: click.style(str(level_name), fg="bright_red"),
    }

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: Literal["%", "{", "$"] = "%",
        use_colors: Optional[bool] = None,
        traceback_to_console: bool = True,
    ):
        if use_colors in (True, False):
            self.use_colors = use_colors
        else:
            self.use_colors = sys.stdout.isatty()
        self.print_traceback = traceback_to_console
        super().__init__(fmt, datefmt, style, self.use_colors)

    def color_level_name(self, level_name: str, level_no: int) -> str:
        def default(level_name: str) -> str:
            return str(level_name)

        func = self.level_name_colors.get(level_no, default)
        return func(level_name)

    def should_use_colors(self) -> bool:
        return sys.stderr.isatty()

    def formatMessage(self, record: logging.LogRecord) -> str:
        recordcopy = copy(record)
        levelname = recordcopy.levelname
        seperator = " " * (8 - len(recordcopy.levelname))
        if self.use_colors:
            levelname = self.color_level_name(levelname, recordcopy.levelno)
            if "color_message" in recordcopy.__dict__:
                recordcopy.msg = recordcopy.__dict__["color_message"]
                recordcopy.__dict__["message"] = recordcopy.getMessage()
            else:
                recordcopy.__dict__["message"] = self.color_level_name(recordcopy.getMessage(), recordcopy.levelno)
        recordcopy.__dict__["levelprefix"] = levelname + ":" + seperator

        return super().formatMessage(recordcopy)

    def formatException(self, ei):
        if self.print_traceback:
            return super().formatException(ei)
        else:
            return ""


class FileLogFormatter(logging.Formatter):
    """
    Available format attributes:
        %(name)s                 Name of the logger (logging channel)
        %(levelno)s              Numeric logging level for the message (DEBUG, INFO,
                                 WARNING, ERROR, CRITICAL)
        %(levelname)s            Text logging level for the message ("DEBUG", "INFO",
                                 "WARNING", "ERROR", "CRITICAL")
        %(pathname)s             Full pathname of the source file where the logging
                                 call was issued (if available)
        %(filename)s             Filename portion of pathname
        %(module)s               Module (name portion of filename)
        %(lineno)d               Source line number where the logging call was issued
                                 (if available)
        %(funcName)s             Function name
        %(created)f              Time when the LogRecord was created (time.time()
                                 return value)
        %(asctime)s              Textual time when the LogRecord was created
        %(msecs)d                Millisecond portion of the creation time
        %(relativeCreated)d      Time in milliseconds when the LogRecord was created,
                                 relative to the time the logging module was loaded
                                 (typically at application startup time)
        %(thread)d               Thread ID (if available)
        %(threadName)s           Thread name (if available)
        %(process)d              Process ID (if available)
        %(message)s              The result of record.getMessage(), computed just as
                                 the record is emitted
        %(duration)s             Duration time
        %(exceptions)s           Traceback
        %(request_uri)s          Request URL
        %(request_referrer)s      Referrer
        %(request_protocol)s     Protocol (HTTP, HTTPS)
        %(request_method)s       Method (GET, POST, PUT, DELETE)
        %(request_path)s         Request path
        %(request_host)s         Request host
        %(request_size)s         Request size
        %(request_content_type)s Request content type
        %(remote_ip)s            Remote ip
        %(remote_port)s          Remote port
        %(response_size)s        Response size
        %(response_headers)s     Response header
        %(request_headers)s      Request header
        %(request_body)s         Request body
        %(response_status_code)s Response status code
        %(response_body)s        Response body
    """

    def __init__(self, fmt: str = FILE_DEFAULT_FORMAT, datefmt: str = DATE_DEFAULT_FORMAT) -> None:
        super().__init__(fmt, datefmt)
        self.fmt = fmt

    def format(self, record: logging.LogRecord, *args, **kwargs) -> str:
        if record.exc_info:
            exceptions = traceback.format_exception(*record.exc_info)
        elif record.exc_text:
            exceptions = record.exc_text
        else:
            exceptions = EMPTY_VALUE
        request_response_fields = RequestResponseFields.get_fields_names()
        log_object = RequestResponseFields(
            **{field: getattr(record, field) for field in set(record.__dir__()).union(request_response_fields)}
        ).dict()
        log_object.update(
            {field: getattr(record, field) for field in LOGGING_ATTRIBUTES.difference(request_response_fields)}
        )
        log_object.update(
            dict(
                asctime=datetime.datetime.fromtimestamp(record.created).strftime(self.datefmt),  # type: ignore
                message=record.getMessage(),
                duration=getattr(record, "duration", record.msecs),
                thread=record.process,
                levelname=_levelToName[record.levelno],
                props=getattr(record, "props", EMPTY_VALUE),
                source=record.name,
                exceptions=exceptions,
                name=getattr(record, "application_name", record.name),
            )
        )

        return self.fmt % log_object


def loguru_format_without_traceback(*args, format: str = LOGURU_DEFAULT_FORMAT) -> Callable:
    def format_method(*args) -> str:
        return format + "\n"

    return format_method


def reset_logging_handlers():
    loggers = (
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict
        if name.startswith(("uvicorn.", "gunicorn."))
    )
    for logger in loggers:
        logger.handlers = []


def loguru_reset_logging_handlers():
    intercept_handler = InterceptHandler()
    for name in logging.root.manager.loggerDict:
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = [intercept_handler] if not name.startswith(("uvicorn.", "gunicorn.")) else []
    reset_logging_handlers()
