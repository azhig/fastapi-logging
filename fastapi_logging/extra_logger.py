import inspect
from logging import (
    CRITICAL,
    DEBUG,
    ERROR,
    FATAL,
    INFO,
    WARN,
    WARNING,
    _levelToName,
    getLogger,
)
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from .schemas import RequestResponseFields

DICT_STR_T = Dict[str, Any]


def path_subtraction(path_one: Path, path_two: Path) -> Path:
    path_one_parts = path_one.parts
    path_two_parts = path_two.parts
    i = 0
    for i in range(min(len(path_one_parts), len(path_two_parts))):
        if path_two_parts[i] != path_one_parts[i]:
            break
    if i != len(path_one_parts):
        i += 1
    return Path("/".join(path_one_parts[i:]))


class ExtraLogger:
    """Logging extra-logger class. With using it you'll get logger with additional 'request_path' and 'request_body'
    fields. 'request_path' will contain filename and module name, from which it was called. 'request_body' will
    contain function args.
    """

    logger_ = None

    def __init__(
        self,
        additional_fields: DICT_STR_T = {},
    ) -> None:
        self.additional_fields = additional_fields

    def info(self, msg: str, extra: Optional[DICT_STR_T] = None, **kwargs):
        self._log(INFO, msg, extra, **kwargs)

    def warning(self, msg: str, extra: Optional[DICT_STR_T] = None, **kwargs):
        self._log(WARNING, msg, extra, **kwargs)

    def warn(self, msg: str, extra: Optional[DICT_STR_T] = None, **kwargs):
        self._log(WARN, msg, extra, **kwargs)

    def error(self, msg: str, extra: Optional[DICT_STR_T] = None, **kwargs):
        self._log(ERROR, msg, extra, **kwargs)

    def debug(self, msg: str, extra: Optional[DICT_STR_T] = None, **kwargs):
        self._log(DEBUG, msg, extra, **kwargs)

    def critical(self, msg: str, extra: Optional[DICT_STR_T] = None, **kwargs):
        self._log(CRITICAL, msg, extra, **kwargs)

    def fatal(self, msg: str, extra: Optional[DICT_STR_T] = None, **kwargs):
        self._log(FATAL, msg, extra, **kwargs)

    def _logger_log(self, level: int, msg: str, extra: DICT_STR_T):
        raise NotImplementedError()

    def _log(
        self,
        level: int,
        msg: str,
        extra: Optional[DICT_STR_T] = None,
    ):
        caller_module = inspect.stack()[2]
        arguments, _, _, values = inspect.getargvalues(caller_module.frame)
        extra_ = RequestResponseFields().dict()
        file_path = path_subtraction(Path(caller_module.filename), Path.cwd())
        extra_.update(
            {
                "request_path": f".{file_path} {caller_module.function}",
                "request_body": str({arg: values[arg] for arg in arguments}),
            }
        )
        extra_.update(self.additional_fields)
        if extra:
            extra_.update(extra)

        self._logger_log(level, msg, extra=extra_)


class LoggingExtraLogger(ExtraLogger):
    def __init__(self, logger_name: str, additional_fields: DICT_STR_T = {}) -> None:
        """
        Parameters
        ----------
        additional_fields, optional
            Dictionary of additional fields to logging
        logger_name
            Logging logger name

        """
        self.logger_ = getLogger(logger_name)
        super().__init__(additional_fields=additional_fields)

    def _logger_log(self, level: int, msg: str, extra: DICT_STR_T):
        self.logger_.log(level, msg, extra=extra)


class LoguruExtraLogger(ExtraLogger):
    def __init__(self, additional_fields: DICT_STR_T = {}) -> None:
        """
        Parameters
        ----------
        additional_fields, optional
            Dictionary of additional fields to logging
        """
        self.logger_ = logger
        super().__init__(additional_fields=additional_fields)

    def _logger_log(self, level: int, msg: str, extra: DICT_STR_T):
        self.logger_.log(_levelToName[level], msg, **extra)
