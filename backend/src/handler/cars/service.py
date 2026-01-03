from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from logger.logger import get_logger
from db import models, schemas

logger = get_logger()


# ---------------- All cars functions ----------------
async def create_car(car: schemas.CarCreate, db: AsyncSession, current_user: dict):
    '''
    Construct a query to create a new car
    '''
    try:
        logger.debug(f"Attempting to create a new car by user ID: {current_user['user_id']}")   
        # create car instance
        db_car = models.Car(**car.model_dump())
        # add to session and commit
        db.add(db_car)
        await db.commit()
        await db.refresh(db_car)
        logger.info(f"Car created with ID: {db_car.car_id} by user ID: {current_user['user_id']}")
        return db_car
    except Exception as e:
        logger.critical(f"Database error in create_car: {e}",
                        extra={"user_id": current_user["user_id"], "endpoint": "create_car"})
        raise HTTPException(status_code=500, detail=f"Error creating car: {e}")
    
async def get_all_cars(current_user: dict, db: AsyncSession, skip: int = 0, limit: int = 100):
    '''
    Construct a query to get all cars with pagination
    '''
    try:
        logger.debug(f"Attempting to retrieve all cars by user ID: {current_user['user_id']}")
        # get car data
        result = await db.execute(
            select(models.Car).offset(skip).limit(limit)
        )
        # query result
        cars = result.scalars().all()
        logger.info(f"Retrieved {len(cars)} cars from database by user ID: {current_user['user_id']}")
        return cars
    except Exception as e:
        logger.critical(f"Database error in get_all_cars: {e}",
                        extra={"user_id": current_user["user_id"], "endpoint": "get_all_cars"})
        raise HTTPException(status_code=500, detail=f"Error fetching cars from database: {e}")
    
async def get_car_by_id(current_user: dict, db: AsyncSession, car_id: int):
    '''
    Construct a query to get a car by ID
    '''
    try:
        logger.debug(f"Attempting to retrieve car with ID: {car_id} by user ID: {current_user['user_id']}")
        # get car data
        result = await db.execute(
            select(models.Car).filter(models.Car.car_id == car_id)
        )
        # Get car data
        db_car = result.scalar_one_or_none()
        # If car not found, raise 404
        if db_car is None:
            logger.error(f"Car with ID: {car_id} not found by user ID: {current_user['user_id']}",
                         extra={"car_id": car_id, "user_id": current_user["user_id"], "endpoint": "get_car_by_id"})
            raise HTTPException(status_code=404, detail="Car not found")
        logger.info(f"Car retrieved with ID: {car_id} by user ID: {current_user['user_id']}")
        return db_car
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_car_by_id: {e}",
                        extra={"car_id": car_id, "user_id": current_user["user_id"], "endpoint": "get_car_by_id"})
        raise HTTPException(status_code=500, detail=f"Error fetching car from database: {e}")
    
async def update_car(current_user: dict, car_id: int, db: AsyncSession, car_update: schemas.CarUpdate):
    '''
    Construct a query to update a car's information
    '''
    try:
        logger.debug(f"Attempting to update car with ID: {car_id} by user ID: {current_user['user_id']}")   
        # Get existing car data
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
        logger.critical(f"Database error in update_car: {e}",
                        extra={"car_id": car_id, "user_id": current_user["user_id"], "endpoint": "update_car"})
        raise HTTPException(status_code=500, detail=f"Error updating car: {e}")

async def delete_car(current_user: dict, db: AsyncSession, car_id: int):
    '''
    Construct a query to delete a car
    '''
    try:
        logger.debug(f"Attempting to delete car with ID: {car_id} by user ID: {current_user['user_id']}")   
        # Get car data to return after deletion
        car_data = await get_car_by_id(current_user, db, car_id)
        # Delete the car
        await db.execute(
            delete(models.Car).where(models.Car.car_id == car_id)
        )
        # Commit changes
        await db.commit()
        logger.info(f"Car deleted with ID: {car_id} by user ID: {current_user['user_id']}")
        return car_data
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in delete_car: {e}",
                        extra={"car_id": car_id, "user_id": current_user["user_id"], "endpoint": "delete_car"})
        raise HTTPException(status_code=500, detail=f"Error deleting car: {e}")