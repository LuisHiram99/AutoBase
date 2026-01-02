from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from auth.auth import get_current_user, pwd_context
from db import models, schemas
from exceptions.exceptions import notFoundException, fetchErrorException
from logger.logger import get_logger

logger = get_logger()


# ---------------- All user functions [ADMIN FUNCTIONS] ----------------
async def get_all_users(current_user: dict, db: AsyncSession, skip: int = 0, limit: int = 100):
    '''
    Construct a query to get all users with pagination
    '''
    try:
        logger.debug(f"[ADMIN FUNC] Getting all users.",
                     extra={"user_id": current_user["user_id"], "endpoint": "get_all_users"})
        result = await db.execute(
            select(models.User).offset(skip).limit(limit)
        )
        users = result.scalars().all()
        logger.info(f"[ADMIN FUNC] Retrieved {len(users)} users.")                        
        return users
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_all_users_query: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "get_all_users"})
        raise fetchErrorException
    

async def get_user_by_id(current_user: dict, db: AsyncSession, user_id: int):
    '''
    Construct a query to get a user by ID
    '''
    try:
        logger.debug(f"[ADMIN FUNC] Getting user by ID: {user_id}.")
        result = await db.execute(
            select(models.User).filter(models.User.user_id == user_id)
        )
        # Get user data
        db_user = result.scalar_one_or_none()
        # If user not found, raise 404
        if db_user is None:
            logger.error(f"[ADMIN FUNC] User with ID {user_id} not found.",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_user_by_id"})
            raise notFoundException
        logger.info(f"[ADMIN FUNC] Retrieved user with ID {user_id}.")
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_user_by_id_query: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "get_user_by_id"})  
        raise fetchErrorException

async def update_user(current_user: dict, user_id: int, db: AsyncSession, user_update: schemas.UserUpdate):
    '''
    Construct a query to update a user's information
    '''
    try:
        logger.debug(f"[ADMIN FUNC] Updating user with ID {user_id}")
        # Get the user data to be updated
        user_data = await get_user_by_id(current_user, db, user_id)
        # Prepare update data
        update_data = user_update.model_dump(exclude_unset=True)
        # handle password hashing specially
        if "password" in update_data:
            plain = update_data.pop("password")
            if plain:
                user_data.hashed_password = pwd_context.hash(plain)
        # Update other fields
        for field, value in update_data.items():
            setattr(user_data, field, value)
        # Commit the transaction
        await db.commit()
        await db.refresh(user_data)
        logger.info(f"[ADMIN FUNC] User with ID {user_id} updated successfully")
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in update_user: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "update_user"})
        raise fetchErrorException
    
async def delete_user(current_user: dict, db: AsyncSession, user_id: int):
    '''
    Construct a query to delete a user
    '''
    try:
        logger.debug(f"[ADMIN FUNC] Deleting user with ID {user_id}")
        # Get the user to be deleted
        result = await db.execute(
            select(models.User).filter(models.User.user_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        # If user not found, raise 404
        if db_user is None:
            logger.error(f"[ADMIN FUNC] User with ID {user_id} not found for deletion.",
                         extra={"user_id": current_user["user_id"], "endpoint": "delete_user"})
            raise notFoundException

        # Delete the user
        await db.execute(
            delete(models.User).where(models.User.user_id == user_id)
        )
        # Commit the transaction
        await db.commit()
        logger.info(f"[ADMIN FUNC] User with ID {user_id} deleted successfully")
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in delete_user: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "delete_user"})
        raise fetchErrorException