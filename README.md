Often when debugging web applications, it is required to display response/request fields in logs. This module allows you to switch from regular uvicorn logging to advanced FasApi logging using Middleware. You can either use logging or loguru. An extra-logger has also been added to the module, when called in any module, fields are added containing the name of the file and function, as well as parameters included in the function.

- [Additional fields](#additional-fields)
  - [Adding fields to logging](#adding-fields-to-logging)
  - [Translation of logging to loguru](#translation-of-logging-to-loguru)
- [Extra-Logger](#extra-logger)
  - [logging extra-logger](#logging-extra-logger)
  - [loguru extra-logger](#loguru-extra-logger)

Additional fields
=================

You can use the following additional fields when formatting logs:
 - **duration** - Duration time
 - **exceptions** - Traceback
 - **request_uri** - Request URL
 - **request_referrer** - Referrer
 - **request_protocol** - Protocol (HTTP, HTTPS)
 - **request_method** - Method (GET, POST, PUT, DELETE)
 - **request_path** - Request path
 - **request_host** - Request host
 - **request_size** - Request size
 - **request_content_type** - Request content type
 - **remote_ip** - Remote ip
 - **remote_port** - Remote port
 - **response_size** - Response size
 - **response_headers** - Response header
 - **request_headers** - Request header
 - **request_body** - Request body
 - **response_status_code** - Response status code
 - **response_body** - Response body

Adding fields to logging
--------------------------
If you are using the logging module, then just call the following command:
``` python
from fastapi import FastAPI
from fastapi_logging import init_logging
app = FastAPI()
init_logging(app)
```
Let's look at an example call. Let's create an endpoint with an error and call it
```python
@app.get("/err")
def err_get():
    1 / 0
```
![deffault logging](/docs/logging_without_traceback.png)

When initiating `init_logging` you can use the following options:
 - **logger_name** -
        Logger name for `logging` module. This name will be used to get logger later.
        So all configurations for console logging logger should by applied to this name.
        By default it take name of  main application
 - **format** -
        String format for message, by default `LOGGING_DEFAULT_FORMAT`
 - **datefmt** -
        Date format, by default `DATE_DEFAULT_FORMAT`
 - **level** -
        Logging level, by default `"INFO"`
 - **traceback_to_console** -
        Set `True` if you want to see traceback in your console, `False` if you don't, by default `False`
```python
init_logging(
    app,
    logger_name=__name__,
    format="%(levelprefix)s %(asctime)s path: %(request_path)s %(response_status_code)-4s %(message)s request body: %(request_body)s",
    traceback_to_console=True,
    level="INFO",
)

```
The format can be set according to logging standards. If the `traceback_to_console` argument is set to `True`, then when you call the same endpoint, you will see the traceback directly in the console.
![logging with traceback](/docs/logging_with_traceback.png)

---
**Note**

To add `traceback` when logging, for example to a file, use the `exceptions` attribute

---

Translation of logging to loguru
--------------------------------
To transfer all dogging to loguru, just run the following commands:

```python
from fastapi import FastAPI
from fastapi_logging import init_loguru
app = FastAPI()
init_loguru(app)
```
Let's look at an example call
![loguru without traceback](/docs/loguru_without_traceback.png)

When initiating `init_logging` you can use the following options:
 - **format** -
        String format for message, by default `LOGURU_DEFAULT_FORMAT`
 - **level** -
        Logging level, by default `"INFO"`
 - **traceback_to_console** -
        Set `True` if you want to see traceback in your console, `False` if you don't, by default False
```python
init_loguru(
    app, 
    traceback_to_console=True, 
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> <level>{level: <8}</level> {extra[request_path]} <level>{extra[response_status_code]: <3} {message}</level>",
    level="DEBUG"
)
```
When the `traceback_to_console` argument is set to `True`, you will see the traceback directly in the console.
![loguru with traceback](/docs/loguru_with_traceback.png)

Extra-Logger
============
You can use extra-logger anywhere in your code. With using it you'll get logger with additional 'request_path' and 'request_body' fields. 'request_path' will contain filename and module name, from which it was called. 'request_body' will contain function args. Also you can add fields  using `addintional_fields` attribute.

logging extra-logger
--------------------

```python
from fastapi_logging.extra_logger import LoggingExtraLogger

extra_logger = LoggingExtraLogger(logger_name=__name__)
```
Let's work on the following example

```python
from pydantic import BaseModel


class Body(BaseModel):
    field_str: str
    field_int: int

@app.post("/extra_logger_example")
def extra_logger_example(body: Body):
    extra_logger.info("here is your info")
    extra_logger.warn("here is your warning")
    extra_logger.critical("here is your critical")
    extra_logger.debug("here is your debug")
    extra_logger.fatal("here is your fatal")
    extra_logger.error("here is your error")
```
The logs will show the following:
![](/docs/logging_extra_logger.png)

loguru extra-logger
-------------------

```python
from fastapi_logging.extra_logger import LoguruExtraLogger

extra_logger = LoguruExtraLogger()
```
As in the previous example, the output will be:
![](/docs/loguru_extra_logger.png)
