import os
from typing import Optional

import redis.asyncio as redis
import uvicorn
from elasticapm import Client
from elasticapm.contrib.starlette import make_apm_client, ElasticAPM

from async_fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi import FastAPI
from fastapi_admin.app import app as admin_app
from fastapi_admin.exceptions import (
    forbidden_error_exception,
    not_found_error_exception,
    server_error_exception,
    unauthorized_error_exception,
)
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from tortoise.contrib.fastapi import register_tortoise

from fa_admin import settings
from fa_admin.constants import BASE_DIR
from fa_admin.exception_handlers import authjwt_exception_handler
from fa_admin.models import Admin
from fa_admin.providers import LoginProvider
from fa_admin.routes.api_routes import router as api_route
from fa_admin.routes.warehouse_proxy import router as warehouse_router
from fa_admin.routes.camunda_routes import router as camunda_route
from fa_admin.routes.seasons_routes import seasons_router
from fa_admin.routes.token_info_routes import router as token_info_router
from fa_admin.settings import database_url


class ApmClient:
    def __init__(self):
        self.client: Optional[Client] = None
        self.apm_config = {
            "SERVICE_NAME": os.getenv("SERVICE_NAME", "fastapi-admin"),
            "SERVER_URL": os.getenv("APM_SERVER_URL", "http://localhost:8200"),
            "ENABLED": os.getenv("APM_ENABLED", False) in ["True", "true", True],
            "RECORDING": os.getenv("APM_RECORDING", False) in ["True", "true"],
            "CAPTURE_HEADERS": os.getenv("APM_CAPTURE_HEADERS", True)
            in ["True", "true"],
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "ERROR"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
            "SERVICE_VERSION": os.getenv("VERSION", "1.0.0"),
            "CAPTURE_BODY": "all",
            "TRANSACTION_IGNORE_URLS": ["/admin", "/admin/*"],
        }
        self._make_apm_client()

    def _make_apm_client(self) -> Client:
        if self.client:
            return self.client

        self.client = make_apm_client(self.apm_config)
        return self.client


def create_app():
    app = FastAPI()
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(BASE_DIR, "static")),
        name="static",
    )
    app.mount("/admin", admin_app)

    admin_app.add_exception_handler(
        HTTP_500_INTERNAL_SERVER_ERROR, server_error_exception
    )
    admin_app.add_exception_handler(HTTP_404_NOT_FOUND, not_found_error_exception)
    admin_app.add_exception_handler(HTTP_403_FORBIDDEN, forbidden_error_exception)
    admin_app.add_exception_handler(HTTP_401_UNAUTHORIZED, unauthorized_error_exception)

    app.add_exception_handler(AuthJWTException, authjwt_exception_handler)

    @app.exception_handler(Exception)
    async def exception_handler(request, exc):
        if os.getenv("APM_ENABLED", False) in ["True", "true", True]:
            app.apm_client.capture_exception()
        return JSONResponse(
            status_code=500,
            content={
                "message": str(exc),
            },
        )

    @app.on_event("startup")
    async def startup():
        r = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf8",
            health_check_interval=30,
            retry_on_timeout=True,
        )
        await admin_app.configure(
            logo_url="https://preview.tabler.io/static/logo-white.svg",
            template_folders=[os.path.join(BASE_DIR, "templates")],
            favicon_url="https://raw.githubusercontent.com/fastapi-admin/fastapi-admin/dev/images/favicon.png",
            providers=[
                LoginProvider(
                    login_logo_url="https://preview.tabler.io/static/logo.svg",
                    admin_model=Admin,
                )
            ],
            redis=r,
        )
        app.sys_key = settings.SYS_KEY

    # @app.exception_handler(AuthJWTException)
    # def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    #     return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    if os.getenv("APM_ENABLED", False) in ["True", "true"]:
        apm = ApmClient().client
        app.add_middleware(
            ElasticAPM,
            client=apm,
        )
        app.apm_client = apm

    register_tortoise(
        app,
        config={
            "connections": {"default": database_url()},
            "apps": {
                "models": {
                    "models": [
                        "fa_admin.models",
                        "fa_admin.art_models",
                        "fa_admin.flow_models",
                    ],
                    "default_connection": "default",
                }
            },
            "use_tz": False,
        },
        generate_schemas=True,
    )
    app = add_routes(app)
    return app


def add_routes(app):
    app.include_router(api_route, prefix="/api")
    app.include_router(camunda_route, prefix="/engine")
    app.include_router(seasons_router, prefix="/seasons")
    app.include_router(warehouse_router, prefix="/warehouse")
    app.include_router(token_info_router, prefix="/token_info")
    return app


app_ = create_app()

if __name__ == "__main__":
    uvicorn.run("fa_admin.__main__:app_", host="0.0.0.0", port=8000, reload=True)
