from uuid import UUID

from pydantic import Field

from fa_admin.rest_models.api_rest_models import ORMBaseModel


class StrategyRest(ORMBaseModel):
    id: UUID
    name: str
    description: str | None = None
    strategy_schema: dict | None = Field(None, alias="schema")
    img_picture: str | None = None
    strategy_type: str = Field(..., alias="type")
    parent_id: UUID
    user_id: UUID
    reference_id: UUID
    total_pnl: float = 0
    drawdown: float = 0
    win_rate: float = 0
    profit_factor: float = 0
    expectancy: float = 0


class FlowRest(ORMBaseModel):
    id: UUID
    key: str
    name: str
    description: str | None = None
    img_picture: str | None = None
    flow_type: str = Field(..., alias="type")
    parent_id: UUID
    user_id: UUID
    reference_id: UUID


class ExternalWorkerRest(ORMBaseModel):
    id: UUID
    name: str
    description: str | None = None
    worker_schema: dict | None = Field(None, alias="schema")
    img_picture: str | None = None
    external_worker_type: str = Field(..., alias="type")
    parent_id: UUID
    user_id: UUID
    reference_id: int
