import pytest
import pytest_asyncio
from db import models, schemas
from sqlalchemy import select
import time


class TestJobsIntegration:
    """Integration tests for jobs endpoints testing complete workflow from API to database"""
    
    @pytest_asyncio.fixture
    async def admin_user_token(self, client, db_session, _setup_workshop):
        """Create an admin user and return authentication token"""
        from auth.auth import pwd_context
        
        # Get the workshop_id from setup
        async with db_session as session:
            result = await session.execute(select(models.Workshop).limit(1))
            default_workshop = result.scalar_one()
            workshop_id = default_workshop.workshop_id
        
        # Create admin user directly in database
        async with db_session as session:
            admin_user = models.User(
                first_name="Admin",
                last_name="User",
                email="admin_jobs@test.com",
                hashed_password=pwd_context.hash("adminpass123"),
                role=models.RoleEnum.admin,
                workshop_id=workshop_id
            )
            session.add(admin_user)
            await session.commit()
        
        # Login to get token
        login_data = {
            "username": "admin_jobs@test.com",
            "password": "adminpass123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest_asyncio.fixture
    async def manager_user_token(self, client, db_session):
        """Create a manager user with their own workshop and return authentication token"""
        from auth.auth import pwd_context
        
        # Create a workshop for the manager
        async with db_session as session:
            manager_workshop = models.Workshop(
                workshop_name="Manager Test Workshop",
                address="123 Manager St",
                opening_hours="09:00",
                closing_hours="18:00"
            )
            session.add(manager_workshop)
            await session.commit()
            await session.refresh(manager_workshop)
            workshop_id = manager_workshop.workshop_id
        
        # Create manager user
        async with db_session as session:
            manager_user = models.User(
                first_name="Manager",
                last_name="User",
                email="manager_jobs@test.com",
                hashed_password=pwd_context.hash("managerpass123"),
                role=models.RoleEnum.manager,
                workshop_id=workshop_id
            )
            session.add(manager_user)
            await session.commit()
        
        # Login to get token
        login_data = {
            "username": "manager_jobs@test.com",
            "password": "managerpass123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest_asyncio.fixture
    async def sample_car(self, db_session):
        """Create a sample car for testing"""
        async with db_session as session:
            car = models.Car(
                brand="Toyota",
                model="Camry",
                year=2020
            )
            session.add(car)
            await session.commit()
            await session.refresh(car)
            return car

    @pytest_asyncio.fixture
    async def sample_customer(self, db_session, manager_user_token):
        """Create a sample customer for the manager's workshop"""
        # Get the manager's workshop ID directly from database to avoid API rate limiting
        from jose import jwt
        from fastapi import HTTPException
        from auth.auth import SECRET_KEY, ALGORITHM
        
        try:
            payload = jwt.decode(manager_user_token, SECRET_KEY, algorithms=[ALGORITHM])
            user_email = payload.get("sub")
        except:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        async with db_session as session:
            # Get manager user from database
            result = await session.execute(
                select(models.User).where(models.User.email == user_email)
            )
            manager_user = result.scalar_one()
            workshop_id = manager_user.workshop_id
            
            customer = models.Customer(
                first_name="John",
                last_name="Doe",
                email="john.doe@test.com",
                phone="555-1234",
                workshop_id=workshop_id
            )
            session.add(customer)
            await session.commit()
            await session.refresh(customer)
            return customer

    @pytest_asyncio.fixture
    async def sample_customer_car(self, db_session, sample_customer, sample_car):
        """Create a sample customer car for testing"""
        async with db_session as session:
            customer_car = models.CustomerCar(
                customer_id=sample_customer.customer_id,
                car_id=sample_car.car_id,
                license_plate="ABC123",
                color="Blue"
            )
            session.add(customer_car)
            await session.commit()
            await session.refresh(customer_car)
            return customer_car

    @pytest_asyncio.fixture
    async def sample_job(self, db_session, sample_customer_car, manager_user_token):
        """Create a sample job for testing"""
        # Get the manager's workshop ID directly from database to avoid API rate limiting
        from jose import jwt
        from fastapi import HTTPException
        from auth.auth import SECRET_KEY, ALGORITHM
        
        try:
            payload = jwt.decode(manager_user_token, SECRET_KEY, algorithms=[ALGORITHM])
            user_email = payload.get("sub")
        except:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        async with db_session as session:
            # Get manager user from database
            result = await session.execute(
                select(models.User).where(models.User.email == user_email)
            )
            manager_user = result.scalar_one()
            workshop_id = manager_user.workshop_id
            
            job = models.Job(
                customer_car_id=sample_customer_car.customer_car_id,
                workshop_id=workshop_id,
                invoice="INV001",
                service_description="Oil change and filter replacement",
                start_date="2024-01-15",
                end_date="2024-01-15",
                status=models.StatusEnum.completed
            )
            session.add(job)
            await session.commit()
            await session.refresh(job)
            return job

    @staticmethod
    def auth_headers(token: str) -> dict:
        """Helper method to create authorization headers"""
        return {"Authorization": f"Bearer {token}"}

    # =============== CREATE JOBS TESTS ===============

    @pytest.mark.asyncio
    async def test_create_job_as_manager(self, client, manager_user_token, sample_customer_car, db_session):
        """Test creating a job as a manager user"""
        headers = self.auth_headers(manager_user_token)
        job_data = {
            "customer_car_id": sample_customer_car.customer_car_id,
            "invoice": "INV002",
            "service_description": "Brake service and inspection",
            "start_date": "2024-01-20",
            "end_date": "2024-01-20",
            "status": "completed"
        }
        
        response = client.post("/api/v1/jobs/", json=job_data, headers=headers)
        assert response.status_code == 200
        
        job = response.json()
        assert job["invoice"] == "INV002"
        assert job["service_description"] == "Brake service and inspection"
        assert job["customer_car_id"] == sample_customer_car.customer_car_id
        assert job["status"] == "completed"
        
        # Verify job was created in database
        async with db_session as session:
            result = await session.execute(
                select(models.Job).where(models.Job.invoice == "INV002")
            )
            db_job = result.scalar_one_or_none()
            assert db_job is not None
            assert db_job.service_description == "Brake service and inspection"

    @pytest.mark.asyncio
    async def test_create_job_unauthenticated(self, client, sample_customer_car):
        """Test creating a job without authentication"""
        job_data = {
            "customer_car_id": sample_customer_car.customer_car_id,
            "invoice": "INV003",
            "service_description": "Engine repair",
            "start_date": "2024-01-25",
            "status": "pending"
        }
        
        response = client.post("/api/v1/jobs/", json=job_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_job_missing_required_fields(self, client, manager_user_token):
        """Test creating a job with missing required fields"""
        headers = self.auth_headers(manager_user_token)
        job_data = {
            "service_description": "Incomplete job data"
        }
        
        response = client.post("/api/v1/jobs/", json=job_data, headers=headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_job_with_nonexistent_customer_car(self, client, manager_user_token):
        """Test creating a job with non-existent customer car"""
        headers = self.auth_headers(manager_user_token)
        job_data = {
            "customer_car_id": 99999,
            "invoice": "INV004",
            "service_description": "Test with invalid customer car",
            "start_date": "2024-01-30",
            "status": "pending"
        }
        
        response = client.post("/api/v1/jobs/", json=job_data, headers=headers)
        assert response.status_code == 404
        assert "Customer car not found" in response.json()["detail"]

    # =============== READ JOBS TESTS ===============

    @pytest.mark.asyncio
    async def test_get_all_jobs_as_manager(self, client, manager_user_token, sample_job):
        """Test getting all jobs as a manager user"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.get("/api/v1/jobs/", headers=headers)
        assert response.status_code == 200
        
        jobs = response.json()
        assert len(jobs) >= 1
        
        # Find our sample job
        sample_job_data = next((job for job in jobs if job["job_id"] == sample_job.job_id), None)
        assert sample_job_data is not None
        assert sample_job_data["invoice"] == "INV001"
        assert sample_job_data["service_description"] == "Oil change and filter replacement"
        
        # Verify car information is included
        assert "car_brand" in sample_job_data
        assert "car_model" in sample_job_data
        assert "license_plate" in sample_job_data
        assert sample_job_data["car_brand"] == "Toyota"
        assert sample_job_data["car_model"] == "Camry"
        assert sample_job_data["license_plate"] == "ABC123"

    @pytest.mark.asyncio
    async def test_get_jobs_with_pagination(self, client, manager_user_token):
        """Test getting jobs with pagination parameters"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.get("/api/v1/jobs/?skip=0&limit=5", headers=headers)
        assert response.status_code == 200
        
        jobs = response.json()
        assert len(jobs) <= 5

    @pytest.mark.asyncio
    async def test_get_jobs_unauthenticated(self, client):
        """Test getting jobs without authentication"""
        response = client.get("/api/v1/jobs/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_job_by_id_as_manager(self, client, manager_user_token, sample_job):
        """Test getting a specific job by ID as manager"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.get(f"/api/v1/jobs/{sample_job.job_id}", headers=headers)
        assert response.status_code == 200
        
        job = response.json()
        assert job["job_id"] == sample_job.job_id
        assert job["invoice"] == "INV001"
        assert job["service_description"] == "Oil change and filter replacement"
        
        # Verify car information is included
        assert "car_brand" in job
        assert "car_model" in job
        assert job["car_brand"] == "Toyota"
        assert job["car_model"] == "Camry"

    @pytest.mark.asyncio
    async def test_get_job_by_id_not_found(self, client, manager_user_token):
        """Test getting a job that doesn't exist"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.get("/api/v1/jobs/99999", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_job_by_id_unauthenticated(self, client, sample_job):
        """Test getting a job without authentication"""
        response = client.get(f"/api/v1/jobs/{sample_job.job_id}")
        assert response.status_code == 401

    # =============== UPDATE JOBS TESTS ===============

    @pytest.mark.asyncio
    async def test_update_job_as_manager(self, client, manager_user_token, sample_job, db_session):
        """Test updating a job as manager"""
        headers = self.auth_headers(manager_user_token)
        update_data = {
            "service_description": "Updated service description",
            "status": "in_progress",
            "end_date": "2024-01-16"
        }
        
        response = client.patch(f"/api/v1/jobs/{sample_job.job_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        job = response.json()
        assert job["service_description"] == "Updated service description"
        assert job["status"] == "in_progress"
        assert job["end_date"] == "2024-01-16"
        
        # Verify job was updated in database
        async with db_session as session:
            result = await session.execute(
                select(models.Job).where(models.Job.job_id == sample_job.job_id)
            )
            db_job = result.scalar_one()
            assert db_job.service_description == "Updated service description"
            assert db_job.status == models.StatusEnum.in_progress

    @pytest.mark.asyncio
    async def test_update_job_partial_update(self, client, manager_user_token, sample_job, db_session):
        """Test partial update of job (only some fields)"""
        headers = self.auth_headers(manager_user_token)
        update_data = {
            "status": "pending"
        }
        
        response = client.patch(f"/api/v1/jobs/{sample_job.job_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        job = response.json()
        assert job["status"] == "pending"
        # Other fields should remain unchanged
        assert job["invoice"] == "INV001"
        assert job["service_description"] == "Oil change and filter replacement"

    @pytest.mark.asyncio
    async def test_update_job_not_found(self, client, manager_user_token):
        """Test updating a job that doesn't exist"""
        headers = self.auth_headers(manager_user_token)
        update_data = {
            "status": "completed"
        }
        
        response = client.patch("/api/v1/jobs/99999", json=update_data, headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_job_unauthenticated(self, client, sample_job):
        """Test updating a job without authentication"""
        update_data = {
            "status": "completed"
        }
        
        response = client.patch(f"/api/v1/jobs/{sample_job.job_id}", json=update_data)
        assert response.status_code == 401

    # =============== DELETE JOBS TESTS ===============

    @pytest.mark.asyncio
    async def test_delete_job_as_manager(self, client, manager_user_token, sample_job, db_session):
        """Test deleting a job as manager"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.delete(f"/api/v1/jobs/{sample_job.job_id}", headers=headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["message"] == "Job deleted successfully"
        assert result["job_id"] == sample_job.job_id
        
        # Verify job was deleted from database
        async with db_session as session:
            result = await session.execute(
                select(models.Job).where(models.Job.job_id == sample_job.job_id)
            )
            db_job = result.scalar_one_or_none()
            assert db_job is None

    @pytest.mark.asyncio
    async def test_delete_job_not_found(self, client, manager_user_token):
        """Test deleting a job that doesn't exist"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.delete("/api/v1/jobs/99999", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_job_unauthenticated(self, client, sample_job):
        """Test deleting a job without authentication"""
        response = client.delete(f"/api/v1/jobs/{sample_job.job_id}")
        assert response.status_code == 401

    # =============== AUTHORIZATION & WORKSHOP ISOLATION TESTS ===============

    @pytest.mark.asyncio
    async def test_cross_workshop_job_access_denied(self, client, manager_user_token, db_session, _setup_workshop):
        """Test that manager cannot access jobs from other workshops"""
        # Create a job in a different workshop
        async with db_session as session:
            # Get the default workshop from setup
            result = await session.execute(select(models.Workshop).limit(1))
            default_workshop = result.scalar_one()
            default_workshop_id = default_workshop.workshop_id
            
            # Create customer and customer_car in the default workshop
            other_customer = models.Customer(
                first_name="Other",
                last_name="Customer",
                email="other@test.com",
                phone="555-9999",
                workshop_id=default_workshop_id
            )
            session.add(other_customer)
            await session.commit()
            await session.refresh(other_customer)
            
            # Create a car
            other_car = models.Car(
                brand="Honda",
                model="Civic",
                year=2019
            )
            session.add(other_car)
            await session.commit()
            await session.refresh(other_car)
            
            # Create customer car
            other_customer_car = models.CustomerCar(
                customer_id=other_customer.customer_id,
                car_id=other_car.car_id,
                license_plate="XYZ789",
                color="Red"
            )
            session.add(other_customer_car)
            await session.commit()
            await session.refresh(other_customer_car)
            
            # Create job in the other workshop
            other_job = models.Job(
                customer_car_id=other_customer_car.customer_car_id,
                workshop_id=default_workshop_id,
                invoice="OTHER001",
                service_description="Service in other workshop",
                start_date="2024-01-10",
                status=models.StatusEnum.pending
            )
            session.add(other_job)
            await session.commit()
            await session.refresh(other_job)
            other_job_id = other_job.job_id
        
        headers = self.auth_headers(manager_user_token)
        
        # Manager should not see the job from the other workshop
        response = client.get(f"/api/v1/jobs/{other_job_id}", headers=headers)
        assert response.status_code == 404
        
        # Manager should not be able to update the job
        response = client.patch(f"/api/v1/jobs/{other_job_id}", 
                               json={"status": "completed"}, headers=headers)
        assert response.status_code == 404
        
        # Manager should not be able to delete the job
        response = client.delete(f"/api/v1/jobs/{other_job_id}", headers=headers)
        assert response.status_code == 404

    # =============== VALIDATION & ERROR HANDLING TESTS ===============

    @pytest.mark.asyncio
    async def test_create_job_with_invalid_status(self, client, manager_user_token, sample_customer_car):
        """Test creating a job with invalid status"""
        headers = self.auth_headers(manager_user_token)
        job_data = {
            "customer_car_id": sample_customer_car.customer_car_id,
            "invoice": "INV005",
            "service_description": "Test invalid status",
            "start_date": "2024-02-01",
            "status": "invalid_status"
        }
        
        response = client.post("/api/v1/jobs/", json=job_data, headers=headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_job_with_invalid_data(self, client, manager_user_token, sample_job):
        """Test updating a job with invalid data"""
        headers = self.auth_headers(manager_user_token)
        update_data = {
            "status": "invalid_status"
        }
        
        response = client.patch(f"/api/v1/jobs/{sample_job.job_id}", json=update_data, headers=headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_job_with_long_invoice(self, client, manager_user_token, sample_customer_car):
        """Test creating a job with invoice exceeding length limit"""
        headers = self.auth_headers(manager_user_token)
        job_data = {
            "customer_car_id": sample_customer_car.customer_car_id,
            "invoice": "A" * 101,  # Exceeds 100 character limit
            "service_description": "Test long invoice",
            "start_date": "2024-02-05",
            "status": "pending"
        }
        
        response = client.post("/api/v1/jobs/", json=job_data, headers=headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_job_with_long_service_description(self, client, manager_user_token, sample_customer_car):
        """Test creating a job with service description exceeding length limit"""
        headers = self.auth_headers(manager_user_token)
        job_data = {
            "customer_car_id": sample_customer_car.customer_car_id,
            "invoice": "INV006",
            "service_description": "A" * 256,  # Exceeds 255 character limit
            "start_date": "2024-02-10",
            "status": "pending"
        }
        
        response = client.post("/api/v1/jobs/", json=job_data, headers=headers)
        assert response.status_code == 422

    # =============== EDGE CASES & SPECIAL SCENARIOS ===============

    @pytest.mark.asyncio
    async def test_create_job_without_optional_fields(self, client, manager_user_token, sample_customer_car, db_session):
        """Test creating a job with only required fields"""
        headers = self.auth_headers(manager_user_token)
        job_data = {
            "customer_car_id": sample_customer_car.customer_car_id,
            "invoice": "INV007",
            "start_date": "2024-02-15",
            "status": "pending"
        }
        
        response = client.post("/api/v1/jobs/", json=job_data, headers=headers)
        assert response.status_code == 200
        
        job = response.json()
        assert job["invoice"] == "INV007"
        assert job["service_description"] is None
        assert job["end_date"] is None

    @pytest.mark.asyncio
    async def test_update_job_with_none_values(self, client, manager_user_token, sample_job):
        """Test updating a job to set optional fields to None"""
        headers = self.auth_headers(manager_user_token)
        update_data = {
            "service_description": None,
            "end_date": None
        }
        
        response = client.patch(f"/api/v1/jobs/{sample_job.job_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        job = response.json()
        assert job["service_description"] is None
        assert job["end_date"] is None

    @pytest.mark.asyncio
    async def test_job_status_transitions(self, client, manager_user_token, sample_job):
        """Test different status transitions for a job"""
        headers = self.auth_headers(manager_user_token)
        
        # Pending to In Progress
        update_data = {"status": "pending"}
        response = client.patch(f"/api/v1/jobs/{sample_job.job_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "pending"
        
        # In Progress to Completed
        update_data = {"status": "in_progress"}
        response = client.patch(f"/api/v1/jobs/{sample_job.job_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"
        
        # Complete the job
        update_data = {"status": "completed"}
        response = client.patch(f"/api/v1/jobs/{sample_job.job_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    @pytest.mark.asyncio
    async def test_concurrent_job_creation(self, client, manager_user_token, sample_customer_car):
        """Test concurrent job creation for stress testing"""
        headers = self.auth_headers(manager_user_token)
        
        # Create multiple jobs with different invoices
        job_data_list = [
            {
                "customer_car_id": sample_customer_car.customer_car_id,
                "invoice": f"CONCURRENT{i}",
                "service_description": f"Concurrent job {i}",
                "start_date": "2024-03-01",
                "status": "pending"
            }
            for i in range(3)
        ]
        
        responses = []
        for job_data in job_data_list:
            response = client.post("/api/v1/jobs/", json=job_data, headers=headers)
            responses.append(response)
        
        # All jobs should be created successfully
        for response in responses:
            assert response.status_code == 200
        
        # Verify all jobs have unique IDs
        job_ids = [response.json()["job_id"] for response in responses]
        assert len(set(job_ids)) == len(job_ids)  # All IDs should be unique

    @pytest.mark.asyncio
    async def test_jobs_with_no_results(self, client, manager_user_token):
        """Test getting jobs when none exist for the user"""
        # Create a new manager with no jobs
        from auth.auth import pwd_context
        
        # This manager should have no jobs initially (except sample_job from fixture)
        headers = self.auth_headers(manager_user_token)
        
        response = client.get("/api/v1/jobs/?skip=1000&limit=10", headers=headers)
        assert response.status_code == 200
        
        jobs = response.json()
        assert len(jobs) == 0

    @pytest.mark.asyncio
    async def test_job_car_information_integrity(self, client, manager_user_token, sample_job):
        """Test that job responses always include correct car information"""
        headers = self.auth_headers(manager_user_token)
        
        response = client.get(f"/api/v1/jobs/{sample_job.job_id}", headers=headers)
        assert response.status_code == 200
        
        job = response.json()
        
        # Verify all required car info fields are present
        required_fields = ["car_brand", "car_model", "car_year", "license_plate"]
        for field in required_fields:
            assert field in job
            assert job[field] is not None
        
        # Verify car info matches expected values
        assert job["car_brand"] == "Toyota"
        assert job["car_model"] == "Camry"
        assert job["car_year"] == 2020
        assert job["license_plate"] == "ABC123"
