import datetime
import uuid
from typing import Optional, Iterable

from tortoise import Model, fields, BaseDBAsyncClient


class Art(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    name = fields.CharField(max_length=200, null=True)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(
        auto_now_add=True, default=datetime.datetime.utcnow
    )
    img_picture = fields.CharField(max_length=200, null=True)
    description_prompt = fields.TextField(null=True)
    type = fields.CharField(max_length=20)
    tags = fields.JSONField(default=[])
    parent_id = fields.UUIDField(default=uuid.uuid4)
    user = fields.ForeignKeyField(
        "models.User", related_name="art", on_delete=fields.CASCADE
    )
    reference_id = fields.UUIDField(default=uuid.uuid4)

    def _pre_save(
        self,
        using_db: Optional[BaseDBAsyncClient] = None,
        update_fields: Optional[Iterable[str]] = None,
    ):
        if isinstance(self.created_at, datetime.datetime):
            self.created_at = self.created_at.replace(tzinfo=None)
        return super()._pre_save(using_db=using_db, update_fields=update_fields)


class ArtCollection(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    name = fields.CharField(max_length=200)
    symbol = fields.CharField(max_length=200, null=True)
    base_uri = fields.CharField(max_length=200, null=True)
    type = fields.CharField(max_length=20)
    created_at = fields.DatetimeField(
        auto_now_add=True, default=datetime.datetime.utcnow
    )
    user = fields.ForeignKeyField(
        "models.User", related_name="art_collections", on_delete=fields.CASCADE
    )
    arts = fields.JSONField(default=[])

    def _pre_save(
        self,
        using_db: Optional[BaseDBAsyncClient] = None,
        update_fields: Optional[Iterable[str]] = None,
    ):
        if isinstance(self.created_at, datetime.datetime):
            self.created_at = self.created_at.replace(tzinfo=None)
        return super()._pre_save(using_db=using_db, update_fields=update_fields)


class Event(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    name = fields.CharField(max_length=200)
    description = fields.TextField(null=True)
    type = fields.CharField(max_length=20)
    address = fields.TextField(null=True)
    location = fields.TextField(null=True)
    img_event_cover = fields.CharField(max_length=200, null=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="events", on_delete=fields.CASCADE
    )
    reference_id = fields.UUIDField(null=True)
    collections = fields.JSONField(default=[])
    created_at = fields.DatetimeField(auto_now_add=True)

    def _pre_save(
        self,
        using_db: Optional[BaseDBAsyncClient] = None,
        update_fields: Optional[Iterable[str]] = None,
    ):
        if isinstance(self.created_at, datetime.datetime):
            self.created_at = self.created_at.replace(tzinfo=None)
        return super()._pre_save(using_db=using_db, update_fields=update_fields)


class ArtLikes(Model):
    id = fields.IntField(pk=True)
    art = fields.ForeignKeyField(
        "models.Art", related_name="likes", on_delete=fields.CASCADE
    )
    user = fields.ForeignKeyField(
        "models.User", related_name="art_likes", on_delete=fields.CASCADE
    )

    class Meta:
        table = "art_likes"
        unique_together = (("art", "user"),)
