import http
import json
import logging
import math
import sys
import time
from logging import ERROR, INFO, WARNING, _levelToName
from typing import Any, Dict, Optional

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import Message

from .format import (
    DATE_DEFAULT_FORMAT,
    LOGGING_DEFAULT_FORMAT,
    LOGURU_DEFAULT_FORMAT,
    LoggingColoredLog,
    loguru_format_without_traceback,
    loguru_reset_logging_handlers,
    reset_logging_handlers,
)
from .schemas import RequestResponseFields

EMPTY_VALUE = ""


class LogMiddleware:
    @staticmethod
    async def get_protocol(request: Request) -> str:
        protocol = str(request.scope.get("type", ""))
        http_version = str(request.scope.get("http_version", ""))
        if protocol.lower() == "http" and http_version:
            return f"{protocol.upper()}/{http_version}"
        return EMPTY_VALUE

    @staticmethod
    async def set_body(request: Request, body: bytes) -> None:
        async def receive() -> Message:
            return {"type": "http.request", "body": body}

        request._receive = receive

    async def get_body(self, request: Request) -> bytes:
        body = await request.body()
        await self.set_body(request, body)
        return body

    async def _log(self, level: int, message: str, extra_fields: Dict[str, Any], exception_object: Optional[Exception]):
        raise NotImplementedError()

    async def __call__(self, request: Request, call_next: RequestResponseEndpoint, *args, **kwargs):
        start_time = time.time()
        exception_object = None
        # Request Side
        try:
            raw_request_body = await request.body()
            await self.set_body(request, raw_request_body)
            raw_request_body = await self.get_body(request)
            request_body = raw_request_body.decode()
        except Exception:
            request_body = EMPTY_VALUE

        server: tuple = request.get("server", ("localhost", 9090))
        request_headers: dict = dict(request.headers.items())
        # Response Side
        try:
            response = await call_next(request)
        except Exception as ex:
            response_body = bytes(http.HTTPStatus.INTERNAL_SERVER_ERROR.phrase.encode())
            response = Response(
                content=response_body,
                status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR.real,
            )
            exception_object = ex
            response_headers = {}
        else:
            response_headers = dict(response.headers.items())
            response_body = b""
            async for chunk in response.body_iterator:  # type: ignore
                response_body += chunk
            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        duration: int = math.ceil((time.time() - start_time) * 1000)
        # Initialization and formation of fields for request-response
        extra_fields = RequestResponseFields(
            request_uri=str(request.url),
            request_referrer=request_headers.get("referer", EMPTY_VALUE),
            request_protocol=await self.get_protocol(request),
            request_method=request.method,
            request_path=request.url.path,
            request_host=f"{server[0]}:{server[1]}",
            request_size=int(request_headers.get("content-length", 0)),
            request_content_type=request_headers.get("content-type", EMPTY_VALUE),
            request_headers=json.dumps(request_headers),
            request_body=request_body,
            remote_ip=request.client[0],  # type: ignore
            remote_port=request.client[1],  # type: ignore
            response_status_code=response.status_code,
            response_size=int(response_headers.get("content-length", 0)),
            response_headers=json.dumps(response_headers),
            response_body=response_body.decode(),
            duration=duration,
        ).dict()
        extra_fields.update({"to_mask": True})
        if 0 <= response.status_code <= 299:
            level = INFO
        if 300 <= response.status_code <= 399:
            level = WARNING
        if 400 <= response.status_code <= 599:
            level = ERROR
        level = ERROR if exception_object else INFO
        message = (
            f'{"Error" if level==ERROR else "Responce"} '
            f"with code {response.status_code} "
            f'for request {request.method} "{str(request.url)}"'
        )

        await self._log(level=level, message=message, extra_fields=extra_fields, exception_object=exception_object)
        return response


class LoggingMiddleware(LogMiddleware):
    def __init__(
        self,
        logger_name: str,
        format: str = LOGGING_DEFAULT_FORMAT,
        datefmt: str = DATE_DEFAULT_FORMAT,
        level: str = "INFO",
        traceback_to_console: bool = True,
    ) -> None:
        self.logger = logging.getLogger(logger_name)
        handler = logging.StreamHandler(sys.stdout)
        formatter = LoggingColoredLog(fmt=format, traceback_to_console=traceback_to_console, datefmt=datefmt)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(level)
        reset_logging_handlers()

    async def _log(self, level: int, message: str, extra_fields: Dict[str, Any], exception_object: Exception):
        self.logger.log(
            level,
            message,
            extra=extra_fields,
            exc_info=exception_object,
        )


class LoguruMiddleware(LogMiddleware):
    def __init__(
        self, format: str = LOGURU_DEFAULT_FORMAT, level: str = "INFO", traceback_to_console: bool = True
    ) -> None:
        format_ = format if traceback_to_console else loguru_format_without_traceback(format=format)
        logger.remove()
        logger.add(sys.stderr, colorize=True, format=format_, backtrace=False, level=level)
        self.logger = logger
        loguru_reset_logging_handlers()

    async def _log(self, level: int, message: str, extra_fields: Dict[str, Any], exception_object: Exception):
        self.logger.opt(exception=exception_object).log(_levelToName[level], message, **extra_fields)
