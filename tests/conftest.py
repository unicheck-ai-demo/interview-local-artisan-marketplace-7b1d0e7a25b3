from typing import Any

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def user(db: Any) -> Any:
    return get_user_model().objects.create_user(username='testuser', password='password123')


@pytest.fixture
def api_client() -> APIClient:
    client = APIClient()
    return client


@pytest.fixture
def authenticated_api_client(user: Any, api_client: APIClient) -> APIClient:
    api_client.force_authenticate(user)
    return api_client
