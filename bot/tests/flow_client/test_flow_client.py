import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from flow_client.clients.flow.client import FlowClient
from flow_client.clients.flow.schemas import AddUserSchema
from flow_client.clients.flow.schemas.response import UserSchema


@pytest.mark.asyncio
async def test_add_user():
    # Mock response data
    mock_response_data = {
        "id": str(uuid4()),
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en",
        "is_admin": False,
        "is_suspicious": False,
        "telegram_user_id": None,
        "webapp_user_id": None,
        "is_block": False,
        "is_premium": False,
    }

    # Mock the httpx.AsyncClient.post method
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response

        # Instantiate the FlowClient
        client = FlowClient(
            base_url="http://testserver",
            sys_key="testkey"
        )

        # Call the add_user method
        response = await client.add_user(
            username="testuser",
            first_name="Test",
            last_name="User",
            language_code="en",
            is_admin=False,
            is_suspicious=False,
            telegram_user_id=None,
            webapp_user_id=None,
            is_block=False,
            is_premium=False,
        )

        # Assert the response
        assert response == UserSchema.model_validate(mock_response_data)


@pytest.mark.skip("This test is functional")
@pytest.mark.asyncio
async def test_add_user_functional():
    # Mock response data
    mock_response_data = {
        "id": str(uuid4()),
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en",
        "is_admin": False,
        "is_suspicious": False,
        "camunda_user_id": None,
        "camunda_key": None,
        "telegram_user_id": None,
        "webapp_user_id": None,
        "is_block": False,
        "is_premium": False,
    }

    # Mock the aiohttp.ClientSession.post method
    client = FlowClient(
        base_url="http://localhost:8000/",
        sys_key="secret",
        transport=httpx.AsyncHTTPTransport()
    )

    # Call the add_user method
    response = await client.add_user(
        username="testuser",
        first_name="Test",
        last_name="User",
        language_code="en",
        is_admin=False,
        is_suspicious=False,
        telegram_user_id=None,
        webapp_user_id=None,
        is_block=False,
        is_premium=False,
    )

    # Assert the response
    assert response == UserSchema.model_validate(mock_response_data)
