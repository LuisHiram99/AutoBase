from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Union
from auth.auth import admin_required, get_current_user, is_admin
from . import service
from ..rate_limiter import limiter

from db import models, schemas, database
from db.database import get_db

router = APIRouter()


# ---------------- All customers endpoints ----------------


@router.post("/customers/", response_model=schemas.Customer)
@limiter.limit("15/minute")
async def create_customer(
    request: Request,
    customer: Union[schemas.CustomerCreate, schemas.CustomerCreateForWorkshop],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    """
    Create a new customer: 
    - If user is admin -> can create customer for any workshop (requires workshop_id)
    - If user is not admin -> customer is created for user's workshop only (no workshop_id needed)
    """
    if not is_admin(current_user):
        # For non-admin users, ensure they're using CustomerCreateForWorkshop schema
        if isinstance(customer, schemas.CustomerCreate):
            raise HTTPException(status_code=400, detail="Non-admin users cannot specify workshop_id")
        return await service.create_current_user_workshop_customer(current_user, customer, db)
    else:
        # For admin users, ensure they're using CustomerCreate schema with workshop_id
        if isinstance(customer, schemas.CustomerCreateForWorkshop):
            raise HTTPException(status_code=400, detail="Admin users must specify workshop_id")
        return await service.create_customer(customer, db, current_user)

@router.get("/customers/", response_model=List[schemas.Customer])
@limiter.limit("15/minute")
async def read_customers(
    request: Request,
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    """
    Get all customers with pagination:
    - If user is admin -> gets all customers
    - If user is not admin -> gets customers for user's workshop only
    """
    if not is_admin(current_user):
        return await service.get_current_user_workshop_customers(current_user, db, skip, limit)
    else:
        return await service.get_all_customers(db, current_user, skip, limit)

@router.get("/customers/{customer_id}", response_model=schemas.Customer)
@limiter.limit("15/minute")
async def read_customer(
    request: Request,
    customer_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(get_current_user)):
    """
    Get a specific customer by ID:
    - If user is admin -> can get any customer
    - If user is not admin -> can get customer only if belongs to user's workshop
    """
    if not is_admin(current_user):
        return await service.get_current_user_workshop_customer_by_id(customer_id, db, current_user)
    else: return await service.get_customer_by_id(customer_id, db, current_user)

@router.patch("/customers/{customer_id}", response_model=schemas.Customer)
@limiter.limit("15/minute")
async def update_customer(
    request: Request,
    customer_id: int, 
    customer_update: schemas.CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    """
    Update a customer's information
    - If user is admin -> can update any customer
    - If user is not admin -> can update customer only if belongs to user's workshop
    """
    if not is_admin(current_user):
        update_data = customer_update.model_dump(exclude_unset=True)
        if "workshop_id" in update_data:
            raise HTTPException(status_code=403, detail="Non-admin users cannot update workshop_id")
        return await service.update_current_user_workshop_customer_by_id(customer_id, customer_update, db, current_user)
    else:
        return await service.update_customer(customer_id, customer_update, db, current_user)

@router.delete("/customers/{customer_id}", response_model=schemas.Customer)
async def delete_customer(
    request: Request, 
    customer_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    """
    Delete a customer
    - If user is admin -> can delete any customer
    - If user is not admin -> can delete customer only if belongs to user's workshop
    """

    if not is_admin(current_user):
        return await service.delete_current_user_workshop_customer(current_user, customer_id, db)
    else:
        return await service.delete_customer(customer_id, db, current_user)


@router.post("/customers/{customer_id}/cars", response_model=schemas.CustomerCarResponse)
@limiter.limit("15/minute")
async def add_car_to_customer(
    request: Request,
    customer_id: int,  # Add customer_id from URL path
    car_data: schemas.CustomerCarAssign,  # Use CustomerCarAssign schema
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    """
    Add a car to a customer's profile
    """
    return await service.assign_customer_to_car(customer_id, car_data, db, current_user)

@router.get("/customers/{customer_id}/cars", response_model=List[schemas.CustomerCarWithCarInfo])
@limiter.limit("15/minute")
async def get_customer_cars(
    request: Request,
    customer_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    """
    Get all cars associated with a customer
    """
    return await service.get_customer_full_car_info_by_id(customer_id, db, current_user)

