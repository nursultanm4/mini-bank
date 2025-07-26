import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Register
        response = await ac.post("/register/", json={
            "username": "testuser",
            "password": "Testpass123!"
        })
        assert response.status_code == 200

        # Login
        response = await ac.post("/login/", json={
            "username": "testuser",
            "password": "Testpass123!"
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        assert token

        headers = {"Authorization": f"Bearer {token}"}

        # Create account
        response = await ac.post("/accounts/", json={
            "name": "TestAccount",
            "balance": 100.0
        }, headers=headers)
        assert response.status_code == 200
        account_id = response.json()["id"]

        # Get balance
        response = await ac.get(f"/accounts/{account_id}/balance", headers=headers)
        assert response.status_code == 200
        assert response.json()["balance"] == 100.0

        # Make transaction (to self for test)
        response = await ac.post("/transactions/", json={
            "from_account_id": account_id,
            "to_account_id": account_id,
            "amount": 10.0
        }, headers=headers)
        assert response.status_code == 200

        # Get transactions
        response = await ac.get("/transactions/", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)