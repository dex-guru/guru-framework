from fastapi import Depends, HTTPException
from fastapi_admin.app import app
from fastapi_admin.depends import get_resources
from fastapi_admin.template import templates
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER, HTTP_404_NOT_FOUND

from fa_admin.models import Config


@app.get("/")
async def home(
    request: Request,
    resources=Depends(get_resources),
):
    return templates.TemplateResponse(
        "dashboard.html",
        context={
            "request": request,
            "resources": resources,
            "resource_label": "Dashboard",
            "page_pre_title": "overview",
            "page_title": "Dashboard",
        },
    )


@app.put("/config/switch_status/{config_id}")
async def switch_config_status(request: Request, config_id: int):
    config = await Config.get_or_none(pk=config_id)
    if not config:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND)
    config.status = not config.status
    await config.save(update_fields=["status"])
    return RedirectResponse(
        url=request.headers.get("referer"), status_code=HTTP_303_SEE_OTHER
    )


# @app.post("/admin/create")
# async def create_admin(
#     username: str = Body(...),
#     password: str = Body(...),
#     email: str = Body(default=""),
#     avatar: str = Body(default=""),
#     intro: str = Body(default=""),
# ):
#     try:
#         admin = await Admin.create(
#             username=username, password=password, email=email, avatar=avatar, intro=intro
#         )
#         return {"message": "Admin created successfully", "admin": admin}
#     except IntegrityError:
#         raise HTTPException(status_code=400, detail="Username already exists")
