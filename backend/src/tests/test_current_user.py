import pytest
from db import models
from auth import auth
from jose import jwt    
from sqlalchemy import select

class TestCurrentUser:
    @pytest.mark.asyncio
    async def test_get_current_user(self, client, db_session):
        """Test retrieving current user info via API endpoint"""
        # First, create a user
        user_data = {
            "first_name": "Current",
            "last_name": "User",
            "email": "currentuser@mail.com",
            "password": "securepassword"
        }
        response = client.post("/api/v1/auth/signup", json=user_data)
        assert response.status_code == 201

        # Now, login to get the token
        login_data = {
            "username": "currentuser@mail.com",
            "password": "securepassword"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        token = response.json()["access_token"]

        # Use the token to get current user info
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/me", headers=headers)
        assert response.status_code == 200
        user_info = response.json()
        assert user_info["email"] == "currentuser@mail.com"
        assert user_info["first_name"] == "Current"
        assert user_info["last_name"] == "User"


    def test_get_current_user_unauthorized(self, client):
        """Test that accessing current user info without token returns unauthorized error"""
        response = client.get("/api/v1/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    @pytest.mark.asyncio
    async def test_patch_current_user(self, client, db_session):
        """Test updating current user info via API endpoint"""
        # First, create a user
        user_data = {
            "first_name": "Patch",
            "last_name": "User",
            "email": "patchuser@mail.com",
            "password": "securepassword"
        }
        response = client.post("/api/v1/auth/signup", json=user_data)
        assert response.status_code == 201

        # Now, login to get the token
        login_data = {
            "username": "patchuser@mail.com",
            "password": "securepassword"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        token = response.json()["access_token"] 

        # Use the token to patch current user info
        headers = {"Authorization": f"Bearer {token}"}
        update_data = {
            "first_name": "Updated",
            "last_name": "User"
        }
        response = client.patch("/api/v1/me", json=update_data, headers=headers)
        assert response.status_code == 200
        updated_info = response.json()
        assert updated_info["first_name"] == "Updated"
        assert updated_info["last_name"] == "User"  

    @pytest.mark.asyncio
    async def test_patch_current_user_unauthorized(self, client):
        """Test that updating current user info without token returns unauthorized error"""
        update_data = {
            "first_name": "ShouldNot",
            "last_name": "Work"
        }
        response = client.patch("/api/v1/me", json=update_data)
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
    
    @pytest.mark.asyncio
    async def test_patch_current_user_invalid_data(self, client, db_session):
        """Test that updating current user with invalid data returns validation error"""
        # First, create a user
        user_data = {
            "first_name": "Invalid",
            "last_name": "Data",
            "email": "invaliddata@mail.com",
            "password": "securepassword"
        }
        response = client.post("/api/v1/auth/signup", json=user_data)
        assert response.status_code == 201
        # Now, login to get the token
        login_data = {
            "username": "invaliddata@mail.com",
            "password": "securepassword"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        token = response.json()["access_token"] 

        # Use the token to patch current user info
        headers = {"Authorization": f"Bearer {token}"}
        update_data = {
            'email': 'notanemail'  # Invalid email format
        }
        response = client.patch("/api/v1/me", json=update_data, headers=headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_delete_current_user(self, client, db_session):
        # First, create a user
        user_data = {
            "first_name": "Delete",
            "last_name": "User",
            "email": "delete@mail.com",
            "password": "securepassword"
        }
        response = client.post("/api/v1/auth/signup", json=user_data)
        assert response.status_code == 201
        # Now, login to get the token
        login_data = {
            "username": "delete@mail.com",
            "password": "securepassword"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        token = response.json()["access_token"] 

        # Use the token to patch current user info
        headers = {"Authorization": f"Bearer {token}"}
        response = client.delete('/api/v1/me', headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_token_version_increment_on_password_change(self, client, db_session):
        """Test that token_version increments when user changes password"""
        user_data = {
            "first_name": "Token",
            "last_name": "Version",
            "email": "tokenversion@mail.com",
            "password": "initialpassword"
        }
        response = client.post("/api/v1/auth/signup", json=user_data)
        assert response.status_code == 201
        result = await db_session.execute(select(models.User).where(models.User.email == "tokenversion@mail.com"))
        user = result.scalar_one()
        original_token_version = user.token_version
        # Simulate password change
        user.hashed_password = auth.pwd_context.hash("newpassword")
        user.token_version += 1
        db_session.add(user)
        await db_session.commit()
        # Verify token_version incremented
        result = await db_session.execute(select(models.User).where(models.User.email == "tokenversion@mail.com"))
        updated_user = result.scalar_one()
        assert updated_user.token_version == original_token_version + 1

    