from async_fastapi_jwt_auth.exceptions import AuthJWTException
from starlette.requests import Request
from starlette.responses import JSONResponse


def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
