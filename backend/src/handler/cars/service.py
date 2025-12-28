from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime
from logger.logger import get_logger

from auth.auth import get_current_user, pwd_context, admin_required
from db import models, schemas

def validate_car_creation(car: schemas.CarCreate):
    '''
    Validate car fields before database operations
    '''
    if car.year < 1900 or car.year > datetime.now().year + 1:
        raise HTTPException(status_code=422, detail="Invalid year for car")
    if not car.brand or car.brand.strip() == "":
        raise HTTPException(status_code=422, detail="Brand cannot be empty")
    if len(car.brand) > 100:
        raise HTTPException(status_code=422, detail="Brand name too long")
    if not car.model or car.model.strip() == "":
        raise HTTPException(status_code=422, detail="Model cannot be empty")
    if len(car.model) > 100:
        raise HTTPException(status_code=422, detail="Model name too long")

def validate_car_update(car: schemas.CarUpdate):
    '''
    Validate car fields before update operations
    '''
    if car.year is not None:
        if car.year < 1900 or car.year > datetime.now().year + 1:
            raise HTTPException(status_code=422, detail="Invalid year for car")
    if car.brand is not None:
        if car.brand.strip() == "":
            raise HTTPException(status_code=422, detail="Brand cannot be empty")
        if len(car.brand) > 100:
            raise HTTPException(status_code=422, detail="Brand name too long")
    if car.model is not None:
        if car.model.strip() == "":
            raise HTTPException(status_code=422, detail="Model cannot be empty")
        if len(car.model) > 100:
            raise HTTPException(status_code=422, detail="Model name too long")

logger = get_logger()


# ---------------- All cars functions ----------------
async def create_car(car: schemas.CarCreate, db: AsyncSession, current_user: dict):
    '''
    Construct a query to create a new car
    '''
    try:
        validate_car_creation(car)
        db_car = models.Car(**car.model_dump())
        db.add(db_car)
        await db.commit()
        await db.refresh(db_car)
        logger.info(f"Car created with ID: {db_car.car_id} by user ID: {current_user['user_id']}")
        return db_car
    except Exception as e:
        logger.error(f"Database error in create_car: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating car: {e}")
    
async def get_all_cars(current_user: dict, db: AsyncSession, skip: int = 0, limit: int = 100):
    '''
    Construct a query to get all cars with pagination
    '''
    try:
        result = await db.execute(
            select(models.Car).offset(skip).limit(limit)
        )
        cars = result.scalars().all()
        logger.info(f"Retrieved {len(cars)} cars from database by user ID: {current_user['user_id']}")
        return cars
    except Exception as e:
        logger.error(f"Database error in get_all_cars: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching cars from database: {e}")
    
async def get_car_by_id(current_user: dict, db: AsyncSession, car_id: int):
    '''
    Construct a query to get a car by ID
    '''
    try:
        result = await db.execute(
            select(models.Car).filter(models.Car.car_id == car_id)
        )
        # Get car data
        db_car = result.scalar_one_or_none()
        # If car not found, raise 404
        if db_car is None:
            raise HTTPException(status_code=404, detail="Car not found")
        logger.info(f"Car retrieved with ID: {car_id} by user ID: {current_user['user_id']}")
        return db_car
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in get_car_by_id: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching car from database: {e}")
    
async def update_car(current_user: dict, car_id: int, db: AsyncSession, car_update: schemas.CarUpdate):
    '''
    Construct a query to update a car's information
    '''
    try:
        validate_car_update(car_update)
        car_data = await get_car_by_id(current_user, db, car_id)
            # Prepare update data
        update_data = car_update.model_dump(exclude_unset=True)
        # Update fields
        for key, value in update_data.items():
            setattr(car_data, key, value)
        await db.commit()
        await db.refresh(car_data)
        logger.info(f"Car updated with ID: {car_id} by user ID: {current_user['user_id']}")
        return car_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in update_car: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating car: {e}")
    

async def delete_car(current_user: dict, db: AsyncSession, car_id: int):
    '''
    Construct a query to delete a car
    '''
    try:
        car_data = await get_car_by_id(current_user, db, car_id)
        await db.execute(
            delete(models.Car).where(models.Car.car_id == car_id)
        )
        await db.commit()
        return car_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in delete_car: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting car: {e}")