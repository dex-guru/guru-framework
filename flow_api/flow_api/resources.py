import os
from typing import List

from fa_admin.art_models import Event, ArtCollection, Art
from fastapi_admin.app import app
from fastapi_admin.enums import Method
from fastapi_admin.file_upload import FileUpload
from fastapi_admin.resources import Action, Field, Link, Model, ToolbarAction
from fastapi_admin.widgets import filters, inputs
from starlette.requests import Request

from fa_admin import enums
from fa_admin.constants import BASE_DIR
from fa_admin.models import (
    Admin,
    Config,
    User,
    Strategy,
    ExternalWorker,
    Role,
)

upload = FileUpload(uploads_dir=os.path.join(BASE_DIR, "static", "uploads"))


@app.register
class Dashboard(Link):
    label = "Dashboard"
    icon = "fas fa-home"
    url = "/admin"


@app.register
class UsersResource(Model):
    label = "Users"
    model = User
    icon = "fas fa-users"
    page_pre_title = "user list"
    page_title = "user model"
    filters = [
        filters.Search(
            name="is_admin",
            label="Is Admin",
            search_mode="contains",
            placeholder="Search for is_admin",
        ),
        filters.Search(
            name="is_suspicious",
            label="Is Suspicious",
            search_mode="contains",
            placeholder="Search for is_suspicious",
        ),
        filters.Search(
            name="is_block",
            label="Is Block",
            search_mode="contains",
            placeholder="Search for is_block",
        ),
        filters.Search(
            name="is_premium",
            label="Is Premium",
            search_mode="contains",
            placeholder="Search for is_premium",
        ),
        filters.Search(
            name="username",
            label="Name",
            search_mode="contains",
            placeholder="Search for username",
        ),
        filters.Date(name="created_at", label="CreatedAt"),
    ]
    fields = [
        "id",
        "username",
        "first_name",
        "last_name",
        "language_code",
        "is_admin",
        "is_suspicious",
        "camunda_user_id",
        "camunda_key",
        "telegram_user_id",
        "webapp_user_id",
        "is_block",
        "is_premium",
        "created_at",
    ]


@app.register
class StrategyResource(Model):
    label = "Strategy"
    model = Strategy
    icon = "fas fa-cogs"
    page_pre_title = "strategy list"
    page_title = "strategy model"
    filters = [
        filters.Search(
            name="name",
            label="Name",
            search_mode="contains",
            placeholder="Search for name",
        ),
        filters.Search(
            name="type",
            label="Type",
            search_mode="contains",
            placeholder="Search for type",
        ),
        filters.Date(name="created_at", label="CreatedAt"),
    ]
    fields = [
        "id",
        "name",
        "description",
        "schema",
        "img_picture",
        "type",
        "parent_id",
        "user_id",
        "reference_id",
        "created_at",
        "total_pnl",
        "drawdown",
        "win_rate",
        "profit_factor",
        "expectancy",
    ]


@app.register
class ExternalWorkerResource(Model):
    label = "External Worker"
    model = ExternalWorker
    icon = "fas fa-cogs"
    page_pre_title = "external worker list"
    page_title = "external worker model"
    filters = [
        filters.Search(
            name="name",
            label="Name",
            search_mode="contains",
            placeholder="Search for name",
        ),
        filters.Search(
            name="type",
            label="Type",
            search_mode="contains",
            placeholder="Search for type",
        ),
        filters.Date(name="created_at", label="CreatedAt"),
    ]
    fields = [
        "id",
        "name",
        "description",
        "schema",
        "type",
        "parent_id",
        "user_id",
        "reference_id",
        "created_at",
    ]


@app.register
class ArtResource(Model):
    label = "Arts"
    model = Art
    icon = "fas fa-paint-brush"
    page_pre_title = "Artworks list"
    page_title = "Art model"
    filters = [
        filters.Search(
            name="name",
            label="Name",
            search_mode="contains",
            placeholder="Search for name",
        ),
        filters.Search(
            name="type",
            label="Type",
            search_mode="contains",
            placeholder="Search for type",
        ),
        filters.Date(name="created_at", label="CreatedAt"),
    ]
    fields = [
        "id",
        "type",
        "tags",
        "name",
        "description",
        "description_prompt",
        "img_picture",
        "parent_id",
        "user_id",
        "reference_id",
        "created_at",
    ]


@app.register
class ArtCollectionResource(Model):
    label = "ArtCollections"
    model = ArtCollection
    icon = "fas fa-paint-brush"
    page_pre_title = "artcollection worker list"
    page_title = "artcollecton worker model"
    filters = [
        filters.Search(
            name="name",
            label="Name",
            search_mode="contains",
            placeholder="Search for name",
        ),
        filters.Search(
            name="type",
            label="Type",
            search_mode="contains",
            placeholder="Search for type",
        ),
        filters.Date(name="created_at", label="CreatedAt"),
    ]
    fields = [
        "id",
        "name",
        "symbol",
        "base_uri",
        "type",
        "user_id",
        "arts",
        "created_at",
    ]

@app.register
class EventResource(Model):
    label = "Events"
    model = Event
    icon = "fas fa-calendar"
    page_pre_title = "event worker list"
    page_title = "event worker model"
    filters = [
        filters.Search(
            name="name",
            label="Name",
            search_mode="contains",
            placeholder="Search for name",
        ),
        filters.Search(
            name="type",
            label="Type",
            search_mode="contains",
            placeholder="Search for type",
        ),
        filters.Date(name="created_at", label="CreatedAt"),
    ]
    fields = [
        "id",
        "name",
        "description",
        "type",
        "address",
        "location",
        "img_event_cover",
        "user_id",
        "reference_id",
        "collections",
        "created_at",
    ]


@app.register
class AdminResource(Model):
    label = "Admin"
    model = Admin
    icon = "fas fa-user"
    page_pre_title = "admin list"
    page_title = "admin model"
    filters = [
        filters.Search(
            name="username",
            label="Username",
            search_mode="contains",
            placeholder="Search for name",
        ),
        filters.Date(name="created_at", label="CreatedAt"),
    ]
    fields = [
        "last_login",
        "email",
        "avatar",
        "intro",
        "created_at",
    ]

    async def get_toolbar_actions(self, request: Request) -> List[ToolbarAction]:
        return await super().get_toolbar_actions(request)

    async def cell_attributes(self, request: Request, obj: dict, field: Field) -> dict:
        if field.name == "id":
            return {"class": "bg-danger text-white"}
        return await super().cell_attributes(request, obj, field)

    async def get_actions(self, request: Request) -> List[Action]:
        return await super().get_actions(request)

    async def get_bulk_actions(self, request: Request) -> List[Action]:
        return await super().get_bulk_actions(request)


# @app.register
# class Content(Dropdown):
#     class CategoryResource(Model):
#         label = "Category"
#         model = Category
#         fields = ["id", "name", "slug", "created_at"]
#
#     class ProductResource(Model):
#         label = "Product"
#         model = Product
#         filters = [
#             filters.Enum(enum=enums.ProductType, name="type", label="ProductType"),
#             filters.Datetime(name="created_at", label="CreatedAt"),
#         ]
#         fields = [
#             "id",
#             "name",
#             "view_num",
#             "sort",
#             "is_reviewed",
#             "type",
#             Field(name="image", label="Image", display=displays.Image(width="40")),
#             Field(name="body", label="Body", input_=inputs.Editor()),
#             "created_at",
#         ]
#
#     label = "Content"
#     icon = "fas fa-bars"
#     resources = [ProductResource, CategoryResource]


@app.register
class ConfigResource(Model):
    label = "Config"
    model = Config
    icon = "fas fa-cogs"
    filters = [
        filters.Enum(enum=enums.Status, name="status", label="Status"),
        filters.Search(name="key", label="Key", search_mode="equal"),
    ]
    fields = [
        "id",
        "label",
        "key",
        "value",
        Field(
            name="status",
            label="Status",
            input_=inputs.RadioEnum(enums.Status, default=enums.Status.on),
        ),
    ]

    async def row_attributes(self, request: Request, obj: dict) -> dict:
        if obj.get("status") == enums.Status.on:
            return {"class": "bg-green text-white"}
        return await super().row_attributes(request, obj)

    async def get_actions(self, request: Request) -> List[Action]:
        actions = await super().get_actions(request)
        switch_status = Action(
            label="Switch Status",
            icon="ti ti-toggle-left",
            name="switch_status",
            method=Method.PUT,
        )
        actions.append(switch_status)
        return actions


@app.register
class RoleResource(Model):
    label = "Role"
    model = Role
    icon = "fas fa-cogs"
    filters = [
        filters.Search(name="name", label="Name", search_mode="contains"),
    ]
    fields = [
        "id",
        "name",
        "description",
    ]

    async def get_actions(self, request: Request) -> List[Action]:
        actions = await super().get_actions(request)
        return actions


@app.register
class DocumentationLink(Link):
    label = "Documentation"
    url = "https://fastapi-admin-docs.long2ice.io"
    icon = "fas fa-file-code"
    target = "_blank"

