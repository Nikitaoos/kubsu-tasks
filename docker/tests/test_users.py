from unittest.mock import ANY

import pytest

pytestmark = pytest.mark.asyncio


async def test_create_user(test_client):
    response = await test_client.post("/users/", json={"name": "John Doe"})
    assert response.status_code == 200
    assert response.json() == {"id": ANY, "name": "John Doe"}


async def test_read_users(test_client, user):
    response = await test_client.get("/users/")
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_read_user(test_client, user):
    response = await test_client.get(f"/users/{user.id}")
    assert response.status_code == 200
    assert response.json() == {"id": user.id, "name": user.name}


async def test_update_user(test_client, user):
    response = await test_client.patch(f"/users/{user.id}", json={"name": "My Name"})
    assert response.status_code == 200
    assert response.json() == {"id": user.id, "name": "My Name"}


async def test_delete_user(test_client, user):
    response = await test_client.delete(f"/users/{user.id}")
    assert response.status_code == 200
    assert response.json() == {"detail": "User deleted"}


async def test_read_nonexistent_user(test_client, user):
    response = await test_client.get(f"/users/{user.id - 1}")
    assert response.status_code == 404


async def test_delete_nonexistent_user(test_client):
    response = await test_client.delete("/users/999999")
    assert response.status_code == 404


async def test_update_nonexistent_user(test_client):
    response = await test_client.patch("/users/999999", json={"name": "X"})
    assert response.status_code == 404


@pytest.mark.parametrize("name", ["", "   ", "x" * 101])
async def test_create_user_invalid_name(test_client, name):
    response = await test_client.post("/users/", json={"name": name})
    assert response.status_code == 422


async def test_create_user_strips_name(test_client):
    response = await test_client.post("/users/", json={"name": "  Ann  "})
    assert response.status_code == 200
    assert response.json()["name"] == "Ann"


async def test_pagination(test_client):
    for i in range(5):
        await test_client.post("/users/", json={"name": f"user{i}"})
    response = await test_client.get("/users/", params={"skip": 1, "limit": 2})
    assert response.status_code == 200
    assert [u["name"] for u in response.json()] == ["user1", "user2"]


@pytest.mark.parametrize("params", [{"skip": -1}, {"limit": 0}, {"limit": 1000}])
async def test_pagination_invalid(test_client, params):
    response = await test_client.get("/users/", params=params)
    assert response.status_code == 422


async def test_health(test_client):
    response = await test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
