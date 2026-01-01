from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel, EmailStr
from auth.auth import get_current_user, pwd_context, admin_required
from db import models, schemas
from exceptions.exceptions import notFoundException, fetchErrorException
from ..workshops.service import get_current_user_workshop_id
from logger.logger import get_logger
from typing import List, Union
logger = get_logger()

# ---------------- All customers functions ----------------
async def create_customer(
        customer: schemas.CustomerCreate,
        db: AsyncSession,
        current_user: dict) -> models.Customer:
    '''
    Construct a query to create a new customer
    '''
    try:
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        
        db_customer = models.Customer(**customer.model_dump())

        db.add(db_customer)
        await db.commit()
        await db.refresh(db_customer)
        logger.info(f"Customer created with ID {db_customer.customer_id} by admin user", 
                    extra={"user_id": current_user["user_id"], "endpoint": "create_customer"})
        return db_customer
    except Exception as e:
        logger.error(f"Database error in create_customer: {e}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "create_customer"})
        raise fetchErrorException

async def create_current_user_workshop_customer(
    current_user: dict,
    customer: schemas.CustomerCreate,
    db: AsyncSession
) -> models.Customer:
    """
    Create a customer for the current logged-in user's workshop
    """
    try:
        logger.debug(f"Creating customer for workshop {get_current_user_workshop_id(current_user)}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "create_current_user_workshop_customer"})
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        
        create_customer_model = models.Customer(
            first_name=customer.first_name,
            last_name=customer.last_name,
            phone=customer.phone,
            email=customer.email,
            workshop_id=workshop_id  # Set automatically from user's workshop
        )

        db.add(create_customer_model)
        await db.commit()
        await db.refresh(create_customer_model)
        logger.info(f"Customer created with ID {create_customer_model.customer_id} for workshop {workshop_id}", 
                    extra={"user_id": current_user["user_id"], "endpoint": "create_current_user_workshop_customer"})
        return create_customer_model
    except HTTPException:
        raise   
    except Exception as e:
        logger.error(f"Database error in create_current_user_workshop_customer: {e}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "create_current_user_workshop_customer"})
        raise fetchErrorException


async def get_all_customers(
        db: AsyncSession, 
        current_user: dict, 
        skip: int = 0, 
        limit: int = 100):
    '''
    Construct a query to get all customers
    '''
    try:
        result = await db.execute(
            select(models.Customer).offset(skip).limit(limit)
        )
        customers = result.scalars().all()
        logger.info(f"Fetched {len(customers)} customers", 
                    extra={"user_id": current_user["user_id"], "endpoint": "get_all_customers"})
        return customers
    except Exception as e:
        logger.error(f"Database error in get_all_customers: {e}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_all_customers"})
        raise fetchErrorException
    
async def get_current_user_workshop_customers(
    current_user: dict,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[models.Customer]:
    """
    Get customers associated with the current logged-in user's workshop
    """
    try: 
        logger.debug(f"Fetching customers for workshop {get_current_user_workshop_id(current_user)}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customers"})
        workshop_id = get_current_user_workshop_id(current_user)
        
        if workshop_id == 1:
            logger.error(f"Current user {current_user['user_id']} has no associated workshop and tried to access customers",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customers"})
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        
        result = await db.execute(
            select(models.Customer)
            .filter(models.Customer.workshop_id == workshop_id)
            .offset(skip)
            .limit(limit)
        )
        customers = result.scalars().all()
        logger.info(f"Fetched {len(customers)} customers for workshop {workshop_id}", 
                    extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customers"})
        return customers
    except HTTPException:
        raise   
    except Exception as e:
        logger.error(f"Database error in get_current_user_workshop_customers: {e}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customers"})
        raise fetchErrorException

async def get_customer_by_id(
        customer_id: int,
        db: AsyncSession, 
        current_user: dict) -> models.Customer:
    '''
    Construct a query to get a customer by ID
    '''
    try:
        logger.debug(f"Fetching customer with ID {customer_id} by admin user", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_customer_by_id"})
        result = await db.execute(
            select(models.Customer).filter(models.Customer.customer_id == customer_id)
        )
        # Get customer data
        db_customer = result.scalar_one_or_none()
        # If customer not found, raise 404
        if db_customer is None:
            logger.error(f"Customer with ID {customer_id} not found", 
                         extra={"user_id": current_user["user_id"], "endpoint": "get_customer_by_id"})
            raise notFoundException
        logger.info(f"Customer with ID {customer_id} fetched by admin user", 
                    extra={"user_id": current_user["user_id"], "endpoint": "get_customer_by_id"})
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in get_customer_by_id: {e}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_customer_by_id"})
        raise fetchErrorException
    
async def get_current_user_workshop_customer_by_id(
        customer_id: int, 
        db: AsyncSession, 
        current_user: dict) -> models.Customer:
    """
    Get a specific customer by ID for the current logged-in user's workshop
    """
    try: 
        logger.debug(f"Fetching customer with ID {customer_id} for workshop {get_current_user_workshop_id(current_user)}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customer_by_id"})
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:   
            logger.error(f"Current user {current_user['user_id']} has no associated workshop and tried to access customer with ID {customer_id}",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customer_by_id"})
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        result = await db.execute(
            select(models.Customer)
            .filter(models.Customer.customer_id == customer_id)
            .filter(models.Customer.workshop_id == workshop_id)
        )
        db_customer = result.scalar_one_or_none()
        # If customer not found or does not belong to user's workshop, raise 404
        if db_customer is None:
            logger.error(f"Customer with ID {customer_id} not found in workshop {workshop_id}", 
                         extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customer_by_id"})
            raise notFoundException
        
        logger.info(f"Customer with ID {customer_id} fetched for workshop {workshop_id}", 
                    extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customer_by_id"})
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in get_current_user_workshop_customer_by_id: {e}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customer_by_id"})
        raise fetchErrorException


async def update_customer(
        customer_id: int, 
        customer_update: schemas.CustomerUpdate,
        db: AsyncSession,
        current_user: dict) -> models.Customer:
    '''
    Construct a query to update a customer's information
    '''
    try:
        customer_data = await get_customer_by_id(customer_id, db, current_user)
        logger.debug(f"Updating customer with ID {customer_id} by admin user", 
                     extra={"user_id": current_user["user_id"], "endpoint": "update_customer"})
        # Prepare update data
        update_data = customer_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(customer_data, key, value)
        await db.commit()
        await db.refresh(customer_data)
        logger.info(f"Customer with ID {customer_id} updated by admin user", 
                    extra={"user_id": current_user["user_id"], "endpoint": "update_customer"})
        return customer_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in update_customer: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "update_customer"})
        raise fetchErrorException

async def update_current_user_workshop_customer_by_id(
        customer_id: int, 
        customer_update: schemas.CustomerUpdate,
        db: AsyncSession, 
        current_user: dict) -> models.Customer:
    """
    Update a specific customer by ID for the current logged-in user's workshop
    """
    try: 
        logger.debug(f"Updating customer with ID {customer_id} for workshop {get_current_user_workshop_id(current_user)}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_workshop_customer_by_id"})
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:   
            logger.error(f"Current user {current_user['user_id']} has no associated workshop and tried to update customer with ID {customer_id}",
                         extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_workshop_customer_by_id"})
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        result = await db.execute(
            select(models.Customer)
            .filter(models.Customer.customer_id == customer_id)
            .filter(models.Customer.workshop_id == workshop_id)
        )
        customer_data = result.scalar_one_or_none()
        # If customer not found or does not belong to user's workshop, raise 404
        if customer_data is None:
            logger.error(f"Customer with ID {customer_id} not found in workshop {workshop_id}", 
                         extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_workshop_customer_by_id"})
            raise notFoundException
        
        update_data = customer_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(customer_data, key, value)

        await db.commit()
        await db.refresh(customer_data)
        logger.info(f"Customer with ID {customer_id} updated for workshop {workshop_id}", 
                    extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_workshop_customer_by_id"})
        return customer_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in update_current_user_workshop_customer_by_id: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_workshop_customer_by_id"})
        raise fetchErrorException

async def delete_customer(
        customer_id: int,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to delete a customer
    '''
    try:
        logger.debug(f"[ADMIN FUNC] Deleting customer with ID {customer_id} by admin user", 
                     extra={"user_id": current_user["user_id"], "endpoint": "delete_customer"})
        result = await db.execute(
            select(models.Customer).filter(models.Customer.customer_id == customer_id)
        )
        db_customer = result.scalar_one_or_none()
        # If customer not found, raise 404
        if db_customer is None:
            logger.error(f"[ADMIN FUNC] Customer with ID {customer_id} not found", 
                         extra={"user_id": current_user["user_id"], "endpoint": "delete_customer"})
            raise notFoundException

        await db.execute(
            delete(models.Customer).where(models.Customer.customer_id == customer_id)
        )
        await db.commit()
        logger.info(f"[ADMIN FUNC] Customer with ID {customer_id} deleted", 
                    extra={"user_id": current_user["user_id"], "endpoint": "delete_customer"})
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in delete_customer: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "delete_customer"})
        raise fetchErrorException

async def delete_current_user_workshop_customer(
    current_user: dict,
    customer_id: int,
    db: AsyncSession
):
    """
    Delete a customer for the current logged-in user's workshop
    """
    try: 
        workshop_id = get_current_user_workshop_id(current_user)

        result = await db.execute(
            select(models.Customer).filter(
                models.Customer.customer_id == customer_id,
                models.Customer.workshop_id == workshop_id
            )
        )
        db_customer = result.scalar_one_or_none()
        if db_customer is None:
            logger.error(f"Customer with ID {customer_id} not found in workshop {workshop_id}", 
                         extra={"user_id": current_user["user_id"], "endpoint": "delete_current_user_workshop_customer"})
            raise notFoundException

        await db.execute(
            delete(models.Customer).where(models.Customer.customer_id == customer_id)
        )
        await db.commit()
        logger.info(f"Customer with ID {customer_id} deleted from workshop {workshop_id}", 
                    extra={"user_id": current_user["user_id"], "endpoint": "delete_current_user_workshop_customer"})
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in delete_current_user_workshop_customer: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "delete_current_user_workshop_customer"})
        raise fetchErrorException

async def assign_customer_to_car(
        customer_id: int,  # Add this parameter
        car_data: schemas.CustomerCarAssign,  # Use CustomerCarAssign instead
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to assign a customer to a car
    '''
    try:
        logger.debug(f"Assigning car ID {car_data.car_id} to customer ID {customer_id}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "assign_customer_to_car"})
        
        # Get current user's workshop ID
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error(f"Current user {current_user['user_id']} has no associated workshop",
                         extra={"user_id": current_user["user_id"], "endpoint": "assign_customer_to_car"})
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        
        # Use async query - filter by both customer_id AND workshop_id
        result = await db.execute(
            select(models.Customer)
            .filter(models.Customer.customer_id == customer_id)
            .filter(models.Customer.workshop_id == workshop_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            logger.error(f"Customer with ID {customer_id} not found", 
                         extra={"user_id": current_user["user_id"], "endpoint": "assign_customer_to_car"})
            raise notFoundException
    
        result = await db.execute(
            select(models.Car).filter(models.Car.car_id == car_data.car_id)
        )
        car = result.scalar_one_or_none()
        if not car:
            logger.error(f"Car with ID {car_data.car_id} not found", 
                         extra={"user_id": current_user["user_id"], "endpoint": "assign_customer_to_car"})
            raise notFoundException
        
        # Create relationship - use models.CustomerCar, not schemas
        customer_car = models.CustomerCar(
            customer_id=customer_id,
            car_id=car_data.car_id,
            license_plate=car_data.license_plate,
            color=car_data.color
        )

        db.add(customer_car)
        await db.commit()
        await db.refresh(customer_car)
        logger.info(f"Assigned car ID {car_data.car_id} to customer ID {customer_id}", 
                    extra={"user_id": current_user["user_id"], "endpoint": "assign_customer_to_car"})
        return customer_car
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in assign_customer_to_car: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "assign_customer_to_car"})
        raise fetchErrorException
    
async def get_cars_by_customer(
        customer_id: int,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to get all cars associated with a customer in the current user's workshop
    '''
    try:
        logger.debug(f"Fetching cars for customer ID {customer_id}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_cars_by_customer"})
        
        # Get current user's workshop ID
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error(f"Current user {current_user['user_id']} has no associated workshop",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_cars_by_customer"})
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        
        # First verify the customer belongs to the user's workshop
        result = await db.execute(
            select(models.Customer)
            .filter(models.Customer.customer_id == customer_id)
            .filter(models.Customer.workshop_id == workshop_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            logger.error(f"Customer with ID {customer_id} not found in workshop {workshop_id}", 
                         extra={"user_id": current_user["user_id"], "endpoint": "get_cars_by_customer"})
            raise notFoundException
        
        # Now get the cars for this customer
        result = await db.execute(
            select(models.Car).join(models.CustomerCar).filter(models.CustomerCar.customer_id == customer_id)
        )
        cars = result.scalars().all()
        logger.info(f"Fetched {len(cars)} cars for customer ID {customer_id}", 
                    extra={"user_id": current_user["user_id"], "endpoint": "get_cars_by_customer"})
        return cars
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in get_cars_by_customer: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "get_cars_by_customer"})
        raise fetchErrorException
    
async def get_customer_full_car_info_by_id(
        customer_id: int,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to get full car information for a customer's cars
    '''
    try:
        logger.debug(f"Fetching full car info for customer ID {customer_id}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_customer_full_car_info_by_id"})
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error(f"Current user {current_user['user_id']} has no associated workshop",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_customer_full_car_info_by_id"})
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        
        # Verify customer belongs to user's workshop
        customer = await db.execute(
            select(models.Customer)
            .filter(models.Customer.customer_id == customer_id)
            .filter(models.Customer.workshop_id == workshop_id)
        )
        customer_obj = customer.scalar_one_or_none()
        if not customer_obj:
            logger.error(f"Customer with ID {customer_id} not found in workshop {workshop_id}", 
                         extra={"user_id": current_user["user_id"], "endpoint": "get_customer_full_car_info_by_id"})
            raise notFoundException
        
        # Fetch full car info
        result = await db.execute(
            select(models.CustomerCar, models.Car)
            .join(models.Car, models.CustomerCar.car_id == models.Car.car_id)
            .filter(models.CustomerCar.customer_id == customer_id)
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
        
        logger.info(f"Fetched {len(customer_cars_with_info)} cars with full info for customer ID {customer_id}", 
                    extra={"user_id": current_user["user_id"], "endpoint": "get_customer_full_car_info_by_id"})
        return customer_cars_with_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in get_customer_full_car_info: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "get_customer_full_car_info_by_id"})
        raise fetchErrorException