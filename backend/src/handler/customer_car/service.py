from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from handler.workshops.service import get_current_user_workshop_id
from db import models, schemas
from exceptions.exceptions import notFoundException, fetchErrorException
from logger.logger import get_logger

logger = get_logger()   


# ---------------- All customer_car functions ----------------
async def create_customer_car_for_current_user_workshop(
    current_user: dict,
    customer_car: schemas.CustomerCarCreate,
    db: AsyncSession
):  
    """
    Create a customer_car for the current logged-in user's workshop
    """
    try:
        logger.debug(f"Creating customer_car for customer ID {customer_car.customer_id} workshop")
        
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error(f"User with ID {current_user['user_id']} does not have an associated workshop",
                         extra={"user_id": current_user["user_id"], "endpoint": "create_customer_car_for_current_user_workshop"})
            raise HTTPException(status_code=400, detail="User does not have an associated workshop")
        
        # Check if customer exist in the user's workshop
        customer_res = await db.execute(
            select(models.Customer)
            .where(models.Customer.customer_id == customer_car.customer_id)
            .where(models.Customer.workshop_id == workshop_id)
        )
        # If customer does not exist, raise 404
        result = customer_res.scalar_one_or_none()
        if result is None:
            logger.error(f"Customer with ID {customer_car.customer_id} not found in workshop ID {workshop_id}",
                        extra={"user_id": current_user["user_id"], "workshop_id": workshop_id, 
                                "endpoint": "create_customer_car_for_current_user_workshop"})
            raise HTTPException(status_code=404, detail="Customer not found in your workshop")
        # Create customer_car model
        create_customer_car_model = models.CustomerCar(
            customer_id=customer_car.customer_id,
            car_id=customer_car.car_id,
            license_plate=customer_car.license_plate,
            color=customer_car.color
        )

        db.add(create_customer_car_model)
        await db.commit()
        await db.refresh(create_customer_car_model)
        logger.info(f"CustomerCar created with ID {create_customer_car_model.customer_car_id} for customer ID {customer_car.customer_id}")
        return create_customer_car_model
    except HTTPException:
        raise  
    except Exception as e:
        logger.critical(f"Database error in create_customer_car_for_current_user_workshop: {e}",
                     extra={"user_id": current_user["user_id"], "workshop_id": workshop_id,
                            "endpoint": "create_customer_car_for_current_user_workshop"})
        raise fetchErrorException

# ADMIN FUNCTION
async def create_customer_car(
        customer_car: schemas.CustomerCarCreate,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to create a new customer_car
    '''
    try:
        logger.debug(f"[ADMIN FUNC] Creating customer_car for customer ID {customer_car.customer_id}",
                      extra={"user_id": current_user["user_id"], "endpoint": "create_customer_car"})
        
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error(f"[ADMIN FUNC] User with ID {current_user['user_id']} does not have an associated workshop",
                         extra={"user_id": current_user["user_id"], "endpoint": "create_customer_car"})
            raise HTTPException(status_code=400, detail="User does not have an associated workshop")
        
        # Check if customer exist in db
        customer_res = await db.execute(select(models.Customer).where(models.Customer.customer_id == customer_car.customer_id))
        if customer_res.scalar_one_or_none() is None:
            logger.warning(f"[ADMIN FUNC] Customer with ID {customer_car.customer_id} not found",
                           extra={"user_id": current_user["user_id"], "endpoint": "create_customer_car"})
            raise HTTPException(status_code=404, detail="Customer not found")

        # Check if car exist in db
        car_res = await db.execute(select(models.Car).where(models.Car.car_id == customer_car.car_id))
        if car_res.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Car not found")

        db_customer_car = models.CustomerCar(**customer_car.model_dump())

        db.add(db_customer_car)
        await db.commit()
        await db.refresh(db_customer_car)
        logger.info(f"[ADMIN FUNC] CustomerCar created with ID {db_customer_car.customer_car_id} by admin",
                    extra={"user_id": current_user["user_id"], "endpoint": "create_customer_car"})
        return db_customer_car
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ADMIN FUNC] Database error in create_customer_car: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "create_customer_car"})
        raise fetchErrorException
    
# ADMIN FUNCTION
async def get_all_customers_cars(
        db: AsyncSession, 
        current_user: dict, 
        skip: int = 0, 
        limit: int = 100):
    '''
    Construct a query to get all customers_cars with car information
    '''
    try:
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error(f"[ADMIN FUNC] User with ID {current_user['user_id']} does not have an associated workshop",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_all_customers_cars"})
            raise HTTPException(status_code=400, detail="User does not have an associated workshop")

        logger.info(f"[ADMIN FUNC] Fetching all customer_cars by admin",
                    extra={"user_id": current_user["user_id"], "endpoint": "get_all_customers_cars"})
        result = await db.execute(
            select(models.CustomerCar, models.Car)
            .join(models.Car, models.CustomerCar.car_id == models.Car.car_id)
            .offset(skip)
            .limit(limit)
        )
        
        customer_cars_with_info = [
            schemas.CustomerCarWithCarInfo(
                customer_car_id=customer_car.customer_car_id,
                customer_id=customer_car.customer_id,
                car_id=customer_car.car_id,
                license_plate=customer_car.license_plate,
                color=customer_car.color,
                car_brand=car.brand,
                car_model=car.model,
                car_year=car.year
            )
            for customer_car, car in result.all()
        ]
        
        logger.info(f"[ADMIN FUNC] Fetched all customer_cars by admin",
                    extra={"user_id": current_user["user_id"], "endpoint": "get_all_customers_cars"})
        return customer_cars_with_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ADMIN FUNC] Database error in get_all_customers_cars: {e}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_all_customers_cars"})
        raise fetchErrorException
    
async def get_customer_cars_for_current_user_workshop(
    db: AsyncSession,    
    current_user: dict,    
    skip: int = 0,
    limit: int = 100
):
    """
    Get customer_cars associated with the current logged-in user's workshop with car information
    """
    try:
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error(f"User with ID {current_user['user_id']} does not have an associated workshop",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_customer_cars_for_current_user_workshop"})
            raise HTTPException(status_code=400, detail="User does not have an associated workshop")

        logger.debug(f"Fetching customer_cars for workshop ID {workshop_id}",
                     extra={"user_id": current_user["user_id"], "workshop_id": workshop_id,
                            "endpoint": "get_customer_cars_for_current_user_workshop"})

        result = await db.execute(
            select(models.CustomerCar, models.Car)
            .join(models.Car, models.CustomerCar.car_id == models.Car.car_id)
            .join(models.Customer, models.CustomerCar.customer_id == models.Customer.customer_id)
            .filter(models.Customer.workshop_id == workshop_id)
            .offset(skip)
            .limit(limit)
        )
        customer_cars_data = result.all()
        
        customer_cars_with_info = [
            schemas.CustomerCarWithCarInfo(
                customer_car_id=customer_car.customer_car_id,
                customer_id=customer_car.customer_id,
                car_id=customer_car.car_id,
                license_plate=customer_car.license_plate,
                color=customer_car.color,
                car_brand=car.brand,
                car_model=car.model,
                car_year=car.year
            )
            for customer_car, car in customer_cars_data
        ]


        logger.info(f"Fetched {len(customer_cars_with_info)} customer_cars for workshop ID {workshop_id}",
                    extra={"user_id": current_user["user_id"], "workshop_id": workshop_id,
                           "endpoint": "get_customer_cars_for_current_user_workshop"})
        return customer_cars_with_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in get_customer_cars_for_current_user_workshop: {e}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_customer_cars_for_current_user_workshop"})
        raise fetchErrorException
    
async def get_customer_car_by_id(
        customer_car_id: int,
        db: AsyncSession, 
        current_user: dict):
    '''
    Construct a query to get a customer_car by ID with car information
    '''
    try:
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error(f"User with ID {current_user['user_id']} does not have an associated workshop",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_customer_car_by_id"})
            raise HTTPException(status_code=400, detail="User does not have an associated workshop")
        
        logger.debug(f"Fetching customer_car with ID {customer_car_id}",
                     extra={"user_id": current_user["user_id"], "endpoint": "get_customer_car_by_id"})
        result = await db.execute(
            select(models.CustomerCar, models.Car)
            .join(models.Car, models.CustomerCar.car_id == models.Car.car_id)
            .where(models.CustomerCar.customer_car_id == customer_car_id)
        )
        # Get customer_car data
        customer_car_data = result.first()
        # If customer_car not found, raise 404
        if customer_car_data is None:
            logger.error(f"CustomerCar with ID {customer_car_id} not found",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_customer_car_by_id"})
            raise notFoundException
        
        customer_car, car = customer_car_data
        
        logger.info(f"Fetched customer_car with ID {customer_car_id}",
                    extra={"user_id": current_user["user_id"], "endpoint": "get_customer_car_by_id"})
        return schemas.CustomerCarWithCarInfo(
            customer_car_id=customer_car.customer_car_id,
            customer_id=customer_car.customer_id,
            car_id=customer_car.car_id,
            license_plate=customer_car.license_plate,
            color=customer_car.color,
            car_brand=car.brand,
            car_model=car.model,
            car_year=car.year
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in get_customer_car_by_id: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "get_customer_car_by_id"})
        raise fetchErrorException
    
async def update_customer_car(
        customer_car_id: int,
        customer_car_update: schemas.CustomerCarUpdate,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to update a customer_car's information
    '''
    try:
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error(f"User with ID {current_user['user_id']} does not have an associated workshop",
                         extra={"user_id": current_user["user_id"], "endpoint": "update_customer_car"})
            raise HTTPException(status_code=400, detail="User does not have an associated workshop")
        
        logger.debug(f"Updating customer_car with ID {customer_car_id}",
                     extra={"user_id": current_user["user_id"], "endpoint": "update_customer_car"})
        # Get the actual SQLAlchemy model for updating
        result = await db.execute(
            select(models.CustomerCar).where(models.CustomerCar.customer_car_id == customer_car_id)
        )
        customer_car_model = result.scalar_one_or_none()
        if customer_car_model is None:
            logger.error(f"CustomerCar with ID {customer_car_id} not found for update",
                         extra={"user_id": current_user["user_id"], "endpoint": "update_customer_car"})
            raise notFoundException
            
        # Prepare update data
        update_data = customer_car_update.model_dump(exclude_unset=True)

        if "customer_id" in update_data:
            customer_res = await db.execute(select(models.Customer).where(models.Customer.customer_id == update_data["customer_id"]))
            if customer_res.scalar_one_or_none() is None:
                logger.error(f"Customer with ID {update_data['customer_id']} not found for update",
                             extra={"user_id": current_user["user_id"], "endpoint": "update_customer_car"})
                raise HTTPException(status_code=404, detail="Customer not found")

        if "car_id" in update_data:
            car_res = await db.execute(select(models.Car).where(models.Car.car_id == update_data["car_id"]))
            if car_res.scalar_one_or_none() is None:
                logger.error(f"Car with ID {update_data['car_id']} not found for update",
                             extra={"user_id": current_user["user_id"], "endpoint": "update_customer_car"})
                raise HTTPException(status_code=404, detail="Car not found")

        # Update the SQLAlchemy model fields
        for field, value in update_data.items():
            setattr(customer_car_model, field, value)
        # Commit the transaction
        await db.commit()
        await db.refresh(customer_car_model)
        logger.info(f"CustomerCar with ID {customer_car_id} updated successfully",
                    extra={"user_id": current_user["user_id"], "endpoint": "update_customer_car"})
        return customer_car_model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in update_customer_car: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "update_customer_car"})
        raise fetchErrorException
    
async def delete_customer_car(
        customer_car_id: int,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to delete a customer_car
    '''
    try:
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error(f"User with ID {current_user['user_id']} does not have an associated workshop",
                         extra={"user_id": current_user["user_id"], "endpoint": "delete_customer_car"})
            raise HTTPException(status_code=400, detail="User does not have an associated workshop")
        
        logger.debug(f"Deleting customer_car with ID {customer_car_id}",
                     extra={"user_id": current_user["user_id"], "endpoint": "delete_customer_car"})
        
        customer_car_data = await get_customer_car_by_id(customer_car_id, db, current_user)

        await db.execute(
            delete(models.CustomerCar).where(models.CustomerCar.customer_car_id == customer_car_id)
        )
        await db.commit()
        logger.info(f"CustomerCar with ID {customer_car_id} deleted successfully",
                    extra={"user_id": current_user["user_id"], "endpoint": "delete_customer_car"})
        return customer_car_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in delete_customer_car: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "delete_customer_car"})
        raise fetchErrorException