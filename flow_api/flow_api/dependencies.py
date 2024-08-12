from fastapi import HTTPException, Depends
from starlette.requests import Request

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from configs.app_config import settings
from fa_admin.settings import ENVIRONMENT, SYS_KEY

auth_dependency = AuthJWTBearer()


class SysKeyAuth(AuthJWT):
    async def get_raw_jwt(
        self, encoded_token: str | None = None
    ) -> dict[str, str | int | bool] | None:
        return {
            "camunda_user_id": settings.ENGINE_USERNAME,
            "camunda_key": settings.ENGINE_PASSWORD,
        }

    async def jwt_required(self, *args, **kwargs) -> None:
        return


def sys_key_depends(request: Request):
    if ENVIRONMENT == "dev":
        return True
    if SYS_KEY != request.headers.get("X-SYS-KEY"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


async def sys_key_or_jwt_depends(
    request: Request, auth: AuthJWT = Depends(auth_dependency)
) -> AuthJWT:
    if ENVIRONMENT == "dev":
        return SysKeyAuth()
    if request.headers.get("Authorization"):
        await auth.jwt_required()
        return auth
    if SYS_KEY == request.headers.get("X-SYS-KEY"):
        return SysKeyAuth()
    raise HTTPException(status_code=401, detail="Unauthorized")
