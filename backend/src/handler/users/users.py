from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Annotated, List
from auth.auth import get_current_user, pwd_context, admin_required
from . import service
from exceptions.exceptions import notAdminException, notFoundException
from ..rate_limiter import limiter

from db import models, schemas, database
from db.database import get_db

router = APIRouter()

user_dependency = Annotated[dict, Depends(get_current_user)]


# ---------------- All user endpoints ----------------

@router.get("/users/", response_model=List[schemas.User], summary="Get all users")
@limiter.limit("15/minute")
async def read_users(
    request: Request,
    user = Depends(admin_required), 
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)):
    """
    Get all users with pagination
    """
    return await service.get_all_users(user, db, skip, limit)

@router.get("/users/{user_id}", response_model=schemas.User, summary="Get user by ID")
@limiter.limit("15/minute")
async def read_user(
    request: Request,
    user_id: int, 
    user = Depends(admin_required), 
    db: AsyncSession = Depends(get_db)):
    """
    Get a specific user by ID
    """
    return await service.get_user_by_id(user, db, user_id)

@router.patch("/users/{user_id}", response_model=schemas.User, summary="Update user by ID")
@limiter.limit("15/minute")
async def patch_user(
    request: Request,
    user_id: int,
    user_update: schemas.UserUpdate,
    current_user = Depends(admin_required),           
    db: AsyncSession = Depends(get_db),):
    """
    Update a user's information
    """
    return await service.update_user(current_user, user_id, db, user_update)

@router.delete("/users/{user_id}", response_model=schemas.User, summary="Delete user by ID")
@limiter.limit("15/minute")
async def delete_user(
    request: Request,
    user_id: int, 
    user =  Depends(admin_required), 
    db: AsyncSession = Depends(get_db)):
    """
    Delete a user
    """
    return await service.delete_user(user, db, user_id)
