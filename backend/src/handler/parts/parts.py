from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Annotated
from auth.auth import get_current_user, is_admin, get_current_user
from . import service
from ..rate_limiter import limiter

from db import models, schemas, database
from db.database import get_db

router = APIRouter()

user_dependency = Annotated[dict, Depends(get_current_user)]

# ---------------- All parts endpointsasdasd ----------------
@router.post("/parts/", response_model=schemas.Part)
@limiter.limit("15/minute")
async def create_part(
    request: Request,
    part: schemas.PartCreate, 
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """
    Create a new part
    """
    # Await the async service function
    return await service.create_part(part, db, current_user)

@router.get("/parts/", response_model=List[schemas.Part])
@limiter.limit("15/minute")
async def read_parts(
    request: Request,
    current_user: dict = Depends(get_current_user), 
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)):
    """
    Get all parts with pagination
    """
    return await service.get_all_parts(current_user, db, skip, limit)

@router.get("/parts/{part_id}", response_model=schemas.Part)
@limiter.limit("15/minute")
async def read_part(
    request: Request,
    part_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """
    Get a part by ID
    """
    return await service.get_part_by_id(current_user, db, part_id)

@router.patch("/parts/{part_id}", response_model=schemas.Part)
@limiter.limit("15/minute")
async def update_part(
    request: Request,
    part_id: int,
    part_update: schemas.PartUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """
    Update a part's information
    """
    return await service.update_part(current_user, part_id, db, part_update)

@router.delete("/parts/{part_id}", response_model=schemas.Part)
@limiter.limit("15/minute")
async def delete_part(
    request: Request,
    part_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """
    Delete a part by ID
    """
    return await service.delete_part(current_user, part_id, db)
