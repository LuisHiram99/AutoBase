import pytest
from db import models
from auth import auth
from jose import jwt    
from sqlalchemy import select

class TestAuthService:
    def test_verify_password(self):
        """Test password hashing and verification"""
        plain_password = "mysecretpassword"
        hashed_password = auth.pwd_context.hash(plain_password)
        assert auth.pwd_context.verify(plain_password, hashed_password)
        assert not auth.pwd_context.verify("wrongpassword", hashed_password)

    def test_create_user(self, client, db_session):
        """Test user creation via API endpoint"""
        user_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@mail.com",
            "password": "securepassword"
        }
        response = client.post("/api/v1/auth/signup", json=user_data)
        assert response.status_code == 201
        assert response.json()["message"] == "User created successfully"

    def test_create_user_duplicate_email(self, client):
        """Test that creating a user with a duplicate email returns an error"""
        user_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "duplicate@mail.com",
            "password": "securepassword"
        }
        
        # First creation should succeed
        response = client.post("/api/v1/auth/signup", json=user_data)
        assert response.status_code == 201
        
        # Second creation with same email should fail
        response = client.post("/api/v1/auth/signup", json=user_data)
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    def test_create_invalid_user(self, client):
        """Test that creating a user with invalid email returns validation error"""
        user_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "invalidemail",  # Invalid email format
            "password": "securepassword"
        }
        response = client.post("/api/v1/auth/signup", json=user_data)
        assert response.status_code == 422  # Validation error

    def test_login_for_access_token(self, client):
        """Test user authentication and JWT token generation via API"""
        # First, create a user
        user_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "testlogin@mail.com",
            "password": "securepassword"
        }
        response = client.post("/api/v1/auth/signup", json=user_data)
        assert response.status_code == 201
        
        # Now test login with form data (OAuth2 expects form data)
        login_data = {
            "username": "testlogin@mail.com",  # OAuth2 uses 'username' field
            "password": "securepassword"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        # Verify token is returned
        response_data = response.json()
        assert "access_token" in response_data
        assert response_data["token_type"] == "bearer"
        
        # Decode and verify token
        token = response_data["access_token"]
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        assert payload["sub"] == "testlogin@mail.com"
        assert "user_id" in payload
    
    def test_login_with_wrong_password(self, client):
        """Test login with incorrect password returns error"""
        # Create a user
        user_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "testfail@mail.com",
            "password": "correctpassword"
        }
        client.post("/api/v1/auth/signup", json=user_data)
        
        # Try to login with wrong password
        login_data = {
            "username": "testfail@mail.com",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user returns error"""
        login_data = {
            "username": "nonexistent@mail.com",
            "password": "anypassword"
        }
        response = client.post('/api/v1/auth/login', data=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_create_user_missing_fields(self, client):
        """Test that creating a user with missing fields returns validation error"""
        user_data = {
            "first_name": "Test",
            # Missing last_name
            "email": "testmissing@mail.com",
            "password": "securepassword"
        }
        response = client.post("/api/v1/auth/signup", json=user_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_user_role_assignment(self,client, db_session):
        """Test that a newly created user is assigned the default role"""
        user_data = {
            "first_name": "Role",
            "last_name": "Tester",
            "email": "roletester@mail.com",
            "password": "securepassword"
        }
        response = client.post("/api/v1/auth/signup", json=user_data)
        assert response.status_code == 201
        
        # Verify user role in database

        result = await db_session.execute(select(models.User).where(models.User.email == "roletester@mail.com"))
        user = result.scalar_one()
        assert user.role == models.RoleEnum.manager
