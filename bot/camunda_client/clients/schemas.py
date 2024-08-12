import pydantic

from camunda_client.types_ import BaseSchema


class PaginationParams(BaseSchema):
    limit: int = pydantic.Field(alias="maxResults")
    offset: int = pydantic.Field(alias="firstResult")


class CountSchema(BaseSchema):
    count: int
