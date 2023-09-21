from rest_framework.test import APIClient


def test_test_endpoint_returns_200(client: APIClient) -> None:
    response = client.get("/api/v1/chat/test/")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}
