import pytest
import pytest_asyncio
from db import models
from sqlalchemy import select
from jose import jwt
from auth import auth


class TestWorkersIntegration:
    """Integration tests for workers endpoints testing complete workflow from API to database"""
    
    @pytest_asyncio.fixture
    async def admin_user_token(self, client, db_session):
        """Create an admin user with their own workshop and return authentication token"""
        from auth.auth import pwd_context
        
        async with db_session as session:
            # Create a dedicated workshop for admin
            admin_workshop = models.Workshop(
                workshop_name="Admin CustomerCar Workshop",
                address="123 Admin St",
                opening_hours="09:00",
                closing_hours="18:00"
            )
            session.add(admin_workshop)
            await session.commit()
            await session.refresh(admin_workshop)
            
            # Create admin user with their workshop
            admin_user = models.User(
                first_name="Admin",
                last_name="User",
                email="admin_customercar@test.com",
                hashed_password=pwd_context.hash("AdminPass123%"),
                role="admin",
                workshop_id=admin_workshop.workshop_id
            )
            session.add(admin_user)
            await session.commit()
        
        # Login to get token
        login_data = {
            "username": "admin_customercar@test.com",
            "password": "AdminPass123%"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest_asyncio.fixture
    async def manager_user_token(self, client, db_session):
        """Create a manager user with their own workshop and return authentication token"""
        from auth.auth import pwd_context
        
        async with db_session as session:
            # Create a dedicated workshop for manager
            manager_workshop = models.Workshop(
                workshop_name="Manager CustomerCar Workshop",
                address="456 Manager Ave",
                opening_hours="08:00",
                closing_hours="17:00"
            )
            session.add(manager_workshop)
            await session.commit()
            await session.refresh(manager_workshop)
            
            # Create manager user with their workshop
            manager_user = models.User(
                first_name="Manager",
                last_name="User",
                email="manager_customercar@test.com",
                hashed_password=pwd_context.hash("ManagerPass123%"),
                role=models.RoleEnum.manager,
                workshop_id=manager_workshop.workshop_id
            )
            session.add(manager_user)
            await session.commit()
        
        # Login to get token
        login_data = {
            "username": "manager_customercar@test.com",
            "password": "ManagerPass123%"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest_asyncio.fixture
    async def second_workshop(self, db_session):
        """Create a second workshop for testing cross-workshop access"""
        async with db_session as session:
            workshop = models.Workshop(
                workshop_name="Second Workshop",
                address="456 Second St",
                opening_hours="08:00",
                closing_hours="17:00"
            )
            session.add(workshop)
            await session.commit()
            await session.refresh(workshop)
            return workshop.workshop_id

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

    async def get_user_workshop_id_from_token(self, token, db_session):
        """Helper method to get workshop_id from JWT token"""
        # Decode the token
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        user_id = payload.get("user_id")
        
        # Query database for user's workshop_id
        async with db_session as session:
            result = await session.execute(
                select(models.User).where(models.User.user_id == user_id)
            )
            user = result.scalar_one()
            return user.workshop_id

    @pytest_asyncio.fixture
    async def sample_worker_for_admin(self, admin_user_token, db_session):
        """Create a sample worker for admin's workshop"""
        async with db_session as session:
            # Get the workshop_id from admin token
            workshop_id = await self.get_user_workshop_id_from_token(admin_user_token, db_session)
            
            worker = models.Worker(
                first_name="John",
                last_name="Smith",
                phone="555-1234",
                position="Mechanic",
                nickname="Johnny",
                workshop_id=workshop_id
            )
            session.add(worker)
            await session.commit()
            await session.refresh(worker)
            return worker

    @pytest_asyncio.fixture
    async def sample_worker_for_manager(self, manager_user_token, db_session):
        """Create a sample worker for manager's workshop"""
        async with db_session as session:
            # Get the workshop_id from manager token
            workshop_id = await self.get_user_workshop_id_from_token(manager_user_token, db_session)
            
            worker = models.Worker(
                first_name="John",
                last_name="Smith",
                phone="555-1234",
                position="Mechanic",
                nickname="Johnny",
                workshop_id=workshop_id
            )
            session.add(worker)
            await session.commit()
            await session.refresh(worker)
            return worker

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

    # ================== CREATE WORKER TESTS ==================

    @pytest.mark.asyncio
    async def test_create_worker_as_admin(self, client, admin_user_token, db_session):
        """Test admin user creating a worker"""
        headers = self.auth_headers(admin_user_token)
        worker_data = {
            "first_name": "Alice",
            "last_name": "Johnson",
            "phone": "555-5678",
            "position": "Electrician",
            "nickname": "Sparky"
        }
        
        response = client.post("/api/v1/workers/", json=worker_data, headers=headers)
        assert response.status_code == 200
        
        worker = response.json()
        assert worker["first_name"] == "Alice"
        assert worker["last_name"] == "Johnson"
        assert worker["phone"] == "555-5678"
        assert worker["position"] == "Electrician"
        assert worker["nickname"] == "Sparky"
        assert "worker_id" in worker
        assert "created_at" in worker
        assert "updated_at" in worker
        assert "workshop_id" in worker
        
        # Verify worker was saved to database
        async with db_session as session:
            result = await session.execute(
                select(models.Worker).where(
                    models.Worker.first_name == "Alice",
                    models.Worker.last_name == "Johnson"
                )
            )
            db_worker = result.scalar_one_or_none()
            assert db_worker is not None
            assert db_worker.phone == "555-5678"
            assert db_worker.position == "Electrician"
            assert db_worker.nickname == "Sparky"

    @pytest.mark.asyncio
    async def test_create_worker_as_manager(self, client, manager_user_token, db_session):
        """Test manager user creating a worker for their own workshop"""
        headers = self.auth_headers(manager_user_token)
        worker_data = {
            "first_name": "Bob",
            "last_name": "Wilson",
            "phone": "555-9876",
            "position": "Painter",
            "nickname": "Painter Bob"
        }
        
        response = client.post("/api/v1/workers/", json=worker_data, headers=headers)
        assert response.status_code == 200
        
        worker = response.json()
        assert worker["first_name"] == "Bob"
        assert worker["last_name"] == "Wilson"
        assert worker["position"] == "Painter"
        
        # Verify worker was assigned to manager's workshop
        workshop_id = await self.get_user_workshop_id_from_token(manager_user_token, db_session)
        assert worker["workshop_id"] == workshop_id
        
        # Verify in database
        async with db_session as session:
            result = await session.execute(
                select(models.Worker).where(
                    models.Worker.first_name == "Bob",
                    models.Worker.last_name == "Wilson"
                )
            )
            db_worker = result.scalar_one_or_none()
            assert db_worker is not None
            assert db_worker.workshop_id == workshop_id

    @pytest.mark.asyncio
    async def test_create_worker_with_optional_fields(self, client, admin_user_token, db_session):
        """Test creating worker with minimal required fields"""
        headers = self.auth_headers(admin_user_token)
        worker_data = {
            "first_name": "Charlie",
            "last_name": "Brown",
            "position": "Apprentice"
            # phone and nickname are optional
        }
        
        response = client.post("/api/v1/workers/", json=worker_data, headers=headers)
        assert response.status_code == 200
        
        worker = response.json()
        assert worker["first_name"] == "Charlie"
        assert worker["last_name"] == "Brown"
        assert worker["position"] == "Apprentice"
        assert worker["phone"] is None
        assert worker["nickname"] is None

    @pytest.mark.asyncio
    async def test_create_worker_unauthenticated(self, client):
        """Test creating worker without authentication fails"""
        worker_data = {
            "first_name": "David",
            "last_name": "Miller",
            "position": "Technician"
        }
        
        response = client.post("/api/v1/workers/", json=worker_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_worker_missing_required_fields(self, client, admin_user_token):
        """Test creating worker with missing required fields"""
        headers = self.auth_headers(admin_user_token)
        worker_data = {
            "first_name": "Emma"
            # Missing last_name and position
        }
        
        response = client.post("/api/v1/workers/", json=worker_data, headers=headers)
        assert response.status_code == 422

    # ================== READ WORKERS TESTS ==================

    @pytest.mark.asyncio
    async def test_get_all_workers_as_admin(self, client, admin_user_token, sample_worker_for_admin):
        """Test admin user getting all workers from their workshop"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.get("/api/v1/workers/", headers=headers)
        assert response.status_code == 200
        
        workers = response.json()
        assert isinstance(workers, list)
        assert len(workers) >= 1
        
        # Find our sample worker
        found_worker = None
        for worker in workers:
            if worker["worker_id"] == sample_worker_for_admin.worker_id:
                found_worker = worker
                break
        
        assert found_worker is not None
        assert found_worker["first_name"] == "John"
        assert found_worker["last_name"] == "Smith"
        assert found_worker["position"] == "Mechanic"

    @pytest.mark.asyncio
    async def test_get_all_workers_as_manager(self, client, manager_user_token, sample_worker_for_manager):
        """Test manager user getting all workers from their workshop"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.get("/api/v1/workers/", headers=headers)
        assert response.status_code == 200
        
        workers = response.json()
        assert isinstance(workers, list)
        
        # Manager should only see workers from their workshop
        for worker in workers:
            assert worker["workshop_id"] == sample_worker_for_manager.workshop_id

    @pytest.mark.asyncio
    async def test_get_all_workers_with_pagination(self, client, admin_user_token, sample_worker_for_admin):
        """Test getting workers with pagination parameters"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.get("/api/v1/workers/?skip=0&limit=10", headers=headers)
        assert response.status_code == 200
        
        workers = response.json()
        assert isinstance(workers, list)
        assert len(workers) <= 10

    @pytest.mark.asyncio
    async def test_get_workers_unauthenticated(self, client):
        """Test getting workers without authentication fails"""
        response = client.get("/api/v1/workers/")
        assert response.status_code == 401

    # ================== READ WORKER BY ID TESTS ==================

    @pytest.mark.asyncio
    async def test_get_worker_by_id_as_admin(self, client, admin_user_token, sample_worker_for_admin):
        """Test admin user getting a specific worker by ID"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.get(f"/api/v1/workers/{sample_worker_for_admin.worker_id}", headers=headers)
        assert response.status_code == 200
        
        worker = response.json()
        assert worker["worker_id"] == sample_worker_for_admin.worker_id
        assert worker["first_name"] == "John"
        assert worker["last_name"] == "Smith"
        assert worker["position"] == "Mechanic"
        assert worker["nickname"] == "Johnny"

    @pytest.mark.asyncio
    async def test_get_worker_by_id_as_manager(self, client, manager_user_token, sample_worker_for_manager):
        """Test manager user getting a worker from their workshop"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.get(f"/api/v1/workers/{sample_worker_for_manager.worker_id}", headers=headers)
        assert response.status_code == 200
        
        worker = response.json()
        assert worker["worker_id"] == sample_worker_for_manager.worker_id
    @pytest.mark.asyncio
    async def test_get_worker_by_id_not_found(self, client, admin_user_token):
        """Test getting a worker that doesn't exist"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.get("/api/v1/workers/99999", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_worker_by_id_unauthenticated(self, client, sample_worker_for_manager):
        """Test getting worker by ID without authentication fails"""
        response = client.get(f"/api/v1/workers/{sample_worker_for_manager.worker_id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_worker_from_different_workshop(self, client, manager_user_token, db_session, second_workshop):
        """Test that manager cannot access workers from different workshop"""
        headers = self.auth_headers(manager_user_token)
        
        # Create worker in different workshop
        async with db_session as session:
            other_worker = models.Worker(
                first_name="Other",
                last_name="Worker",
                position="Technician",
                workshop_id=second_workshop
            )
            session.add(other_worker)
            await session.commit()
            await session.refresh(other_worker)
            
            response = client.get(f"/api/v1/workers/{other_worker.worker_id}", headers=headers)
            assert response.status_code == 404

    # ================== UPDATE WORKER TESTS ==================

    @pytest.mark.asyncio
    async def test_update_worker_as_admin(self, client, admin_user_token, sample_worker_for_admin, db_session):
        """Test admin user updating a worker"""
        headers = self.auth_headers(admin_user_token)
        update_data = {
            "first_name": "Johnny",
            "position": "Senior Mechanic",
            "phone": "555-0000"
        }
        
        response = client.patch(f"/api/v1/workers/{sample_worker_for_admin.worker_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        worker = response.json()
        assert worker["first_name"] == "Johnny"
        assert worker["position"] == "Senior Mechanic"
        assert worker["phone"] == "555-0000"
        assert worker["last_name"] == "Smith"  # Unchanged
        assert worker["nickname"] == "Johnny"  # Unchanged
        
        # Verify changes in database
        async with db_session as session:
            result = await session.execute(
                select(models.Worker).where(models.Worker.worker_id == sample_worker_for_admin.worker_id)
            )
            db_worker = result.scalar_one()
            assert db_worker.first_name == "Johnny"
            assert db_worker.position == "Senior Mechanic"
            assert db_worker.phone == "555-0000"

    @pytest.mark.asyncio
    async def test_update_worker_as_manager(self, client, manager_user_token, sample_worker_for_manager, db_session):
        """Test manager user updating a worker in their workshop"""
        headers = self.auth_headers(manager_user_token)
        update_data = {
            "nickname": "Super Johnny",
            "position": "Lead Mechanic"
        }
        
        response = client.patch(f"/api/v1/workers/{sample_worker_for_manager.worker_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        worker = response.json()
        assert worker["nickname"] == "Super Johnny"
        assert worker["position"] == "Lead Mechanic"
        
        # Verify changes in database
        async with db_session as session:
            result = await session.execute(
                select(models.Worker).where(models.Worker.worker_id == sample_worker_for_manager.worker_id)
            )
            db_worker = result.scalar_one()
            assert db_worker.nickname == "Super Johnny"
            assert db_worker.position == "Lead Mechanic"

    @pytest.mark.asyncio
    async def test_update_worker_partial_update(self, client, admin_user_token, sample_worker_for_admin):
        """Test updating only some fields of a worker"""
        headers = self.auth_headers(admin_user_token)
        update_data = {
            "phone": "555-9999"
        }
        
        response = client.patch(f"/api/v1/workers/{sample_worker_for_admin.worker_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        worker = response.json()
        assert worker["phone"] == "555-9999"
        assert worker["first_name"] == "John"  # Unchanged
        assert worker["last_name"] == "Smith"  # Unchanged
        assert worker["position"] == "Mechanic"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_worker_not_found(self, client, admin_user_token):
        """Test updating a worker that doesn't exist"""
        headers = self.auth_headers(admin_user_token)
        update_data = {"position": "New Position"}
        
        response = client.patch("/api/v1/workers/99999", json=update_data, headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_worker_unauthenticated(self, client, sample_worker_for_manager):
        """Test updating worker without authentication fails"""
        update_data = {"position": "New Position"}
        
        response = client.patch(f"/api/v1/workers/{sample_worker_for_manager.worker_id}", json=update_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_worker_from_different_workshop(self, client, manager_user_token, db_session, second_workshop):
        """Test that manager cannot update workers from different workshop"""
        headers = self.auth_headers(manager_user_token)
        
        # Create worker in different workshop
        async with db_session as session:
            other_worker = models.Worker(
                first_name="Other",
                last_name="Worker",
                position="Technician",
                workshop_id=second_workshop
            )
            session.add(other_worker)
            await session.commit()
            await session.refresh(other_worker)
            
            update_data = {"position": "New Position"}
            response = client.patch(f"/api/v1/workers/{other_worker.worker_id}", json=update_data, headers=headers)
            assert response.status_code == 404

    # ================== DELETE WORKER TESTS ==================

    @pytest.mark.asyncio
    async def test_delete_worker_as_admin(self, client, admin_user_token, sample_worker_for_admin, db_session):
        """Test admin user deleting a worker"""
        headers = self.auth_headers(admin_user_token)
        worker_id = sample_worker_for_admin.worker_id
        
        response = client.delete(f"/api/v1/workers/{worker_id}", headers=headers)
        assert response.status_code == 200
        
        deleted_worker = response.json()
        assert deleted_worker["worker_id"] == worker_id
        assert deleted_worker["first_name"] == "John"
        assert deleted_worker["last_name"] == "Smith"
        
        # Verify worker was deleted from database
        async with db_session as session:
            result = await session.execute(
                select(models.Worker).where(models.Worker.worker_id == worker_id)
            )
            db_worker = result.scalar_one_or_none()
            assert db_worker is None

    @pytest.mark.asyncio
    async def test_delete_worker_as_manager(self, client, manager_user_token, sample_worker_for_manager, db_session):
        """Test manager user deleting a worker from their workshop"""
        headers = self.auth_headers(manager_user_token)
        worker_id = sample_worker_for_manager.worker_id
        
        response = client.delete(f"/api/v1/workers/{worker_id}", headers=headers)
        assert response.status_code == 200
        
        # Verify worker was deleted from database
        async with db_session as session:
            result = await session.execute(
                select(models.Worker).where(models.Worker.worker_id == worker_id)
            )
            db_worker = result.scalar_one_or_none()
            assert db_worker is None

    @pytest.mark.asyncio
    async def test_delete_worker_not_found(self, client, admin_user_token):
        """Test deleting a worker that doesn't exist"""
        headers = self.auth_headers(admin_user_token)
        
        response = client.delete("/api/v1/workers/99999", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_worker_unauthenticated(self, client, sample_worker_for_manager):
        """Test deleting worker without authentication fails"""
        response = client.delete(f"/api/v1/workers/{sample_worker_for_manager.worker_id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_worker_from_different_workshop(self, client, manager_user_token, db_session, second_workshop):
        """Test that manager cannot delete workers from different workshop"""
        headers = self.auth_headers(manager_user_token)
        
        # Create worker in different workshop
        async with db_session as session:
            other_worker = models.Worker(
                first_name="Other",
                last_name="Worker",
                position="Technician",
                workshop_id=second_workshop
            )
            session.add(other_worker)
            await session.commit()
            await session.refresh(other_worker)
            
            response = client.delete(f"/api/v1/workers/{other_worker.worker_id}", headers=headers)
            assert response.status_code == 404

    # ================== EDGE CASES AND VALIDATION TESTS ==================

    @pytest.mark.asyncio
    async def test_create_worker_with_empty_strings(self, client, admin_user_token):
        """Test creating worker with empty string fields"""
        headers = self.auth_headers(admin_user_token)
        worker_data = {
            "first_name": "",
            "last_name": "",
            "position": ""
        }
        
        response = client.post("/api/v1/workers/", json=worker_data, headers=headers)
        # Should fail validation for empty required strings
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_worker_with_empty_fields(self, client, admin_user_token, sample_worker_for_admin):
        """Test updating worker with None values to clear optional fields"""
        headers = self.auth_headers(admin_user_token)
        update_data = {
            "phone": None,
            "nickname": None
        }
        
        response = client.patch(f"/api/v1/workers/{sample_worker_for_admin.worker_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        worker = response.json()
        assert worker["phone"] is None
        assert worker["nickname"] is None
        assert worker["first_name"] == "John"  # Required field unchanged

    @pytest.mark.asyncio
    async def test_worker_timestamps_behavior(self, client, admin_user_token, db_session):
        """Test that worker timestamps are properly set and updated"""
        headers = self.auth_headers(admin_user_token)
        worker_data = {
            "first_name": "Timestamp",
            "last_name": "Test",
            "position": "Tester"
        }
        
        # Create worker
        response = client.post("/api/v1/workers/", json=worker_data, headers=headers)
        assert response.status_code == 200
        
        created_worker = response.json()
        worker_id = created_worker["worker_id"]
        created_at = created_worker["created_at"]
        updated_at = created_worker["updated_at"]
        
        assert created_at is not None
        assert updated_at is not None
        
        # Update worker
        import time
        time.sleep(1)  # Ensure different timestamp
        
        update_data = {"position": "Updated Tester"}
        response = client.patch(f"/api/v1/workers/{worker_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        updated_worker = response.json()
        assert updated_worker["created_at"] == created_at  # Should not change
        assert updated_worker["updated_at"] != updated_at  # Should change
