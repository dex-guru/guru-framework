import datetime
import uuid
from typing import Optional, Iterable

from tortoise import Model, fields, BaseDBAsyncClient


class Strategy(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    name = fields.CharField(max_length=200, null=True)
    description = fields.TextField(null=True)
    schema = fields.JSONField(default={})
    img_picture = fields.CharField(max_length=200, null=True)
    type = fields.CharField(max_length=20)
    parent_id = fields.UUIDField(default=uuid.uuid4)
    user = fields.ForeignKeyField(
        "models.User", related_name="strategy", on_delete=fields.CASCADE
    )
    reference_id = fields.UUIDField(default=uuid.uuid4)
    created_at = fields.DatetimeField(
        auto_now_add=True, default=datetime.datetime.utcnow
    )
    total_pnl = fields.FloatField(default=0)
    drawdown = fields.FloatField(default=0)
    win_rate = fields.FloatField(default=0)
    profit_factor = fields.FloatField(default=0)
    expectancy = fields.FloatField(default=0)

    def _pre_save(
        self,
        using_db: Optional[BaseDBAsyncClient] = None,
        update_fields: Optional[Iterable[str]] = None,
    ):
        if isinstance(self.created_at, datetime.datetime):
            self.created_at = self.created_at.replace(tzinfo=None)
        return super()._pre_save(using_db=using_db, update_fields=update_fields)


class Flow(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    key = fields.CharField(max_length=200)
    name = fields.CharField(max_length=200, null=True)
    description = fields.TextField(null=True)
    img_picture = fields.CharField(max_length=200, null=True)
    type = fields.CharField(max_length=20)
    parent_id = fields.UUIDField(default=uuid.uuid4)
    user = fields.ForeignKeyField(
        "models.User", related_name="flow", on_delete=fields.CASCADE
    )
    reference_id = fields.UUIDField(default=uuid.uuid4)


class ExternalWorker(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    name = fields.CharField(max_length=200, null=True)
    description = fields.TextField(null=True)
    schema = fields.JSONField(default={})
    type = fields.CharField(max_length=200)
    parent_id = fields.UUIDField(default=uuid.uuid4)
    user = fields.ForeignKeyField(
        "models.User", related_name="externalworker", on_delete=fields.CASCADE
    )
    reference_id = fields.UUIDField(default=uuid.uuid4)
    created_at = fields.DatetimeField(
        auto_now_add=True, default=datetime.datetime.utcnow
    )

    def _pre_save(
        self,
        using_db: Optional[BaseDBAsyncClient] = None,
        update_fields: Optional[Iterable[str]] = None,
    ):
        if isinstance(self.created_at, datetime.datetime):
            self.created_at = self.created_at.replace(tzinfo=None)
        return super()._pre_save(using_db=using_db, update_fields=update_fields)


class Invite(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    wallet_address = fields.CharField(max_length=200)
    token_id = fields.IntField()
    chain_id = fields.IntField()
    is_updated_merkle_root = fields.BooleanField(default=False)


class NftMetadata(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    season_id = fields.IntField()
    token_id = fields.IntField()
    chain_id = fields.IntField()
    art = fields.ForeignKeyField("models.Art", related_name="nft_metadata")

    class Meta:
        table = "nft_metadata"
