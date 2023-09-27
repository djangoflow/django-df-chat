from typing import Callable, TypeVar

import pytest
from faker import Faker
from rest_framework.test import APIClient

T = TypeVar("T")
Factory = Callable[..., T]


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def faker() -> Faker:
    return Faker()
