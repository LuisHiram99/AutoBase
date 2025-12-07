from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from auth.auth import get_current_user, pwd_context, admin_required
from db import models, schemas
from exceptions.exceptions import notFoundException, fetchErrorException
from ..workshops.service import get_current_user_workshop_id

# ---------------- All customers functions ----------------
async def create_customer(
        customer: schemas.CustomerCreate,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to create a new customer
    '''
    try:
        db_customer = models.Customer(**customer.model_dump())

        db.add(db_customer)
        await db.commit()
        await db.refresh(db_customer)
        return db_customer
    except Exception as e:
        print(f"Database error in create_customer: {e}")
        raise fetchErrorException

async def create_current_user_workshop_customer(
    current_user: dict,
    customer: schemas.CustomerCreate,
    db: AsyncSession
):
    """
    Create a customer for the current logged-in user's workshop
    """
    workshop_id = get_current_user_workshop_id(current_user)
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
    return create_customer_model


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
        return result.scalars().all()
    except Exception as e:
        print(f"Database error in get_all_customers: {e}")
        raise fetchErrorException
    
async def get_current_user_workshop_customers(
    current_user: dict,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
):
    """
    Get customers associated with the current logged-in user's workshop
    """
    workshop_id = get_current_user_workshop_id(current_user)
    result = await db.execute(
        select(models.Customer)
        .filter(models.Customer.workshop_id == workshop_id)
        .offset(skip)
        .limit(limit)
    )
    customers = result.scalars().all()
    return customers

async def get_customer_by_id(
        customer_id: int,
        db: AsyncSession, 
        current_user: dict) -> models.Customer:
    '''
    Construct a query to get a customer by ID
    '''
    try:
        result = await db.execute(
            select(models.Customer).filter(models.Customer.customer_id == customer_id)
        )
        # Get customer data
        db_customer = result.scalar_one_or_none()
        # If customer not found, raise 404
        if db_customer is None:
            raise notFoundException
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in get_customer_by_id: {e}")
        raise fetchErrorException
    
async def get_current_user_workshop_customer_by_id(
        customer_id: int, 
        db: AsyncSession, 
        current_user: dict) -> models.Customer:
    """
    Get a specific customer by ID for the current logged-in user's workshop
    """
    try: 
        workshop_id = get_current_user_workshop_id(current_user)
        result = await db.execute(
            select(models.Customer)
            .filter(models.Customer.customer_id == customer_id)
            .filter(models.Customer.workshop_id == workshop_id)
        )
        db_customer = result.scalar_one_or_none()
        # If customer not found or does not belong to user's workshop, raise 404
        if db_customer is None:
            raise notFoundException
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in get_current_user_workshop_customer_by_id: {e}")
        raise fetchErrorException


async def update_customer(
        customer_id: int, 
        customer_update: schemas.CustomerUpdate,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to update a customer's information
    '''
    try:
        customer_data = await get_customer_by_id(customer_id, db, current_user)
            # Prepare update data
        update_data = customer_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(customer_data, key, value)
        await db.commit()
        await db.refresh(customer_data)
        return customer_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in update_customer: {e}")
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
        workshop_id = get_current_user_workshop_id(current_user)
        result = await db.execute(
            select(models.Customer)
            .filter(models.Customer.customer_id == customer_id)
            .filter(models.Customer.workshop_id == workshop_id)
        )
        customer_data = result.scalar_one_or_none()
        # If customer not found or does not belong to user's workshop, raise 404
        if customer_data is None:
            raise notFoundException
        
        update_data = customer_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(customer_data, key, value)

        await db.commit()
        await db.refresh(customer_data)
        return customer_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in update_current_user_workshop_customer_by_id: {e}")
        raise fetchErrorException

async def delete_customer(
        customer_id: int,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to delete a customer
    '''
    try:
        result = await db.execute(
            select(models.Customer).filter(models.Customer.customer_id == customer_id)
        )
        db_customer = result.scalar_one_or_none()
        # If customer not found, raise 404
        if db_customer is None:
            raise notFoundException

        await db.execute(
            delete(models.Customer).where(models.Customer.customer_id == customer_id)
        )
        await db.commit()
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in delete_customer: {e}")
        raise fetchErrorException

async def delete_current_user_workshop_customer(
    current_user: dict,
    customer_id: int,
    db: AsyncSession
):
    """
    Delete a customer for the current logged-in user's workshop
    """
    workshop_id = get_current_user_workshop_id(current_user)

    result = await db.execute(
        select(models.Customer).filter(
            models.Customer.customer_id == customer_id,
            models.Customer.workshop_id == workshop_id
        )
    )
    db_customer = result.scalar_one_or_none()
    if db_customer is None:
        raise notFoundException

    await db.execute(
        delete(models.Customer).where(models.Customer.customer_id == customer_id)
    )
    await db.commit()
    return db_customer


async def assign_customer_to_car(
        customer_id: int,  # Add this parameter
        car_data: schemas.CustomerCarAssign,  # Use CustomerCarAssign instead
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to assign a customer to a car
    '''
    try:
        # Use async query
        result = await db.execute(
            select(models.Customer).filter(models.Customer.customer_id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            raise notFoundException
    
        result = await db.execute(
            select(models.Car).filter(models.Car.car_id == car_data.car_id)
        )
        car = result.scalar_one_or_none()
        if not car:
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
        return customer_car
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in assign_customer_to_car: {e}")
        raise fetchErrorException
    
async def get_cars_by_customer(
        customer_id: int,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to get all cars associated with a customer
    '''
    try:
        result = await db.execute(
            select(models.Car).join(models.CustomerCar).filter(models.CustomerCar.customer_id == customer_id)
        )
        cars = result.scalars().all()
        return cars
    except Exception as e:
        print(f"Database error in get_cars_by_customer: {e}")
        raise fetchErrorException
    
async def get_customer_full_car_info_by_id(
        customer_id: int,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to get full car information for a customer's cars
    '''
    try:
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
        
        return customer_cars_with_info
    except Exception as e:
        print(f"Database error in get_customer_full_car_info: {e}")
        raise fetchErrorException