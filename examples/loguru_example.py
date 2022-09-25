import uvicorn
from fastapi import FastAPI
from fastapi_logging import init_loguru
from fastapi_logging.extra_logger import LoguruExtraLogger
from fastapi_logging.format import (
    LOGURU_DEFAULT_FORMAT,
    loguru_format_without_traceback,
)
from loguru import logger
from pydantic import BaseModel

LOGURU_FORMAT = LOGURU_DEFAULT_FORMAT + " {extra[request_body]}"

app = FastAPI()

init_loguru(app, traceback_to_console=True, format=LOGURU_FORMAT)
# simply you can use
# init_loguru(app)
extra_logger = LoguruExtraLogger()
# next actions are not necessary, they only add file handlers
logger.add(sink="/tmp/fastapilogging.log", format=LOGURU_FORMAT, rotation="1 day")
# if you want log to file without traceback, you can use loguru_format_without_traceback function
# logger.add(sink="/tmp/fastapilogging.log", format=loguru_format_without_traceback(LOGURU_FORMAT), rotation="1 day")


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
