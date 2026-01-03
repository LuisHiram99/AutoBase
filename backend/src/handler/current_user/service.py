from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from auth.auth import pwd_context, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from db import models, schemas
from logger.logger import get_logger


logger = get_logger()
# ---------------- Current user endpoints ----------------
async def get_current_user_info(
    current_user: dict, 
    db: AsyncSession):
    """
    Get current logged-in user information
    """
    try:
        logger.debug(f"Fetching info for user {current_user['user_id']}")
        # Look up the user in the database
        result = await db.execute(
            select(models.User).where(models.User.user_id == current_user["user_id"])
        )
        # query result
        user = result.scalars().first()
        # If user not found, raise 404
        if not user:
            logger.error(f"User {current_user['user_id']} tried to access info but was not found in DB", 
                         extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_info"})
            raise HTTPException(status_code=404, detail="User not found")
        logger.info(f"User {current_user['user_id']} fetched their info successfully")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_current_user_info: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching user info: {str(e)}")
    
async def patch_current_user_info(
    user_update: schemas.CurrentUserUpdate,
    current_user: dict,
    db: AsyncSession):
    """
    Update current logged-in user information
    """
    try:
        logger.debug(f"Patching user {current_user['user_id']}")
        # Look up the user in the database
        result = await db.execute(
            select(models.User).where(models.User.user_id == current_user["user_id"])
        )
        # query result
        db_user = result.scalars().first()
        # If user not found, raise 404
        if not db_user:
            logger.error(f"User {current_user['user_id']} tried to patch info but was not found in DB")
            raise HTTPException(status_code=404, detail="User not found")
        # Update fields
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        # Commit changes to database
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"User {current_user['user_id']} updated their info")
        return db_user  
    except HTTPException:
        raise  
    except Exception as e:
        logger.critical(f"Database error in patch_current_user_info: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "patch_current_user_info"})
        raise HTTPException(status_code=500, detail="Error updating user info")
    
async def update_current_user_password(
    password_update: schemas.CurrentUserPassword,
    current_user: dict,
    db: AsyncSession):
    """
    Update current logged-in user's password
    """
    try:
        logger.debug(f"Updating password for user {current_user['user_id']}")
        # Look up the user in the database
        result = await db.execute(
            select(models.User).where(models.User.user_id == current_user["user_id"])
        )
        # query result
        db_user = result.scalars().first()
        # If user not found, raise 404
        if not db_user:
            logger.error(f"User {current_user['user_id']} tried to update password but was not found in DB",
                         extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_password"})
            raise HTTPException(status_code=404, detail="User not found")
        # Verify old password
        if not pwd_context.verify(password_update.old_password, db_user.hashed_password):
            logger.error(f"User {current_user['user_id']} provided incorrect old password",
                         extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_password"})
            raise HTTPException(status_code=400, detail="Old password is incorrect")
        
        # Hash and update to new password
        hashed_password = pwd_context.hash(password_update.new_password)
        db_user.hashed_password = hashed_password

        # Increment token version to invalidate all existing tokens
        db_user.token_version += 1
        logger.info(f"User {current_user['user_id']} updated their password", 
                    extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_password"})
        # Commit changes to database
        await db.commit()
        await db.refresh(db_user)

        # Create new access token
        new_token = create_access_token(
        db_user.email, 
        db_user.user_id,
        db_user.token_version,
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
        logger.info(f"New access token issued for user {current_user['user_id']} after password change")
        return {
            "message": "Password updated successfully",
            "access_token": new_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise  
    except Exception as e:
        logger.critical(f"Database error in update_current_user_password: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_password"})
        raise HTTPException(status_code=500, detail="Error updating password")

async def delete_current_user_account(
    current_user: dict,
    db: AsyncSession):
    """
    Delete current logged-in user's account
    """
    try:
        logger.debug(f"Deleting account for user {current_user['user_id']}")
        # Look up the user in the database
        result = await db.execute(
            select(models.User).where(models.User.user_id == current_user["user_id"])
        )
        # query result
        db_user = result.scalars().first()
        # If user not found, raise 404
        if not db_user:
            logger.error(f"User {current_user['user_id']} tried to delete account but was not found in DB",
                           extra={"user_id": current_user["user_id"], "endpoint": "delete_current_user_account"})
            raise HTTPException(status_code=404, detail="User not found")
        # Delete the user
        await db.delete(db_user)
        await db.commit()
        logger.info(f"User {current_user['user_id']} deleted their account",
                    extra={"user_id": current_user["user_id"], "endpoint": "delete_current_user_account"})
        return db_user
    except HTTPException:
        raise  
    except Exception as e:
        logger.critical(f"Database error in delete_current_user_account: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "delete_current_user_account"})
        raise HTTPException(status_code=500, detail="Error deleting user account")
# ---------------- End of current user's info endpoints ----------------


