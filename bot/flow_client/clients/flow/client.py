import json
from datetime import datetime, timedelta

import httpx
from uuid import UUID

from .schemas import AddUserSchema
from .schemas.response import UserSchema, ArtSchema
from .. import FlowUrls


class FlowClient:
    def __init__(
        self, base_url: str, sys_key: str, urls: FlowUrls | None = None
    ) -> None:
        headers = {"Content-Type": "application/json", "X-SYS-KEY": sys_key}
        self._base_url = base_url
        self._urls = urls or FlowUrls()
        transport = httpx.AsyncHTTPTransport(retries=3)
        self._client = httpx.AsyncClient(
            transport=transport,
            base_url=base_url,
            headers=headers,
            timeout=10,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def add_user(
        self,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language_code: str | None = None,
        is_admin: bool = False,
        is_suspicious: bool = False,
        telegram_user_id: int | None = None,
        webapp_user_id: UUID | None = None,
        is_block: bool = False,
        is_premium: bool = False,
    ) -> UserSchema:
        url = f"{self._base_url}/api/users"

        add_user_body = AddUserSchema(
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            is_admin=is_admin,
            is_suspicious=is_suspicious,
            telegram_user_id=telegram_user_id,
            webapp_user_id=webapp_user_id,
            is_block=is_block,
            is_premium=is_premium,
        )
        json_body = add_user_body.model_dump()
        response = await self._client.post(url, json=json_body)
        response.raise_for_status()
        return UserSchema.model_validate(response.json())

    async def get_user(
        self,
        webapp_id: str | None = None,
        camunda_user_id: str | None = None,
        telegram_user_id: int | None = None,
    ) -> None | UserSchema:
        url = f"{self._base_url}/api/users"
        params = {}

        if webapp_id is not None:
            params["webapp_user_id"] = webapp_id
        if camunda_user_id is not None:
            params["camunda_user_id"] = camunda_user_id
        if telegram_user_id is not None:
            params["telegram_user_id"] = telegram_user_id

        response = await self._client.get(url, params=params)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return UserSchema.model_validate(response.json())

    async def close(self):
        await self._client.aclose()

    async def get_art_by_id(self, art_id: str) -> ArtSchema:
        url = f"{self._base_url}/api/arts/{art_id}"
        response = await self._client.get(url)
        response.raise_for_status()
        return ArtSchema.model_validate(response.json())

    async def get_random_art_for_vote(
        self, exclude_ids: list | None = None
    ) -> ArtSchema | None:
        url = f"{self._base_url}/api/arts"
        params = {
            "limit": 1,
            "offset": 0,
            "parameters": {
                "nft_metadata__token_address__not_isnull": "true",
                "created_at__gt": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            },
        }
        if exclude_ids:
            params["parameters"]["id__not_in"] = exclude_ids
        params["parameters"] = json.dumps(params["parameters"])
        response = await self._client.get(url, params=params)
        response.raise_for_status()
        art = response.json()
        if not art:
            return None
        return ArtSchema.model_validate(art[0])

    async def get_all_quests(self) -> list[dict]:
        url = f"{self._base_url}/api/flows"
        response = await self._client.get(url)
        response.raise_for_status()
        return response.json()

    async def get_camunda_form_variables(
        self, webapp_user_id: str, task_id: str
    ) -> dict[str, str]:
        login_url = f"{self._base_url}/api/login/{webapp_user_id}"
        response = await self._client.get(login_url)
        access_token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{self._base_url}/engine/task/{task_id}/form-variables"
        response = await self._client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
