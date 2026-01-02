from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from db import models, schemas
from exceptions.exceptions import notFoundException, fetchErrorException
from ..workshops.service import get_current_user_workshop_id
from db import models, schemas
from logger.logger import get_logger

router = APIRouter(tags=["workers"])

logger = get_logger()

# ---------------- BEGIN Current user's info functions ----------------
async def add_worker_to_current_user_workshop(
    current_user: dict,
    worker: schemas.WorkerCreateForWorkshop,
    db: AsyncSession
):
    """
    Add a worker to the current logged-in user's workshop
    """
    try: 
        logger.debug(f"Adding worker to workshop for user: {current_user['user_id']}",
                     extra={"user_id": current_user["user_id"], "endpoint": "add_worker_to_current_user_workshop"})
        # Check if user has a workshop associated (not default workshop_id = 1)
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error("User does not have an associated workshop.")
            raise HTTPException(status_code=400, detail="User does not have an associated workshop.",
                                extra={"user_id": current_user["user_id"], "endpoint": "add_worker_to_current_user_workshop"})

        # Create the worker model and add the values
        create_worker_model = models.Worker(
            first_name=worker.first_name,
            last_name=worker.last_name,
            nickname=worker.nickname,
            phone=worker.phone,
            position=worker.position,
            workshop_id=workshop_id  # Set automatically from user's workshop
        )

        # Add and commit the new worker to the database
        db.add(create_worker_model)
        await db.commit()
        await db.refresh(create_worker_model)
        logger.info(f"Worker added to workshop ID {workshop_id}",
                    extra={"user_id": current_user["user_id"], "endpoint": "add_worker_to_current_user_workshop"})
        return create_worker_model
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in add_worker_to_current_user_workshop: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "add_worker_to_current_user_workshop"})
        raise fetchErrorException

async def get_all_workers_for_current_user_workshop(
        db: AsyncSession, 
        current_user: dict, 
        skip: int = 0, 
        limit: int = 100):
    '''
    Construct a query to get all workers for the current user's workshop
    '''
    try: 
        logger.debug(f"Retrieving workers for user: {current_user["user_id"]}",
                     extra={"user_id": current_user["user_id"], "endpoint": "get_all_workers_for_current_user_workshop"})
        
        # Check if user has a workshop associated (not default workshop_id = 1)
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error("User does not have an associated workshop.")
            raise HTTPException(status_code=400, detail="User does not have an associated workshop.",
                                extra={"user_id": current_user["user_id"], "endpoint": "get_all_workers_for_current_user_workshop"})

        # Query to get all workers for the user's workshop with pagination
        result = await db.execute(
            select(models.Worker)
            .where(models.Worker.workshop_id == workshop_id)
            .offset(skip)
            .limit(limit)
        )
        # Get the query results
        workers = result.scalars().all()
        if workers is None:
            logger.error(f"No workers found for workshop ID {workshop_id}",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_all_workers_for_current_user_workshop"})
            raise notFoundException
        
        logger.info(f"Retrieved {len(workers)} workers for workshop ID {workshop_id}",
                    extra={"user_id": current_user["user_id"], "endpoint": "get_all_workers_for_current_user_workshop"})
        return workers
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_all_workers_for_current_user_workshop: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "get_all_workers_for_current_user_workshop"})
        raise fetchErrorException
    
async def get_worker_by_id(
        worker_id: int,
        current_user: dict,
        db: AsyncSession,
):
    try:
        logger.debug(f"Retrieving worker ID {worker_id} for user: {current_user['user_id']}",
                     extra={"user_id": current_user["user_id"], "endpoint": "get_worker_by_id"})
        
        # Check if user has a workshop associated (not default workshop_id = 1)
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error("User does not have an associated workshop.")
            raise HTTPException(status_code=400, detail="User does not have an associated workshop.",
                                extra={"user_id": current_user["user_id"], "endpoint": "get_worker_by_id"})


        # Query to get the worker by ID within user's workshop 
        result = await db.execute(
            select(models.Worker)
            .filter(models.Worker.workshop_id == workshop_id)
            .filter(models.Worker.worker_id == worker_id)
        )

        # Get the query results
        db_worker = result.scalar_one_or_none()
        if db_worker is None:
            logger.error(f"Worker ID {worker_id} not found in workshop ID {workshop_id}",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_worker_by_id"})
            raise notFoundException
        logger.info(f"Retrieved worker ID {worker_id} for workshop ID {workshop_id}",
                    extra={"user_id": current_user["user_id"], "endpoint": "get_worker_by_id"})
        return db_worker
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error while retrieving worker information: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "get_worker_by_id"})
        raise fetchErrorException
    

async def update_worker_info(
    worker_id: int,
    worker_update: schemas.WorkerUpdate,
    current_user: dict,
    db: AsyncSession
):
    """
    Update a worker's information for the current user's workshop
    """
    try:
        logger.debug(f"Updating worker ID {worker_id} for user: {current_user['user_id']}",
                     extra={"user_id": current_user["user_id"], "endpoint": "update_worker_info"})
        
        # Check if user has a workshop associated (not default workshop_id = 1)
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error("User does not have an associated workshop.")
            raise HTTPException(status_code=400, detail="User does not have an associated workshop.",
                                extra={"user_id": current_user["user_id"], "endpoint": "update_worker_info"})
        
        # Query to get the worker by ID within user's workshop
        result = await db.execute(
            select(models.Worker).where(
                models.Worker.worker_id == worker_id,
                models.Worker.workshop_id == workshop_id
            )
        )
        # Get the query results
        db_worker = result.scalars().first()
        if not db_worker:
            logger.error(f"Worker ID {worker_id} not found in workshop ID {workshop_id}",
                         extra={"user_id": current_user["user_id"], "endpoint": "update_worker_info"})
            raise notFoundException
        
        # Update fields
        update_data = worker_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_worker, field, value)

        await db.commit()
        await db.refresh(db_worker)
        logger.info(f"Updated worker ID {worker_id} for workshop ID {workshop_id}",
                    extra={"user_id": current_user["user_id"], "endpoint": "update_worker_info"})
        return db_worker
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in update_worker_info: {e}",
                        extra={"user_id": current_user["user_id"], "endpoint": "update_worker_info"})
        raise fetchErrorException
    

async def delete_worker_info(
    worker_id: int,
    current_user: dict,
    db: AsyncSession
):
    """
    delete a worker's information for the current user's workshop
    """
    try:
        logger.debug(f"Deleting worker ID {worker_id} for user: {current_user['user_id']}",
                     extra={"user_id": current_user["user_id"], "endpoint": "delete_worker_info"})
        
        # Check if user has a workshop associated (not default workshop_id = 1)
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error("User does not have an associated workshop.")
            raise HTTPException(status_code=400, detail="User does not have an associated workshop.",
                                extra={"user_id": current_user["user_id"], "endpoint": "delete_worker_info"})

        # Query to get the worker by ID within user's workshop
        result = await db.execute(
            select(models.Worker).where(
                models.Worker.worker_id == worker_id,
                models.Worker.workshop_id == workshop_id
            )
        )
        # Get the query results
        db_customer = result.scalars().first()
        if db_customer is None:
            logger.error(f"Worker ID {worker_id} not found in workshop ID {workshop_id}",
                         extra={"user_id": current_user["user_id"], "endpoint": "delete_worker_info"})
            raise notFoundException
        
        # Delete the worker
        await db.execute(
            delete(models.Worker).where(models.Worker.worker_id == worker_id)
        )
        await db.commit()

        logger.info(f"Deleted worker ID {worker_id} from workshop ID {workshop_id}",
                    extra={"user_id": current_user["user_id"], "endpoint": "delete_worker_info"})
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in delete_worker_info: {e}",
                        extra={"user_id": current_user["user_id"], "endpoint": "delete_worker_info"})
        raise fetchErrorException

# ---------------- END Current user's info functions ----------------


