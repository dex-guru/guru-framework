from typing import Any


class CamundaClientError(Exception):
    status_code: int
    response_data: Any = None

    def __init__(self, status_code: int, response_data: Any = None) -> None:
        self.status_code = status_code
        self.response_data = response_data

    def __str__(self) -> str:
        return f"HTTP CODE: {self.status_code}, RESPONSE DATA: {self.response_data}"


class InvalidStateError(Exception):
    pass
