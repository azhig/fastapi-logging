import logging
from types import FrameType

from loguru import logger

from .schemas import RequestResponseFields

REQUEST_RESPONSE_FIELDS = RequestResponseFields().dict()


class InterceptHandler(logging.Handler):
    def __init__(self, level: int = logging.NOTSET) -> None:

        super().__init__(level)

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame: FrameType = frame.f_back  # type: ignore
            depth += 1

        logger.bind(**REQUEST_RESPONSE_FIELDS).opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )
