from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, TypeVar

import httpx
import orjson

from camunda_client.exceptions import CamundaClientError
from camunda_client.types_ import VariableTypes, VariableValueSchema

_T = TypeVar("_T")


def raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return

    raise CamundaClientError(
        status_code=response.status_code,
        response_data=response.content,
    )


def camunda_timedelta(delta: timedelta) -> int:
    return int(delta.total_seconds() * 1000)


def deserialize(
    value: Any,  # noqa: ANN401
    type_: VariableTypes | None = None,
) -> VariableValueSchema:
    if type_ is not None:
        return VariableValueSchema(value=value, type=type_)

    match value:
        case bool():
            type_ = "Boolean"
        case datetime():
            type_ = "Date"
            value = to_camunda_datetime(value)
        case Decimal():
            type_ = "Double"
        case float():
            type_ = "Double"
        case int():
            type_ = "Integer"
        case None:
            type_ = "Null"
        case dict() | list():
            type_ = "Json"
            value = orjson.dumps(value)
        case bytes():
            type_ = "Bytes"
        case str():
            type_ = "String"
        case _ as never:
            msg = f"Got undefined type: {type(never)}"
            raise ValueError(msg)

    return VariableValueSchema(value=value, type=type_)


def to_camunda_datetime(value: datetime) -> str:
    return value.isoformat(timespec="milliseconds").replace("+00:00", "+0000")


def process_variable(variable: VariableValueSchema) -> Any:  # noqa: ANN401
    if variable.type == "Json":
        return orjson.loads(variable.value)

    return variable.value


def get_value(value: _T | None) -> _T:
    """
    Returns value if value is not None

    Raised:
        - `ValueError`
    """
    if value is None:
        raise ValueError
    return value
