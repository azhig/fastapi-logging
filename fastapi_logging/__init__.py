import inspect
from typing import Any

from fastapi import FastAPI

from .format import DATE_DEFAULT_FORMAT, LOGGING_DEFAULT_FORMAT, LOGURU_DEFAULT_FORMAT
from .middlewares import LoggingMiddleware, LoguruMiddleware


def init_logging(
    app: FastAPI,
    logger_name: Any = None,
    format: str = LOGGING_DEFAULT_FORMAT,
    datefmt: str = DATE_DEFAULT_FORMAT,
    level: str = "INFO",
    traceback_to_console: bool = False,
):
    """Add request/response fields to logging by using middleware

    Parameters
    ----------
    app
        FastApi application to add middleware
    logger_name, optional
        Logger name for 'logging' module. This name will be used to get logger later.
        So all configurations for console logging logger should by applied to this name.
        By default it take __name__ of  main application
    format, optional
        String format for message. See docs to get all additional fields, by default LOGGING_DEFAULT_FORMAT
    datefmt, optional
        Date format, by default DATE_DEFAULT_FORMAT
    level, optional
        Logging level, by default "INFO"
    traceback_to_console, optional
        Set 'True' if you want to see traceback in your console, 'False' if you don't, by default False
    """
    if logger_name is None:
        logger_name = inspect.stack()[1][0].f_locals["__name__"]

    app.middleware("http")(
        LoggingMiddleware(
            logger_name=logger_name,
            format=format,
            datefmt=datefmt,
            level=level,
            traceback_to_console=traceback_to_console,
        )
    )


def init_loguru(
    app: FastAPI, format: str = LOGURU_DEFAULT_FORMAT, level: str = "INFO", traceback_to_console: bool = False
):
    """Add request/response fields to logging by using middleware. Also it change all non-loguru logging to loguru

    Parameters
    ----------
    app
        FastApi application to add middleware
    format, optional
        String format for message. See docs to get all additional fields, by default LOGURU_DEFAULT_FORMAT
    level, optional
        Logging level, by default "INFO"
    traceback_to_console, optional
        Set 'True' if you want to see traceback in your console, 'False' if you don't, by default False
    """
    app.middleware("http")(LoguruMiddleware(format=format, level=level, traceback_to_console=traceback_to_console))
