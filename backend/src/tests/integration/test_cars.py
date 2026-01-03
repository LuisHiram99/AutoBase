import pytest
import pytest_asyncio
from db import models
from sqlalchemy import select


class TestCarsIntegration:
    """Integration tests for cars endpoints testing complete workflow from API to database"""
    
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
                email="admin_cars@test.com",
                hashed_password=pwd_context.hash("Adminpass123%"),
                role="admin",
                workshop_id=workshop_id
            )
            session.add(admin_user)
            await session.commit()
        
        # Login to get token
        login_data = {
            "username": "admin_cars@test.com",
            "password": "Adminpass123%"
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
                email="manager_cars@test.com",
                hashed_password=pwd_context.hash("Managerpass123%"),
                role=models.RoleEnum.manager,
                workshop_id=workshop_id
            )
            session.add(manager_user)
            await session.commit()
        
        # Login to get token
        login_data = {
            "username": "manager_cars@test.com",
            "password": "Managerpass123%"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        return response.json()["access_token"]

    def auth_headers(self, token):
        """Helper method to create authorization headers"""
        return {"Authorization": f"Bearer {token}"}

    # ================== CREATE CAR TESTS ==================

    @pytest.mark.asyncio
    async def test_create_car_as_admin(self, client, admin_user_token, db_session):
        """Test admin user creating a car"""
        headers = self.auth_headers(admin_user_token)
        car_data = {
            "year": 2023,
            "brand": "Toyota",
            "model": "Camry"
        }
        
        response = client.post("/api/v1/cars/", json=car_data, headers=headers)
        assert response.status_code == 200
        
        car = response.json()
        assert car["year"] == 2023
        assert car["brand"] == "Toyota"
        assert car["model"] == "Camry"
        assert "car_id" in car
        
        # Verify car was saved to database
        async with db_session as session:
            result = await session.execute(
                select(models.Car).where(models.Car.brand == "Toyota", models.Car.model == "Camry")
            )
            db_car = result.scalar_one_or_none()
            assert db_car is not None
            assert db_car.year == 2023

    @pytest.mark.asyncio
    async def test_create_car_as_manager(self, client, manager_user_token, db_session):
        """Test manager user creating a car"""
        headers = self.auth_headers(manager_user_token)
        car_data = {
            "year": 2022,
            "brand": "Honda",
            "model": "Civic"
        }
        
        response = client.post("/api/v1/cars/", json=car_data, headers=headers)
        assert response.status_code == 200
        
        car = response.json()
        assert car["year"] == 2022
        assert car["brand"] == "Honda" 
        assert car["model"] == "Civic"
        
        # Verify car was saved to database
        async with db_session as session:
            result = await session.execute(
                select(models.Car).where(models.Car.brand == "Honda", models.Car.model == "Civic")
            )
            db_car = result.scalar_one_or_none()
            assert db_car is not None
            assert db_car.year == 2022

    @pytest.mark.asyncio
    async def test_create_car_unauthenticated(self, client):
        """Test creating car without authentication fails"""
        car_data = {
            "year": 2021,
            "brand": "Ford",
            "model": "Focus"
        }
        
        response = client.post("/api/v1/cars/", json=car_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_car_invalid_data(self, client, admin_user_token):
        """Test creating car with invalid data"""
        headers = self.auth_headers(admin_user_token)
        
        # Missing required fields
        invalid_data = {
            "year": 2023,
            "brand": "Tesla"
            # Missing model
        }
        
        response = client.post("/api/v1/cars/", json=invalid_data, headers=headers)
        assert response.status_code in [400, 422, 429]  # Validation error or rate limit
        
        # Invalid year
        invalid_year_data = {
            "year": "not_a_number",
            "brand": "BMW",
            "model": "X5"
        }
        
        response = client.post("/api/v1/cars/", json=invalid_year_data, headers=headers)
        assert response.status_code in [400, 422, 429]

    # ================== READ CARS TESTS ==================

    @pytest.mark.asyncio
    async def test_get_cars_as_admin(self, client, admin_user_token, db_session):
        """Test admin user can get all cars"""
        # Create test cars
        async with db_session as session:
            car1 = models.Car(year=2020, brand="Audi", model="A4")
            car2 = models.Car(year=2021, brand="BMW", model="3 Series")
            session.add_all([car1, car2])
            await session.commit()
        
        headers = self.auth_headers(admin_user_token)
        response = client.get("/api/v1/cars/", headers=headers)
        assert response.status_code == 200
        
        cars = response.json()
        assert len(cars) >= 2
        car_brands = [c["brand"] for c in cars]
        assert "Audi" in car_brands
        assert "BMW" in car_brands

    @pytest.mark.asyncio
    async def test_get_cars_as_manager(self, client, manager_user_token, db_session):
        """Test manager user can get all cars"""
        # Create test cars
        async with db_session as session:
            car1 = models.Car(year=2019, brand="Mercedes", model="C-Class")
            car2 = models.Car(year=2020, brand="Lexus", model="RX")
            session.add_all([car1, car2])
            await session.commit()
        
        headers = self.auth_headers(manager_user_token)
        response = client.get("/api/v1/cars/", headers=headers)
        assert response.status_code == 200
        
        cars = response.json()
        assert len(cars) >= 2
        car_brands = [c["brand"] for c in cars]
        assert "Mercedes" in car_brands
        assert "Lexus" in car_brands

    @pytest.mark.asyncio
    async def test_get_cars_pagination(self, client, admin_user_token, db_session):
        """Test cars pagination parameters"""
        # Create multiple cars
        async with db_session as session:
            cars = [
                models.Car(
                    year=2010 + i,
                    brand=f"Brand{i}",
                    model=f"Model{i}"
                ) for i in range(15)
            ]
            session.add_all(cars)
            await session.commit()
        
        headers = self.auth_headers(admin_user_token)
        
        # Test limit
        response = client.get("/api/v1/cars/?limit=5", headers=headers)
        assert response.status_code == 200
        cars = response.json()
        assert len(cars) == 5
        
        # Test skip and limit
        response = client.get("/api/v1/cars/?skip=5&limit=5", headers=headers)
        assert response.status_code == 200
        cars = response.json()
        assert len(cars) == 5

    @pytest.mark.asyncio
    async def test_get_cars_unauthenticated(self, client):
        """Test getting cars without authentication fails"""
        response = client.get("/api/v1/cars/")
        assert response.status_code == 401

    # ================== READ SINGLE CAR TESTS ==================

    @pytest.mark.asyncio
    async def test_get_car_by_id_as_admin(self, client, admin_user_token, db_session):
        """Test admin user can get any car by ID"""
        # Create car
        async with db_session as session:
            car = models.Car(
                year=2023,
                brand="Porsche",
                model="911"
            )
            session.add(car)
            await session.commit()
            await session.refresh(car)
            car_id = car.car_id
        
        headers = self.auth_headers(admin_user_token)
        response = client.get(f"/api/v1/cars/{car_id}", headers=headers)
        assert response.status_code == 200
        
        car_data = response.json()
        assert car_data["car_id"] == car_id
        assert car_data["brand"] == "Porsche"
        assert car_data["model"] == "911"
        assert car_data["year"] == 2023

    @pytest.mark.asyncio
    async def test_get_car_by_id_as_manager(self, client, manager_user_token, db_session):
        """Test manager user can get any car by ID"""
        # Create car
        async with db_session as session:
            car = models.Car(
                year=2022,
                brand="Subaru",
                model="Outback"
            )
            session.add(car)
            await session.commit()
            await session.refresh(car)
            car_id = car.car_id
        
        headers = self.auth_headers(manager_user_token)
        response = client.get(f"/api/v1/cars/{car_id}", headers=headers)
        assert response.status_code == 200
        
        car_data = response.json()
        assert car_data["car_id"] == car_id
        assert car_data["brand"] == "Subaru"

    @pytest.mark.asyncio
    async def test_get_car_not_found(self, client, admin_user_token):
        """Test getting non-existent car returns 404"""
        headers = self.auth_headers(admin_user_token)
        response = client.get("/api/v1/cars/99999", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_car_unauthenticated(self, client):
        """Test getting car without authentication fails"""
        response = client.get("/api/v1/cars/1")
        assert response.status_code == 401

    # ================== UPDATE CAR TESTS ==================

    @pytest.mark.asyncio
    async def test_update_car_as_admin(self, client, admin_user_token, db_session):
        """Test admin user can update any car"""
        # Create car
        async with db_session as session:
            car = models.Car(
                year=2020,
                brand="Original",
                model="Model"
            )
            session.add(car)
            await session.commit()
            await session.refresh(car)
            car_id = car.car_id
        
        headers = self.auth_headers(admin_user_token)
        update_data = {
            "year": 2021,
            "brand": "Updated",
            "model": "NewModel"
        }
        
        response = client.put(f"/api/v1/cars/{car_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        updated_car = response.json()
        assert updated_car["year"] == 2021
        assert updated_car["brand"] == "Updated"
        assert updated_car["model"] == "NewModel"
        
        # Verify in database
        async with db_session as session:
            result = await session.execute(
                select(models.Car).where(models.Car.car_id == car_id)
            )
            db_car = result.scalar_one_or_none()
            assert db_car.brand == "Updated"
            assert db_car.year == 2021

    @pytest.mark.asyncio
    async def test_update_car_partial_as_manager(self, client, manager_user_token, db_session):
        """Test manager user can partially update a car"""
        # Create car
        async with db_session as session:
            car = models.Car(
                year=2019,
                brand="Partial",
                model="Update"
            )
            session.add(car)
            await session.commit()
            await session.refresh(car)
            car_id = car.car_id
        
        headers = self.auth_headers(manager_user_token)
        # Only update year, leave brand and model unchanged
        update_data = {
            "year": 2020
        }
        
        response = client.put(f"/api/v1/cars/{car_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        updated_car = response.json()
        assert updated_car["year"] == 2020
        assert updated_car["brand"] == "Partial"  # Unchanged
        assert updated_car["model"] == "Update"   # Unchanged

    @pytest.mark.asyncio
    async def test_update_car_not_found(self, client, admin_user_token):
        """Test updating non-existent car returns 404"""
        headers = self.auth_headers(admin_user_token)
        update_data = {
            "year": 2023,
            "brand": "NotFound",
            "model": "Car"
        }
        
        response = client.put("/api/v1/cars/99999", json=update_data, headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_car_unauthenticated(self, client):
        """Test updating car without authentication fails"""
        update_data = {
            "year": 2023,
            "brand": "Unauthorized",
            "model": "Update"
        }
        
        response = client.put("/api/v1/cars/1", json=update_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_car_invalid_data(self, client, admin_user_token, db_session):
        """Test updating car with invalid data"""
        # Create car
        async with db_session as session:
            car = models.Car(
                year=2020,
                brand="Valid",
                model="Car"
            )
            session.add(car)
            await session.commit()
            await session.refresh(car)
            car_id = car.car_id
        
        headers = self.auth_headers(admin_user_token)
        
        # Invalid year format
        invalid_data = {
            "year": "not_a_number"
        }
        
        response = client.put(f"/api/v1/cars/{car_id}", json=invalid_data, headers=headers)
        assert response.status_code in [400, 422, 429]

    # ================== DELETE CAR TESTS ==================

    @pytest.mark.asyncio
    async def test_delete_car_as_admin(self, client, admin_user_token, db_session):
        """Test admin user can delete any car"""
        # Create car
        async with db_session as session:
            car = models.Car(
                year=2021,
                brand="ToDelete",
                model="Car"
            )
            session.add(car)
            await session.commit()
            await session.refresh(car)
            car_id = car.car_id
        
        headers = self.auth_headers(admin_user_token)
        response = client.delete(f"/api/v1/cars/{car_id}", headers=headers)
        assert response.status_code == 200
        
        deleted_car = response.json()
        assert deleted_car["car_id"] == car_id
        assert deleted_car["brand"] == "ToDelete"
        
        # Verify deleted from database
        async with db_session as session:
            result = await session.execute(
                select(models.Car).where(models.Car.car_id == car_id)
            )
            db_car = result.scalar_one_or_none()
            assert db_car is None

    @pytest.mark.asyncio
    async def test_delete_car_as_manager(self, client, manager_user_token, db_session):
        """Test manager user can delete cars"""
        # Create car
        async with db_session as session:
            car = models.Car(
                year=2022,
                brand="ManagerDelete",
                model="Car"
            )
            session.add(car)
            await session.commit()
            await session.refresh(car)
            car_id = car.car_id
        
        headers = self.auth_headers(manager_user_token)
        response = client.delete(f"/api/v1/cars/{car_id}", headers=headers)
        assert response.status_code == 200
        
        # Verify deleted from database
        async with db_session as session:
            result = await session.execute(
                select(models.Car).where(models.Car.car_id == car_id)
            )
            db_car = result.scalar_one_or_none()
            assert db_car is None

    @pytest.mark.asyncio
    async def test_delete_car_not_found(self, client, admin_user_token):
        """Test deleting non-existent car returns 404"""
        headers = self.auth_headers(admin_user_token)
        response = client.delete("/api/v1/cars/99999", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_car_unauthenticated(self, client):
        """Test deleting car without authentication fails"""
        response = client.delete("/api/v1/cars/1")
        assert response.status_code == 401

    # ================== ERROR HANDLING TESTS ==================

    @pytest.mark.asyncio
    async def test_create_duplicate_car(self, client, admin_user_token, db_session):
        """Test creating identical cars (should be allowed as cars don't have unique constraints)"""
        headers = self.auth_headers(admin_user_token)
        car_data = {
            "year": 2023,
            "brand": "Duplicate",
            "model": "Test"
        }
        
        # Create first car
        response1 = client.post("/api/v1/cars/", json=car_data, headers=headers)
        assert response1.status_code == 200
        
        # Create identical car (should be allowed)
        response2 = client.post("/api/v1/cars/", json=car_data, headers=headers)
        assert response2.status_code == 200
        
        # Verify both cars exist
        async with db_session as session:
            result = await session.execute(
                select(models.Car).where(models.Car.brand == "Duplicate", models.Car.model == "Test")
            )
            db_cars = result.scalars().all()
            assert len(db_cars) == 2

    @pytest.mark.asyncio
    async def test_car_operations_comprehensive_workflow(self, client, admin_user_token, db_session):
        """Test complete CRUD workflow for cars"""
        headers = self.auth_headers(admin_user_token)
        
        # 1. Create car
        car_data = {
            "year": 2023,
            "brand": "Workflow",
            "model": "Test"
        }
        
        create_response = client.post("/api/v1/cars/", json=car_data, headers=headers)
        assert create_response.status_code == 200
        car = create_response.json()
        car_id = car["car_id"]
        
        # 2. Read car
        read_response = client.get(f"/api/v1/cars/{car_id}", headers=headers)
        assert read_response.status_code == 200
        read_car = read_response.json()
        assert read_car["brand"] == "Workflow"
        
        # 3. Update car
        update_data = {"brand": "UpdatedWorkflow"}
        update_response = client.put(f"/api/v1/cars/{car_id}", json=update_data, headers=headers)
        assert update_response.status_code == 200
        updated_car = update_response.json()
        assert updated_car["brand"] == "UpdatedWorkflow"
        
        # 4. Delete car
        delete_response = client.delete(f"/api/v1/cars/{car_id}", headers=headers)
        assert delete_response.status_code == 200
        
        # 5. Verify deletion
        verify_response = client.get(f"/api/v1/cars/{car_id}", headers=headers)
        assert verify_response.status_code == 404

    @pytest.mark.asyncio
    async def test_rate_limiting_behavior(self, client, admin_user_token):
        """Test that rate limiting is properly handled"""
        headers = self.auth_headers(admin_user_token)
        car_data = {
            "year": 2023,
            "brand": "RateLimit",
            "model": "Test"
        }
        
        # Make multiple rapid requests - should handle rate limiting gracefully
        responses = []
        for i in range(5):
            response = client.post("/api/v1/cars/", json=car_data, headers=headers)
            responses.append(response.status_code)
        
        # Should have at least some successful requests (200) and possibly some rate limited (429)
        assert 200 in responses
        # Rate limiting might kick in, but should not cause server errors
        assert all(status in [200, 429] for status in responses)
