from typing import Optional, Set, Union

from pydantic import BaseModel

EMPTY_STR = ""


class AdaptedModel(BaseModel):
    @classmethod
    def get_fields_names(cls, alias=False) -> Set[str]:
        return set(cls.schema(alias)["properties"].keys())


class RequestResponseFields(AdaptedModel):
    """
    Scheme of the request-response part of the log format
    """

    application_name: str = EMPTY_STR
    request_uri: str = EMPTY_STR
    request_referrer: str = EMPTY_STR
    request_protocol: str = EMPTY_STR
    request_method: str = EMPTY_STR
    request_path: str = EMPTY_STR
    request_host: str = EMPTY_STR
    request_size: Optional[int] = None
    request_content_type: str = EMPTY_STR
    request_headers: str = EMPTY_STR
    request_body: str = EMPTY_STR
    request_direction: str = EMPTY_STR
    remote_ip: str = EMPTY_STR
    remote_port: str = EMPTY_STR
    response_status_code: Union[int, str] = ""
    response_size: Optional[int] = None
    response_headers: str = EMPTY_STR
    response_body: str = EMPTY_STR
    duration: Optional[int] = 0
