from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Annotated
from auth.auth import get_current_user, is_admin
from . import service
from ..rate_limiter import limiter

from db import models, schemas, database
from db.database import get_db

router = APIRouter()

user_dependency = Annotated[dict, Depends(get_current_user)]

@router.post("/customer_car/", response_model=schemas.CustomerCar)
@limiter.limit("15/minute")
async def create_customer_car(
    request: Request,
    customer_car: schemas.CustomerCarCreate, 
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    """
    Create a new customer_car
    """
    if is_admin(current_user):
        return await service.create_customer_car(customer_car, db, current_user)
    else:
        return await service.create_customer_car_for_current_user_workshop(current_user, customer_car, db)

@router.get("/customer_car/", response_model=List[schemas.CustomerCarWithCarInfo])
@limiter.limit("15/minute")
async def read_customers_cars(
    request: Request,
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(get_current_user),
    skip: int = 0, 
    limit: int = 100):
    """
    Get all customers_cars with pagination and car information
    """
    if is_admin(current_user):
        return await service.get_all_customers_cars(db, current_user, skip, limit)
    else:
        return await service.get_customer_cars_for_current_user_workshop(db, current_user, skip, limit)


@router.get("/customer_car/{customer_car_id}", response_model=schemas.CustomerCarWithCarInfo)
@limiter.limit("15/minute")
async def read_customer_car(
    request: Request,
    customer_car_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    """
    Get a specific customer_car by ID with car information
    """
    return await service.get_customer_car_by_id(customer_car_id, db, current_user)

@router.put("/customer_car/{customer_car_id}", response_model=schemas.CustomerCar)
@limiter.limit("15/minute")
async def update_customer_car(
    request: Request,
    customer_car_id: int,
    customer_car_update: schemas.CustomerCarUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    """
    Update an existing customer_car (partial updates allowed)
    """
    return await service.update_customer_car(customer_car_id, customer_car_update, db, current_user)

@router.delete("/customer_car/{customer_car_id}", response_model=schemas.CustomerCar)
@limiter.limit("15/minute")
async def delete_customer_car(
    request: Request,
    customer_car_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    """
    Delete a customer_car
    """
    return await service.delete_customer_car(customer_car_id, db, current_user)
