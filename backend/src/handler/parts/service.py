from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from logger.logger import get_logger
from db import models, schemas
from exceptions.exceptions import notFoundException, fetchErrorException

logger = get_logger()

async def create_part(part: schemas.PartCreate, db: AsyncSession, current_user: dict):
    '''
    Construct a query to create a new partasdsa
    '''
    try:
        logger.debug(f"Attempting to create a new part: {part.part_name} by user {current_user['user_id']}")
        # Create Part instance
        db_part = models.Part(**part.model_dump())
        # Add part to the session
        db.add(db_part)
        # Commit changes to database
        await db.commit()
        await db.refresh(db_part)
        logger.info(f"Part {part.part_name} created successfully with ID {db_part.part_id}")
        return db_part
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in create_part: {e}",
                        extra={"user_id": current_user['user_id'], "endpoint": "create_part"})
        raise fetchErrorException
    
async def get_all_parts(current_user: dict, db: AsyncSession, skip: int = 0, limit: int = 100):
    '''
    Construct a query to get all parts with pagination
    '''
    try:
        logger.debug(f"Fetching parts for user {current_user['user_id']} with skip={skip} and limit={limit}")
        result = await db.execute(
            select(models.Part).offset(skip).limit(limit)
        )
        parts = result.scalars().all()  
        return parts
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_all_parts: {e}",
                        extra={"user_id": current_user['user_id'], "endpoint": "get_all_parts"})
        raise fetchErrorException
    
async def get_part_by_id(current_user: dict, db: AsyncSession, part_id: int):
    '''
    Construct a query to get a part by ID
    '''
    try:
        logger.debug(f"Fetching part with ID: {part_id} for user {current_user['user_id']}")

        # Fetch the part by ID
        result = await db.execute(
            select(models.Part).filter(models.Part.part_id == part_id)
        )
        # Getting the part data
        db_part = result.scalar_one_or_none()
        # If part not found, raise 404
        if db_part is None:
            logger.error(f"Part with ID {part_id} not found",
                         extra={"user_id": current_user['user_id'], "endpoint": "get_part_by_id"})
            raise notFoundException
        
        logger.info(f"Part with ID {part_id} fetched successfully by user {current_user['user_id']}")
        return db_part
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_part_by_id: {e}",
                        extra={"user_id": current_user['user_id'], "endpoint": "get_part_by_id"})
        raise fetchErrorException
    
async def update_part(current_user: dict, part_id: int, db: AsyncSession, part_update: schemas.PartUpdate):
    '''
    Construct a query to update a part's information
    '''
    try:
        logger.debug(f"Attempting to update part with ID: {part_id} by user {current_user['user_id']}")
        # Fetch the part to be updated
        result = await db.execute(
            select(models.Part).filter(models.Part.part_id == part_id)
        )
        db_part = result.scalar_one_or_none()
        # If part not found, raise 404
        if db_part is None:
            logger.error(f"Part with ID {part_id} not found for update",
                         extra={"user_id": current_user['user_id'], "endpoint": "update_part"})
            raise notFoundException
        # Update fields
        update_data = part_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_part, key, value)
        db.add(db_part)
        # Commit changes to database
        await db.commit()
        await db.refresh(db_part)
        logger.info(f"Part with ID {part_id} updated successfully")
        return db_part
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in update_part: {e}",
                        extra={"user_id": current_user['user_id'], "endpoint": "update_part"})
        raise fetchErrorException
    
async def delete_part(current_user: dict, part_id: int, db: AsyncSession):
    '''
    Construct a query to delete a part
    '''
    try:
        logger.debug(f"Attempting to delete part with ID: {part_id}")
        # Fetch the part to be deleted
        result = await db.execute(
            select(models.Part).filter(models.Part.part_id == part_id)
        )
        db_part = result.scalar_one_or_none()
        # If part not found, raise 404
        if db_part is None:
            logger.error(f"Part with ID {part_id} not found for deletion",
                         extra={"user_id": current_user['user_id'], "endpoint": "delete_part"})
            raise notFoundException
        # Commit changes to database
        await db.delete(db_part)
        await db.commit()
        logger.info(f"Part with ID {part_id} deleted successfully")
        return db_part
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in delete_part: {e}",
                        extra={"user_id": current_user['user_id'], "endpoint": "delete_part"})
        raise fetchErrorException
