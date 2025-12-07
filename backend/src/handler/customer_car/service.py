from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from handler.workshops.service import get_current_user_workshop_id
from db import models, schemas
from exceptions.exceptions import notFoundException, fetchErrorException


# ---------------- All customer_car functions ----------------
async def create_customer_car_for_current_user_workshop(
    current_user: dict,
    customer_car: schemas.CustomerCarCreate,
    db: AsyncSession
):  
    """
    Create a customer_car for the current logged-in user's workshop
    """
    customer_res = await db.execute(
        select(models.Customer)
        .where(models.Customer.customer_id == customer_car.customer_id)
        .where(models.Customer.workshop_id == get_current_user_workshop_id(current_user))
    )
    if customer_res.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Customer not found in your workshop")

    create_customer_car_model = models.CustomerCar(
        customer_id=customer_car.customer_id,
        car_id=customer_car.car_id,
        license_plate=customer_car.license_plate,
        color=customer_car.color
    )

    db.add(create_customer_car_model)
    await db.commit()
    await db.refresh(create_customer_car_model)
    return create_customer_car_model

async def create_customer_car(
        customer_car: schemas.CustomerCarCreate,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to create a new customer_car
    '''
    try:
        # Check if customer exist in db
        customer_res = await db.execute(select(models.Customer).where(models.Customer.customer_id == customer_car.customer_id))
        if customer_res.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Check if car exist in db
        car_res = await db.execute(select(models.Car).where(models.Car.car_id == customer_car.car_id))
        if car_res.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Car not found")

        db_customer_car = models.CustomerCar(**customer_car.model_dump())

        db.add(db_customer_car)
        await db.commit()
        await db.refresh(db_customer_car)
        return db_customer_car
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in create_customer_car: {e}")
        raise fetchErrorException
    
async def get_all_customers_cars(
        db: AsyncSession, 
        current_user: dict, 
        skip: int = 0, 
        limit: int = 100):
    '''
    Construct a query to get all customers_cars with car information
    '''
    try:
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
        
        return customer_cars_with_info
    except Exception as e:
        print(f"Database error in get_all_customers_cars: {e}")
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
    workshop_id = get_current_user_workshop_id(current_user)
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
    
    return customer_cars_with_info
    
async def get_customer_car_by_id(
        customer_car_id: int,
        db: AsyncSession, 
        current_user: dict):
    '''
    Construct a query to get a customer_car by ID with car information
    '''
    try:
        result = await db.execute(
            select(models.CustomerCar, models.Car)
            .join(models.Car, models.CustomerCar.car_id == models.Car.car_id)
            .where(models.CustomerCar.customer_car_id == customer_car_id)
        )
        # Get customer_car data
        customer_car_data = result.first()
        # If customer_car not found, raise 404
        if customer_car_data is None:
            raise notFoundException
        
        customer_car, car = customer_car_data
        
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
        print(f"Database error in get_customer_car_by_id: {e}")
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
        customer_car_data = await get_customer_car_by_id(customer_car_id, db, current_user)
            # Prepare update data
        update_data = customer_car_update.model_dump(exclude_unset=True)

        if "customer_id" in update_data:
            customer_res = await db.execute(select(models.Customer).where(models.Customer.customer_id == update_data["customer_id"]))
            if customer_res.scalar_one_or_none() is None:
                raise HTTPException(status_code=404, detail="Customer not found")

        if "car_id" in update_data:
            car_res = await db.execute(select(models.Car).where(models.Car.car_id == update_data["car_id"]))
            if car_res.scalar_one_or_none() is None:
                raise HTTPException(status_code=404, detail="Car not found")

        # Update other fields
        for field, value in update_data.items():
            setattr(customer_car_data, field, value)
        # Commit the transaction
        await db.commit()
        await db.refresh(customer_car_data)
        return customer_car_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in update_customer_car: {e}")
        raise fetchErrorException
    
async def delete_customer_car(
        customer_car_id: int,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to delete a customer_car
    '''
    try:
        customer_car_data = await get_customer_car_by_id(customer_car_id, db, current_user)

        await db.execute(
            delete(models.CustomerCar).where(models.CustomerCar.customer_car_id == customer_car_id)
        )
        await db.commit()
        return customer_car_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in delete_customer_car: {e}")
        raise fetchErrorException