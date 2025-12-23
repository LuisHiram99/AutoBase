import pytest
import pytest_asyncio
import time
import tempfile
import os
from pathlib import Path
from db import models
from sqlalchemy import select
from fastapi import UploadFile
from io import BytesIO


class TestWorkshopsIntegration:
    """Integration tests for workshops endpoints testing complete workflow from API to database"""
    
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
                email="admin_workshops@test.com",
                hashed_password=pwd_context.hash("adminpass123"),
                role=models.RoleEnum.admin,
                workshop_id=workshop_id
            )
            session.add(admin_user)
            await session.commit()
        
        # Login to get token
        login_data = {
            "username": "admin_workshops@test.com",
            "password": "adminpass123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest_asyncio.fixture
    async def manager_user_token(self, client, db_session, _setup_workshop):
        """Create a manager user and return authentication token"""
        from auth.auth import pwd_context
        
        # Create a second workshop (the first one from _setup_workshop might be ID 1)
        async with db_session as session:
            workshop = models.Workshop(
                workshop_name="Manager's Existing Workshop",
                address="Manager's Address",
                opening_hours="09:00",
                closing_hours="17:00"
            )
            session.add(workshop)
            await session.commit()
            await session.refresh(workshop)
            workshop_id = workshop.workshop_id
        
        # Create manager user directly in database with the new workshop
        async with db_session as session:
            manager_user = models.User(
                first_name="Manager",
                last_name="User",
                email="manager_workshops@test.com",
                hashed_password=pwd_context.hash("managerpass123"),
                role=models.RoleEnum.manager,
                workshop_id=workshop_id
            )
            session.add(manager_user)
            await session.commit()
        
        # Login to get token
        login_data = {
            "username": "manager_workshops@test.com",
            "password": "managerpass123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest_asyncio.fixture
    async def manager_user_no_workshop_token(self, client, db_session):
        """Create a manager user with default workshop (workshop_id=1) for testing workshop creation"""
        from auth.auth import pwd_context
        
        # Create manager user with default workshop
        async with db_session as session:
            manager_user = models.User(
                first_name="New",
                last_name="Manager",
                email="new_manager_workshops@test.com",
                hashed_password=pwd_context.hash("newmanagerpass123"),
                role=models.RoleEnum.manager,
                workshop_id=1  # Default workshop
            )
            session.add(manager_user)
            await session.commit()
        
        # Login to get token
        login_data = {
            "username": "new_manager_workshops@test.com",
            "password": "newmanagerpass123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest_asyncio.fixture
    async def sample_workshop(self, db_session):
        """Create a sample workshop for testing"""
        async with db_session as session:
            workshop = models.Workshop(
                workshop_name="Sample Auto Shop",
                address="123 Main St, City, State",
                opening_hours="08:00",
                closing_hours="18:00",
                workshop_logo=None
            )
            session.add(workshop)
            await session.commit()
            await session.refresh(workshop)
            return workshop

    @pytest_asyncio.fixture
    async def sample_part(self, db_session):
        """Create a sample part for workshop-part testing"""
        async with db_session as session:
            part = models.Part(
                part_name="Brake Pad",
                brand="Bosch",
                description="Front brake pad",
                category="Brakes"
            )
            session.add(part)
            await session.commit()
            await session.refresh(part)
            return part

    @pytest_asyncio.fixture
    async def sample_part_workshop(self, db_session, sample_part, _setup_workshop):
        """Create a sample part-workshop relationship"""
        async with db_session as session:
            # Get workshop_id from setup
            result = await session.execute(select(models.Workshop).limit(1))
            default_workshop = result.scalar_one()
            workshop_id = default_workshop.workshop_id
            
            part_workshop = models.PartWorkshop(
                part_id=sample_part.part_id,
                workshop_id=workshop_id,
                quantity=10,
                purchase_price=2500,  # $25.00
                sale_price=5000       # $50.00
            )
            session.add(part_workshop)
            await session.commit()
            await session.refresh(part_workshop)
            return part_workshop

    def auth_headers(self, token):
        """Helper method to create authorization headers"""
        return {"Authorization": f"Bearer {token}"}

    async def get_default_workshop_id(self, db_session):
        """Helper method to get the default workshop ID"""
        async with db_session as session:
            from sqlalchemy import select
            result = await session.execute(select(models.Workshop).limit(1))
            default_workshop = result.scalar_one()
            return default_workshop.workshop_id

    def create_test_image_file(self):
        """Helper to create a test image file"""
        # Create a simple 1x1 PNG image
        image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xd2\x01\xa1\x00\x05\x17\x72\xb9\xf4\x00\x00\x00\x00IEND\xaeB`\x82'
        return BytesIO(image_data), "test_image.png"

    # ================== CREATE WORKSHOP TESTS ==================

    @pytest.mark.asyncio
    async def test_create_workshop_as_admin(self, client, admin_user_token, db_session):
        """Test admin user creating a workshop"""
        headers = self.auth_headers(admin_user_token)
        workshop_data = {
            "workshop_name": "New Auto Center",
            "address": "456 Auto St, Mechanic City",
            "opening_hours": "07:00",
            "closing_hours": "19:00"
        }
        
        response = client.post("/api/v1/workshops/", json=workshop_data, headers=headers)
        assert response.status_code == 200
        
        workshop = response.json()
        assert workshop["workshop_name"] == "New Auto Center"
        assert workshop["address"] == "456 Auto St, Mechanic City"
        assert workshop["opening_hours"] == "07:00"
        assert workshop["closing_hours"] == "19:00"
        assert "workshop_id" in workshop
        
        # Verify workshop was saved to database
        async with db_session as session:
            result = await session.execute(
                select(models.Workshop).where(
                    models.Workshop.workshop_name == "New Auto Center"
                )
            )
            db_workshop = result.scalar_one_or_none()
            assert db_workshop is not None
            assert db_workshop.address == "456 Auto St, Mechanic City"

    @pytest.mark.asyncio
    async def test_create_workshop_as_manager_without_workshop(self, client, manager_user_no_workshop_token, db_session):
        """Test manager user creating their own workshop"""
        headers = self.auth_headers(manager_user_no_workshop_token)
        workshop_data = {
            "workshop_name": "Manager's Workshop",
            "address": "789 Manager Ave",
            "opening_hours": "08:30",
            "closing_hours": "17:30"
        }
        
        response = client.post("/api/v1/workshops/", json=workshop_data, headers=headers)
        assert response.status_code == 200
        
        workshop = response.json()
        assert workshop["workshop_name"] == "Manager's Workshop"
        assert workshop["address"] == "789 Manager Ave"
        
        # Verify workshop was saved and user's workshop_id was updated
        async with db_session as session:
            result = await session.execute(
                select(models.Workshop).where(
                    models.Workshop.workshop_name == "Manager's Workshop"
                )
            )
            db_workshop = result.scalar_one_or_none()
            assert db_workshop is not None
            
            # Check user's workshop_id was updated
            result = await session.execute(
                select(models.User).where(
                    models.User.email == "new_manager_workshops@test.com"
                )
            )
            db_user = result.scalar_one()
            assert db_user.workshop_id == db_workshop.workshop_id

    @pytest.mark.asyncio
    async def test_create_workshop_as_manager_already_has_workshop(self, client, manager_user_token):
        """Test manager user cannot create workshop when they already have one"""
        headers = self.auth_headers(manager_user_token)
        workshop_data = {
            "workshop_name": "Second Workshop",
            "address": "Second Address"
        }
        
        response = client.post("/api/v1/workshops/", json=workshop_data, headers=headers)
        assert response.status_code == 400
        assert "already has a workshop" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_workshop_unauthenticated(self, client):
        """Test creating workshop without authentication fails"""
        workshop_data = {
            "workshop_name": "Unauthorized Workshop",
            "address": "No Auth Address"
        }
        
        response = client.post("/api/v1/workshops/", json=workshop_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_workshop_missing_required_fields(self, client, admin_user_token):
        """Test creating workshop with missing required fields"""
        headers = self.auth_headers(admin_user_token)
        workshop_data = {
            "address": "Missing Name Workshop"
            # Missing workshop_name
        }
        
        response = client.post("/api/v1/workshops/", json=workshop_data, headers=headers)
        assert response.status_code == 422

    # ================== READ WORKSHOPS TESTS ==================

    @pytest.mark.asyncio
    async def test_get_all_workshops_as_admin(self, client, admin_user_token, sample_workshop):
        """Test admin user getting all workshops"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.get("/api/v1/workshops/", headers=headers)
        assert response.status_code == 200
        
        workshops = response.json()
        assert isinstance(workshops, list)
        assert len(workshops) >= 1
        
        # Find our sample workshop
        found_workshop = None
        for workshop in workshops:
            if workshop["workshop_id"] == sample_workshop.workshop_id:
                found_workshop = workshop
                break
        
        assert found_workshop is not None
        assert found_workshop["workshop_name"] == "Sample Auto Shop"

    @pytest.mark.asyncio
    async def test_get_current_user_workshop_as_manager(self, client, manager_user_token, db_session):
        """Test manager user getting their own workshop"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.get("/api/v1/workshops/", headers=headers)
        assert response.status_code == 200
        
        # Manager should get their own workshop (as a single-item list based on service logic)
        workshop = response.json()
        assert workshop["workshop_name"] == "Test Workshop"  # From _setup_workshop fixture

    @pytest.mark.asyncio
    async def test_get_workshops_with_pagination_as_admin(self, client, admin_user_token):
        """Test getting workshops with pagination parameters"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.get("/api/v1/workshops/?skip=0&limit=10", headers=headers)
        assert response.status_code == 200
        
        workshops = response.json()
        assert isinstance(workshops, list)
        assert len(workshops) <= 10

    @pytest.mark.asyncio
    async def test_get_workshops_unauthenticated(self, client):
        """Test getting workshops without authentication fails"""
        response = client.get("/api/v1/workshops/")
        assert response.status_code == 401

    # ================== READ WORKSHOP BY ID TESTS (ADMIN ONLY) ==================

    @pytest.mark.asyncio
    async def test_get_workshop_by_id_as_admin(self, client, admin_user_token, sample_workshop):
        """Test admin user getting a specific workshop by ID"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.get(f"/api/v1/workshops/{sample_workshop.workshop_id}", headers=headers)
        assert response.status_code == 200
        
        workshop = response.json()
        assert workshop["workshop_id"] == sample_workshop.workshop_id
        assert workshop["workshop_name"] == "Sample Auto Shop"
        assert workshop["address"] == "123 Main St, City, State"

    @pytest.mark.asyncio
    async def test_get_workshop_by_id_as_manager_forbidden(self, client, manager_user_token, sample_workshop):
        """Test manager user cannot get workshop by ID (admin required)"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.get(f"/api/v1/workshops/{sample_workshop.workshop_id}", headers=headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_workshop_by_id_not_found(self, client, admin_user_token):
        """Test getting a workshop that doesn't exist"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.get("/api/v1/workshops/99999", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_workshop_by_id_unauthenticated(self, client, sample_workshop):
        """Test getting workshop by ID without authentication fails"""
        response = client.get(f"/api/v1/workshops/{sample_workshop.workshop_id}")
        assert response.status_code == 401

    # ================== UPDATE WORKSHOP TESTS ==================

    @pytest.mark.asyncio
    async def test_update_workshop_as_admin(self, client, admin_user_token, sample_workshop, db_session):
        """Test admin user updating a workshop"""
        headers = self.auth_headers(admin_user_token)
        update_data = {
            "workshop_name": "Updated Auto Shop",
            "address": "456 Updated St",
            "opening_hours": "07:30",
            "closing_hours": "18:30"
        }
        
        response = client.patch(f"/api/v1/workshops/{sample_workshop.workshop_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        workshop = response.json()
        assert workshop["workshop_name"] == "Updated Auto Shop"
        assert workshop["address"] == "456 Updated St"
        assert workshop["opening_hours"] == "07:30"
        assert workshop["closing_hours"] == "18:30"
        
        # Verify changes in database
        async with db_session as session:
            result = await session.execute(
                select(models.Workshop).where(models.Workshop.workshop_id == sample_workshop.workshop_id)
            )
            db_workshop = result.scalar_one()
            assert db_workshop.workshop_name == "Updated Auto Shop"
            assert db_workshop.address == "456 Updated St"

    @pytest.mark.asyncio
    async def test_update_current_user_workshop_as_manager(self, client, manager_user_token, db_session):
        """Test manager user updating their own workshop"""
        headers = self.auth_headers(manager_user_token)
        update_data = {
            "workshop_name": "My Updated Workshop",
            "address": "New Manager Address"
        }
        
        response = client.patch("/api/v1/workshops/me", json=update_data, headers=headers)
        assert response.status_code == 200
        
        workshop = response.json()
        assert workshop["workshop_name"] == "My Updated Workshop"
        assert workshop["address"] == "New Manager Address"

    @pytest.mark.asyncio
    async def test_update_workshop_by_id_as_manager_forbidden(self, client, manager_user_token, sample_workshop):
        """Test manager user cannot update workshop by ID (admin required)"""
        headers = self.auth_headers(manager_user_token)
        update_data = {"workshop_name": "Forbidden Update"}
        
        response = client.patch(f"/api/v1/workshops/{sample_workshop.workshop_id}", json=update_data, headers=headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_workshop_partial_update(self, client, admin_user_token, sample_workshop):
        """Test updating only some fields of a workshop"""
        headers = self.auth_headers(admin_user_token)
        update_data = {
            "workshop_name": "Partially Updated Shop"
        }
        
        response = client.patch(f"/api/v1/workshops/{sample_workshop.workshop_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        workshop = response.json()
        assert workshop["workshop_name"] == "Partially Updated Shop"
        assert workshop["address"] == "123 Main St, City, State"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_workshop_not_found(self, client, admin_user_token):
        """Test updating a workshop that doesn't exist"""
        headers = self.auth_headers(admin_user_token)
        update_data = {"workshop_name": "Non-existent Shop"}
        
        response = client.patch("/api/v1/workshops/99999", json=update_data, headers=headers)
        assert response.status_code == 404

    # ================== DELETE WORKSHOP TESTS (ADMIN ONLY) ==================

    @pytest.mark.asyncio
    async def test_delete_workshop_as_admin(self, client, admin_user_token, sample_workshop, db_session):
        """Test admin user deleting a workshop"""
        headers = self.auth_headers(admin_user_token)
        workshop_id = sample_workshop.workshop_id
        
        response = client.delete(f"/api/v1/workshops/{workshop_id}", headers=headers)
        assert response.status_code == 200
        
        deleted_workshop = response.json()
        assert deleted_workshop["workshop_id"] == workshop_id
        assert deleted_workshop["workshop_name"] == "Sample Auto Shop"
        
        # Verify workshop was deleted from database
        async with db_session as session:
            result = await session.execute(
                select(models.Workshop).where(models.Workshop.workshop_id == workshop_id)
            )
            db_workshop = result.scalar_one_or_none()
            assert db_workshop is None

    @pytest.mark.asyncio
    async def test_delete_workshop_as_manager_forbidden(self, client, manager_user_token, sample_workshop):
        """Test manager user cannot delete workshop (admin required)"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.delete(f"/api/v1/workshops/{sample_workshop.workshop_id}", headers=headers)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_workshop_not_found(self, client, admin_user_token):
        """Test deleting a workshop that doesn't exist"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.delete("/api/v1/workshops/99999", headers=headers)
        assert response.status_code == 404

    # ================== WORKSHOP LOGO TESTS ==================

    @pytest.mark.asyncio
    async def test_upload_workshop_logo_as_manager(self, client, manager_user_token, tmpdir):
        """Test manager user uploading a logo for their workshop"""
        headers = self.auth_headers(manager_user_token)
        
        # Create a test image file
        image_data, filename = self.create_test_image_file()
        
        files = {"logo_file": (filename, image_data, "image/png")}
        
        response = client.post("/api/v1/workshops/logo", files=files, headers=headers)
        assert response.status_code == 200
        
        workshop = response.json()
        assert workshop["workshop_logo"] is not None
        assert "/logos/" in workshop["workshop_logo"]

    @pytest.mark.asyncio
    async def test_get_workshop_logo_as_manager(self, client, manager_user_token):
        """Test manager user getting their workshop logo"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.get("/api/v1/workshops/logo", headers=headers)
        assert response.status_code == 200
        
        logo_data = response.json()
        assert "workshop_id" in logo_data

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, client, manager_user_token):
        """Test uploading invalid file type as logo"""
        headers = self.auth_headers(manager_user_token)
        
        # Create a text file instead of image
        text_data = BytesIO(b"This is not an image")
        files = {"logo_file": ("test.txt", text_data, "text/plain")}
        
        response = client.post("/api/v1/workshops/logo", files=files, headers=headers)
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    # ================== WORKSHOP PARTS TESTS ==================

    @pytest.mark.asyncio
    async def test_create_workshop_part_as_manager(self, client, manager_user_token, sample_part, db_session):
        """Test manager user creating a part for their workshop"""
        headers = self.auth_headers(manager_user_token)
        part_data = {
            "part_id": sample_part.part_id,
            "quantity": 15,
            "purchase_price": 3000,  # $30.00
            "sale_price": 6000       # $60.00
        }
        
        response = client.post("/api/v1/workshops/parts", json=part_data, headers=headers)
        assert response.status_code == 200
        
        part_workshop = response.json()
        assert part_workshop["part_id"] == sample_part.part_id
        assert part_workshop["quantity"] == 15
        assert part_workshop["purchase_price"] == 3000
        assert part_workshop["sale_price"] == 6000

    @pytest.mark.asyncio
    async def test_get_workshop_parts_as_manager(self, client, manager_user_token, sample_part_workshop):
        """Test manager user getting parts for their workshop"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.get("/api/v1/workshops/parts", headers=headers)
        assert response.status_code == 200
        
        parts = response.json()
        assert isinstance(parts, list)
        assert len(parts) >= 1
        
        found_part = None
        for part in parts:
            if part["part_id"] == sample_part_workshop.part_id:
                found_part = part
                break
        
        assert found_part is not None
        assert found_part["quantity"] == 10
        assert found_part["purchase_price"] == 2500

    @pytest.mark.asyncio
    async def test_update_workshop_part_as_manager(self, client, manager_user_token, sample_part_workshop, db_session):
        """Test manager user updating a part in their workshop"""
        headers = self.auth_headers(manager_user_token)
        update_data = {
            "quantity": 20,
            "purchase_price": 2800,
            "sale_price": 5500
        }
        
        response = client.patch(f"/api/v1/workshops/parts/{sample_part_workshop.part_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        part_workshop = response.json()
        assert part_workshop["quantity"] == 20
        assert part_workshop["purchase_price"] == 2800
        assert part_workshop["sale_price"] == 5500

    @pytest.mark.asyncio
    async def test_delete_workshop_part_as_manager(self, client, manager_user_token, sample_part_workshop, db_session):
        """Test manager user deleting a part from their workshop"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.delete(f"/api/v1/workshops/parts/{sample_part_workshop.part_id}", headers=headers)
        assert response.status_code == 200
        
        # Verify part-workshop relationship was deleted
        async with db_session as session:
            result = await session.execute(
                select(models.PartWorkshop).where(
                    models.PartWorkshop.part_id == sample_part_workshop.part_id,
                    models.PartWorkshop.workshop_id == sample_part_workshop.workshop_id
                )
            )
            db_part_workshop = result.scalar_one_or_none()
            assert db_part_workshop is None

    # ================== EDGE CASES AND VALIDATION TESTS ==================

    @pytest.mark.asyncio
    async def test_create_workshop_with_empty_name(self, client, admin_user_token):
        """Test creating workshop with empty name"""
        headers = self.auth_headers(admin_user_token)
        workshop_data = {
            "workshop_name": "",
            "address": "Valid Address"
        }
        
        response = client.post("/api/v1/workshops/", json=workshop_data, headers=headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_workshop_with_very_long_fields(self, client, admin_user_token):
        """Test creating workshop with very long field values"""
        headers = self.auth_headers(admin_user_token)
        workshop_data = {
            "workshop_name": "Very Long Workshop Name" * 10,
            "address": "Very Long Address" * 20,
            "opening_hours": "Very Long Opening Hours" * 5,
            "closing_hours": "Very Long Closing Hours" * 5
        }
        
        response = client.post("/api/v1/workshops/", json=workshop_data, headers=headers)
        # Should handle appropriately (succeed or fail with validation)
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_update_workshop_with_none_values(self, client, admin_user_token, sample_workshop):
        """Test updating workshop with None values for optional fields"""
        headers = self.auth_headers(admin_user_token)
        update_data = {
            "address": None,
            "opening_hours": None,
            "closing_hours": None
        }
        
        response = client.patch(f"/api/v1/workshops/{sample_workshop.workshop_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        workshop = response.json()
        assert workshop["address"] is None
        assert workshop["opening_hours"] is None
        assert workshop["closing_hours"] is None

    @pytest.mark.asyncio
    async def test_workshop_case_sensitivity(self, client, admin_user_token, db_session):
        """Test workshop name case sensitivity"""
        headers = self.auth_headers(admin_user_token)
        
        # Create two workshops with different cases
        workshop_data_1 = {"workshop_name": "auto shop"}
        workshop_data_2 = {"workshop_name": "AUTO SHOP"}
        
        response1 = client.post("/api/v1/workshops/", json=workshop_data_1, headers=headers)
        response2 = client.post("/api/v1/workshops/", json=workshop_data_2, headers=headers)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        workshop1 = response1.json()
        workshop2 = response2.json()
        assert workshop1["workshop_id"] != workshop2["workshop_id"]
        assert workshop1["workshop_name"] == "auto shop"
        assert workshop2["workshop_name"] == "AUTO SHOP"

    @pytest.mark.asyncio
    async def test_workshop_parts_negative_values(self, client, manager_user_token, sample_part):
        """Test creating workshop part with negative values"""
        headers = self.auth_headers(manager_user_token)
        part_data = {
            "part_id": sample_part.part_id,
            "quantity": -5,
            "purchase_price": -1000,
            "sale_price": -2000
        }
        
        response = client.post("/api/v1/workshops/parts", json=part_data, headers=headers)
        # Should either succeed (business allows negative values) or fail with validation
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_manager_user_no_workshop_logo_operations(self, client, manager_user_no_workshop_token):
        """Test manager user without workshop cannot perform logo operations"""
        headers = self.auth_headers(manager_user_no_workshop_token)
        
        # Try to get logo
        response = client.get("/api/v1/workshops/logo", headers=headers)
        assert response.status_code == 400
        assert "no workshop" in response.json()["detail"]
        
        # Try to upload logo
        image_data, filename = self.create_test_image_file()
        files = {"logo_file": (filename, image_data, "image/png")}
        response = client.post("/api/v1/workshops/logo", files=files, headers=headers)
        assert response.status_code == 400
        assert "no workshop" in response.json()["detail"]

    @pytest.mark.asyncio 
    async def test_concurrent_workshop_creation(self, client, db_session):
        """Test concurrent workshop creation by different users"""
        from auth.auth import pwd_context
        
        # Create two users without workshops
        async with db_session as session:
            user1 = models.User(
                first_name="User1",
                last_name="Test",
                email="user1_concurrent@test.com",
                hashed_password=pwd_context.hash("testpass"),
                role=models.RoleEnum.manager,
                workshop_id=1
            )
            user2 = models.User(
                first_name="User2", 
                last_name="Test",
                email="user2_concurrent@test.com",
                hashed_password=pwd_context.hash("testpass"),
                role=models.RoleEnum.manager,
                workshop_id=1
            )
            session.add(user1)
            session.add(user2)
            await session.commit()
        
        # Login both users
        login_data1 = {"username": "user1_concurrent@test.com", "password": "testpass"}
        login_data2 = {"username": "user2_concurrent@test.com", "password": "testpass"}
        
        response1 = client.post("/api/v1/auth/login", data=login_data1)
        response2 = client.post("/api/v1/auth/login", data=login_data2)
        
        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]
        
        # Both create workshops concurrently
        workshop_data1 = {"workshop_name": "Concurrent Shop 1"}
        workshop_data2 = {"workshop_name": "Concurrent Shop 2"}
        
        headers1 = self.auth_headers(token1)
        headers2 = self.auth_headers(token2)
        
        response1 = client.post("/api/v1/workshops/", json=workshop_data1, headers=headers1)
        response2 = client.post("/api/v1/workshops/", json=workshop_data2, headers=headers2)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        workshop1 = response1.json()
        workshop2 = response2.json()
        assert workshop1["workshop_id"] != workshop2["workshop_id"]