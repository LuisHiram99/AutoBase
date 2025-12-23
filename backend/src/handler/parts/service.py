from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from auth.auth import get_current_user, pwd_context, admin_required
from db import models, schemas
from exceptions.exceptions import notFoundException, fetchErrorException

async def create_part(part: schemas.PartCreate, db: AsyncSession, current_user: dict):
    '''
    Construct a query to create a new partasdsa
    '''
    try:
        db_part = models.Part(**part.model_dump())
        # Check for empty required fields
        if not db_part.part_name or not db_part.part_name.strip():
            raise HTTPException(status_code=422, detail="Part name cannot be empty")
        if not db_part.brand or not db_part.brand.strip():
            raise HTTPException(status_code=422, detail="Brand cannot be empty")
        
        # check for valid lenghth
        if len(db_part.part_name) > 100:
            raise HTTPException(status_code=422, detail="Part name exceeds maximum length of 100 characters")
        if len(db_part.brand) > 100:
            raise HTTPException(status_code=422, detail="Brand exceeds maximum length of 100 characters")
        if db_part.description and len(db_part.description) > 255:
            raise HTTPException(status_code=422, detail="Description exceeds maximum length of 255 characters")
        if db_part.category and len(db_part.category) > 100:
            raise HTTPException(status_code=422, detail="Category exceeds maximum length of 100 characters")

        db.add(db_part)
        await db.commit()
        await db.refresh(db_part)
        return db_part
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in create_part: {e}")
        raise fetchErrorException
    
async def get_all_parts(current_user: dict, db: AsyncSession, skip: int = 0, limit: int = 100):
    '''
    Construct a query to get all parts with pagination
    '''
    try:
        result = await db.execute(
            select(models.Part).offset(skip).limit(limit)
        )
        parts = result.scalars().all()
        return parts
    except:
        raise fetchErrorException
    
async def get_part_by_id(current_user: dict, db: AsyncSession, part_id: int):
    '''
    Construct a query to get a part by ID
    '''
    try:
        result = await db.execute(
            select(models.Part).filter(models.Part.part_id == part_id)
        )
        # Getting the part data
        db_part = result.scalar_one_or_none()
        # If part not found, raise 404
        if db_part is None:
            raise notFoundException
        return db_part
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in get_part_by_id: {e}")
        raise fetchErrorException
    
async def update_part(current_user: dict, part_id: int, db: AsyncSession, part_update: schemas.PartUpdate):
    '''
    Construct a query to update a part's information
    '''
    try:
        result = await db.execute(
            select(models.Part).filter(models.Part.part_id == part_id)
        )
        db_part = result.scalar_one_or_none()
        if db_part is None:
            raise notFoundException
        update_data = part_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_part, key, value)
        db.add(db_part)
        await db.commit()
        await db.refresh(db_part)
        return db_part
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in update_part: {e}")
        raise fetchErrorException
    
async def delete_part(current_user: dict, part_id: int, db: AsyncSession):
    '''
    Construct a query to delete a part
    '''
    try:
        result = await db.execute(
            select(models.Part).filter(models.Part.part_id == part_id)
        )
        db_part = result.scalar_one_or_none()
        if db_part is None:
            raise notFoundException
        await db.delete(db_part)
        await db.commit()
        return db_part
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in delete_part: {e}")
