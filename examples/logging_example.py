import logging
from logging.handlers import TimedRotatingFileHandler

import uvicorn
from fastapi import FastAPI
from fastapi_logging import init_logging
from fastapi_logging.extra_logger import LoggingExtraLogger
from fastapi_logging.format import (
    FILE_DEFAULT_FORMAT,
    LOGGING_DEFAULT_FORMAT,
    FileLogFormatter,
)
from pydantic import BaseModel

app = FastAPI()
init_logging(
    app,
    format=LOGGING_DEFAULT_FORMAT,
    traceback_to_console=True,
    level="INFO",
)
# simply you can use
# init_logging(app)

# next actions are not necessary, they only add file handlers
logger = logging.getLogger(__name__)
handler = TimedRotatingFileHandler(filename="/tmp/fastapilogging.log", when="d", interval=1, backupCount=14)
formatter = FileLogFormatter(FILE_DEFAULT_FORMAT)
handler.setFormatter(formatter)
logger.addHandler(handler)

extra_logger = LoggingExtraLogger(logger_name=__name__)


@app.get("/err")
def err_get():
    1 / 0


@app.get("/noerr")
def noerr_get():
    return


class Body(BaseModel):
    field_str: str
    field_int: int


# everything you'll log with using extra_logger will automaticaly add income args discription and function name
@app.post("/extra_logger_example")
def extra_logger_example(body: Body):
    extra_logger.info("here is your info")
    extra_logger.warn("here is your warning")
    extra_logger.critical("here is your critical")
    extra_logger.debug("here is your debug")
    extra_logger.fatal("here is your fatal")
    extra_logger.error("here is your error")


uvicorn.run(app)
