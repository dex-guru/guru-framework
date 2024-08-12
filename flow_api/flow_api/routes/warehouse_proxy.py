import aiohttp
import requests
from aiocache import cached
from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import Response
from yarl import URL

from fa_admin import settings
from fa_admin.utils import CACHE_CONFIG

router = APIRouter()


@router.get("/{path:path}")
async def warehouse(
    request: Request,
    path: str,
):
    query_params = dict(request.query_params)
    headers = dict(request.headers)
    body = await request.body()
    response = await get_warehouse(
        path=path,
        query_params=query_params,
        headers=headers,
        body=body,
    )
    return response


@cached(ttl=300, **CACHE_CONFIG)
async def get_warehouse(
    path: str,
    query_params: dict | None = None,
    headers: dict | None = None,
    body: bytes | None = None,
):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            URL(settings.WAREHOUSE_URL).with_path(path),
            params=query_params,
            headers=headers,
            data=body,
        ) as response:
            return Response(
                content=await response.content.read(),
                status_code=response.status,
                headers=response.headers,
            )
