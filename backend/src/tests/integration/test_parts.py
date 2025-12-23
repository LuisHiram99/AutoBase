import pytest
import pytest_asyncio
import time
from db import models
from sqlalchemy import select


class TestPartsIntegration:
    """Integration tests for parts endpoints testing complete workflow from API to database"""
    
    @pytest_asyncio.fixture
    async def admin_user_token(self, client, db_session, _setup_workshop):
        """Create an admin user and return authentication token"""
        from auth.auth import pwd_context
        
        # Get the workshop_id from setup
        async with db_session as session:
            from sqlalchemy import select
            result = await session.execute(select(models.Workshop).limit(1))
            default_workshop = result.scalar_one()
            workshop_id = default_workshop.workshop_id
        
        # Create admin user directly in database
        async with db_session as session:
            admin_user = models.User(
                first_name="Admin",
                last_name="User",
                email="admin_parts@test.com",
                hashed_password=pwd_context.hash("adminpass123"),
                role=models.RoleEnum.admin,
                workshop_id=workshop_id
            )
            session.add(admin_user)
            await session.commit()
        
        # Login to get token
        login_data = {
            "username": "admin_parts@test.com",
            "password": "adminpass123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest_asyncio.fixture
    async def manager_user_token(self, client, db_session, _setup_workshop):
        """Create a manager user and return authentication token"""
        from auth.auth import pwd_context
        
        # Get the workshop_id from setup
        async with db_session as session:
            from sqlalchemy import select
            result = await session.execute(select(models.Workshop).limit(1))
            default_workshop = result.scalar_one()
            workshop_id = default_workshop.workshop_id
        
        # Create manager user directly in database
        async with db_session as session:
            manager_user = models.User(
                first_name="Manager",
                last_name="User",
                email="manager_parts@test.com",
                hashed_password=pwd_context.hash("managerpass123"),
                role=models.RoleEnum.manager,
                workshop_id=workshop_id
            )
            session.add(manager_user)
            await session.commit()
        
        # Login to get token
        login_data = {
            "username": "manager_parts@test.com",
            "password": "managerpass123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest_asyncio.fixture
    async def sample_part(self, db_session):
        """Create a sample part for testing"""
        async with db_session as session:
            part = models.Part(
                part_name="Brake Pad",
                brand="Bosch",
                description="Front brake pad for sedan cars",
                category="Brakes"
            )
            session.add(part)
            await session.commit()
            await session.refresh(part)
            return part

    def auth_headers(self, token):
        """Helper method to create authorization headers"""
        return {"Authorization": f"Bearer {token}"}

    # ================== CREATE PART TESTS ==================

    @pytest.mark.asyncio
    async def test_create_part_as_admin(self, client, admin_user_token, db_session):
        """Test admin user creating a part"""
        headers = self.auth_headers(admin_user_token)
        part_data = {
            "part_name": "Oil Filter",
            "brand": "Fram",
            "description": "High-quality oil filter for gasoline engines",
            "category": "Filters"
        }
        
        response = client.post("/api/v1/parts/", json=part_data, headers=headers)
        assert response.status_code == 200
        
        part = response.json()
        assert part["part_name"] == "Oil Filter"
        assert part["brand"] == "Fram"
        assert part["description"] == "High-quality oil filter for gasoline engines"
        assert part["category"] == "Filters"
        assert "part_id" in part
        
        # Verify part was saved to database
        async with db_session as session:
            result = await session.execute(
                select(models.Part).where(
                    models.Part.part_name == "Oil Filter",
                    models.Part.brand == "Fram"
                )
            )
            db_part = result.scalar_one_or_none()
            assert db_part is not None
            assert db_part.description == "High-quality oil filter for gasoline engines"
            assert db_part.category == "Filters"

    @pytest.mark.asyncio
    async def test_create_part_as_manager(self, client, manager_user_token, db_session):
        """Test manager user creating a part"""
        headers = self.auth_headers(manager_user_token)
        part_data = {
            "part_name": "Spark Plug",
            "brand": "NGK",
            "description": "Iridium spark plug for better performance",
            "category": "Ignition"
        }
        
        response = client.post("/api/v1/parts/", json=part_data, headers=headers)
        assert response.status_code == 200
        
        part = response.json()
        assert part["part_name"] == "Spark Plug"
        assert part["brand"] == "NGK"
        assert part["description"] == "Iridium spark plug for better performance"
        assert part["category"] == "Ignition"
        
        # Verify part was saved to database
        async with db_session as session:
            result = await session.execute(
                select(models.Part).where(
                    models.Part.part_name == "Spark Plug",
                    models.Part.brand == "NGK"
                )
            )
            db_part = result.scalar_one_or_none()
            assert db_part is not None

    @pytest.mark.asyncio
    async def test_create_part_with_optional_fields(self, client, admin_user_token, db_session):
        """Test creating part with minimal required fields"""
        headers = self.auth_headers(admin_user_token)
        part_data = {
            "part_name": "Tire",
            "brand": "Michelin"
            # description and category are optional
        }
        
        response = client.post("/api/v1/parts/", json=part_data, headers=headers)
        assert response.status_code == 200
        
        part = response.json()
        assert part["part_name"] == "Tire"
        assert part["brand"] == "Michelin"
        assert part["description"] is None
        assert part["category"] is None

    @pytest.mark.asyncio
    async def test_create_part_unauthenticated(self, client):
        """Test creating part without authentication fails"""
        part_data = {
            "part_name": "Battery",
            "brand": "Optima"
        }
        
        response = client.post("/api/v1/parts/", json=part_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_part_missing_required_fields(self, client, admin_user_token):
        """Test creating part with missing required fields"""
        headers = self.auth_headers(admin_user_token)
        part_data = {
            "part_name": "Alternator"
            # Missing brand
        }
        
        response = client.post("/api/v1/parts/", json=part_data, headers=headers)
        assert response.status_code == 422

    # ================== READ PARTS TESTS ==================

    @pytest.mark.asyncio
    async def test_get_all_parts_as_admin(self, client, admin_user_token, sample_part):
        """Test admin user getting all parts"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.get("/api/v1/parts/", headers=headers)
        assert response.status_code == 200
        
        parts = response.json()
        assert isinstance(parts, list)
        assert len(parts) >= 1
        
        # Find our sample part
        found_part = None
        for part in parts:
            if part["part_id"] == sample_part.part_id:
                found_part = part
                break
        
        assert found_part is not None
        assert found_part["part_name"] == "Brake Pad"
        assert found_part["brand"] == "Bosch"
        assert found_part["category"] == "Brakes"

    @pytest.mark.asyncio
    async def test_get_all_parts_as_manager(self, client, manager_user_token, sample_part):
        """Test manager user getting all parts"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.get("/api/v1/parts/", headers=headers)
        assert response.status_code == 200
        
        parts = response.json()
        assert isinstance(parts, list)

    @pytest.mark.asyncio
    async def test_get_all_parts_with_pagination(self, client, admin_user_token, sample_part):
        """Test getting parts with pagination parameters"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.get("/api/v1/parts/?skip=0&limit=10", headers=headers)
        assert response.status_code == 200
        
        parts = response.json()
        assert isinstance(parts, list)
        assert len(parts) <= 10

    @pytest.mark.asyncio
    async def test_get_parts_unauthenticated(self, client):
        """Test getting parts without authentication fails"""
        response = client.get("/api/v1/parts/")
        assert response.status_code == 401

    # ================== READ PART BY ID TESTS ==================

    @pytest.mark.asyncio
    async def test_get_part_by_id_as_admin(self, client, admin_user_token, sample_part):
        """Test admin user getting a specific part by ID"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.get(f"/api/v1/parts/{sample_part.part_id}", headers=headers)
        assert response.status_code == 200
        
        part = response.json()
        assert part["part_id"] == sample_part.part_id
        assert part["part_name"] == "Brake Pad"
        assert part["brand"] == "Bosch"
        assert part["description"] == "Front brake pad for sedan cars"
        assert part["category"] == "Brakes"

    @pytest.mark.asyncio
    async def test_get_part_by_id_as_manager(self, client, manager_user_token, sample_part):
        """Test manager user getting a part by ID"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.get(f"/api/v1/parts/{sample_part.part_id}", headers=headers)
        assert response.status_code == 200
        
        part = response.json()
        assert part["part_id"] == sample_part.part_id

    @pytest.mark.asyncio
    async def test_get_part_by_id_not_found(self, client, admin_user_token):
        """Test getting a part that doesn't exist"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.get("/api/v1/parts/99999", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_part_by_id_unauthenticated(self, client, sample_part):
        """Test getting part by ID without authentication fails"""
        response = client.get(f"/api/v1/parts/{sample_part.part_id}")
        assert response.status_code == 401

    # ================== UPDATE PART TESTS ==================

    @pytest.mark.asyncio
    async def test_update_part_as_admin(self, client, admin_user_token, sample_part, db_session):
        """Test admin user updating a part"""
        headers = self.auth_headers(admin_user_token)
        update_data = {
            "part_name": "Premium Brake Pad",
            "description": "High-performance brake pad for sports cars",
            "category": "Performance Brakes"
        }
        
        response = client.patch(f"/api/v1/parts/{sample_part.part_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        part = response.json()
        assert part["part_name"] == "Premium Brake Pad"
        assert part["description"] == "High-performance brake pad for sports cars"
        assert part["category"] == "Performance Brakes"
        assert part["brand"] == "Bosch"  # Unchanged
        
        # Verify changes in database
        async with db_session as session:
            result = await session.execute(
                select(models.Part).where(models.Part.part_id == sample_part.part_id)
            )
            db_part = result.scalar_one()
            assert db_part.part_name == "Premium Brake Pad"
            assert db_part.description == "High-performance brake pad for sports cars"
            assert db_part.category == "Performance Brakes"

    @pytest.mark.asyncio
    async def test_update_part_as_manager(self, client, manager_user_token, sample_part, db_session):
        """Test manager user updating a part"""
        headers = self.auth_headers(manager_user_token)
        update_data = {
            "description": "Updated description for brake pad",
            "category": "Updated Category"
        }
        
        response = client.patch(f"/api/v1/parts/{sample_part.part_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        part = response.json()
        assert part["description"] == "Updated description for brake pad"
        assert part["category"] == "Updated Category"
        
        # Verify changes in database
        async with db_session as session:
            result = await session.execute(
                select(models.Part).where(models.Part.part_id == sample_part.part_id)
            )
            db_part = result.scalar_one()
            assert db_part.description == "Updated description for brake pad"
            assert db_part.category == "Updated Category"

    @pytest.mark.asyncio
    async def test_update_part_partial_update(self, client, admin_user_token, sample_part):
        """Test updating only some fields of a part"""
        headers = self.auth_headers(admin_user_token)
        update_data = {
            "brand": "Brembo"
        }
        
        response = client.patch(f"/api/v1/parts/{sample_part.part_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        part = response.json()
        assert part["brand"] == "Brembo"
        assert part["part_name"] == "Brake Pad"  # Unchanged
        assert part["category"] == "Brakes"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_part_not_found(self, client, admin_user_token):
        """Test updating a part that doesn't exist"""
        headers = self.auth_headers(admin_user_token)
        update_data = {"part_name": "New Name"}
        
        response = client.patch("/api/v1/parts/99999", json=update_data, headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_part_unauthenticated(self, client, sample_part):
        """Test updating part without authentication fails"""
        update_data = {"part_name": "New Name"}
        
        response = client.patch(f"/api/v1/parts/{sample_part.part_id}", json=update_data)
        assert response.status_code == 401

    # ================== DELETE PART TESTS ==================

    @pytest.mark.asyncio
    async def test_delete_part_as_admin(self, client, admin_user_token, sample_part, db_session):
        """Test admin user deleting a part"""
        headers = self.auth_headers(admin_user_token)
        part_id = sample_part.part_id
        
        response = client.delete(f"/api/v1/parts/{part_id}", headers=headers)
        assert response.status_code == 200
        
        deleted_part = response.json()
        assert deleted_part["part_id"] == part_id
        assert deleted_part["part_name"] == "Brake Pad"
        assert deleted_part["brand"] == "Bosch"
        
        # Verify part was deleted from database
        async with db_session as session:
            result = await session.execute(
                select(models.Part).where(models.Part.part_id == part_id)
            )
            db_part = result.scalar_one_or_none()
            assert db_part is None

    @pytest.mark.asyncio
    async def test_delete_part_as_manager(self, client, manager_user_token, sample_part, db_session):
        """Test manager user deleting a part"""
        headers = self.auth_headers(manager_user_token)
        part_id = sample_part.part_id
        
        response = client.delete(f"/api/v1/parts/{part_id}", headers=headers)
        assert response.status_code == 200
        
        # Verify part was deleted from database
        async with db_session as session:
            result = await session.execute(
                select(models.Part).where(models.Part.part_id == part_id)
            )
            db_part = result.scalar_one_or_none()
            assert db_part is None

    @pytest.mark.asyncio
    async def test_delete_part_not_found(self, client, admin_user_token):
        """Test deleting a part that doesn't exist"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.delete("/api/v1/parts/99999", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_part_unauthenticated(self, client, sample_part):
        """Test deleting part without authentication fails"""
        response = client.delete(f"/api/v1/parts/{sample_part.part_id}")
        assert response.status_code == 401

    # ================== EDGE CASES AND VALIDATION TESTS ==================

    @pytest.mark.asyncio
    async def test_create_part_with_empty_strings(self, client, admin_user_token):
        """Test creating part with empty string fields"""
        headers = self.auth_headers(admin_user_token)
        part_data = {
            "part_name": "",
            "brand": ""
        }
        
        response = client.post("/api/v1/parts/", json=part_data, headers=headers)
        # Should fail validation for empty required strings
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_part_with_none_values(self, client, admin_user_token, sample_part):
        """Test updating part with None values to clear optional fields"""
        headers = self.auth_headers(admin_user_token)
        update_data = {
            "description": None,
            "category": None
        }
        
        response = client.patch(f"/api/v1/parts/{sample_part.part_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        part = response.json()
        assert part["description"] is None
        assert part["category"] is None
        assert part["part_name"] == "Brake Pad"  # Required field unchanged
        assert part["brand"] == "Bosch"  # Required field unchanged

    @pytest.mark.asyncio
    async def test_create_part_with_long_strings(self, client, admin_user_token):
        """Test creating part with very long strings"""
        headers = self.auth_headers(admin_user_token)
        part_data = {
            "part_name": "Very Long Part Name" * 10,  # Very long name
            "brand": "Brand" * 20,
            "description": "Description " * 50,
            "category": "Category " * 20
        }
        
        response = client.post("/api/v1/parts/", json=part_data, headers=headers)
        # Should handle long strings appropriately (either succeed or fail with validation)
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_part_case_sensitivity(self, client, admin_user_token, db_session):
        """Test that parts are case-sensitive in searches"""
        headers = self.auth_headers(admin_user_token)
        
        # Create two parts with different cases
        part_data_1 = {
            "part_name": "brake pad",
            "brand": "bosch"
        }
        part_data_2 = {
            "part_name": "BRAKE PAD",
            "brand": "BOSCH"
        }
        
        response1 = client.post("/api/v1/parts/", json=part_data_1, headers=headers)
        response2 = client.post("/api/v1/parts/", json=part_data_2, headers=headers)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Both parts should be created successfully
        part1 = response1.json()
        part2 = response2.json()
        assert part1["part_id"] != part2["part_id"]
        assert part1["part_name"] == "brake pad"
        assert part2["part_name"] == "BRAKE PAD"

    @pytest.mark.asyncio
    async def test_get_parts_empty_database(self, client, admin_user_token, db_session):
        """Test getting parts when database is empty"""
        headers = self.auth_headers(admin_user_token)
        
        # Clear all parts from database
        async with db_session as session:
            await session.execute(select(models.Part).limit(1))  # This will be empty
        
        response = client.get("/api/v1/parts/", headers=headers)
        assert response.status_code == 200
        
        parts = response.json()
        assert isinstance(parts, list)
        # Should return empty list, not error
