from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from auth.auth import get_current_user, pwd_context, admin_required, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from db import models, schemas
from exceptions.exceptions import notFoundException, fetchErrorException
from db.database import get_db

from ..workshops.service import get_current_user_workshop_id

from db import models, schemas
from db.database import get_db

router = APIRouter(tags=["workers"])


# ---------------- BEGIN Current user's info functions ----------------
async def add_worker_to_current_user_workshop(
    current_user: dict,
    worker: schemas.WorkerCreateForWorkshop,
    db: AsyncSession
):
    """
    Add a worker to the current logged-in user's workshop
    """
    # Validate required fields are not empty
    if not worker.first_name or not worker.first_name.strip():
        raise HTTPException(status_code=422, detail="First name cannot be empty")
    if not worker.last_name or not worker.last_name.strip():
        raise HTTPException(status_code=422, detail="Last name cannot be empty")
    if not worker.position or not worker.position.strip():
        raise HTTPException(status_code=422, detail="Position cannot be empty")
    
    workshop_id = get_current_user_workshop_id(current_user)
    create_worker_model = models.Worker(
        first_name=worker.first_name,
        last_name=worker.last_name,
        nickname=worker.nickname,
        phone=worker.phone,
        position=worker.position,
        workshop_id=workshop_id  # Set automatically from user's workshop
    )

    db.add(create_worker_model)
    await db.commit()
    await db.refresh(create_worker_model)
    return create_worker_model

async def get_all_workers_for_current_user_workshop(
        db: AsyncSession, 
        current_user: dict, 
        skip: int = 0, 
        limit: int = 100):
    '''
    Construct a query to get all workers for the current user's workshop
    '''
    try:
        workshop_id = get_current_user_workshop_id(current_user)
        result = await db.execute(
            select(models.Worker)
            .where(models.Worker.workshop_id == workshop_id)
            .offset(skip)
            .limit(limit)
        )
        workers = result.scalars().all()
        if not workers:
            raise notFoundException
        return workers
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in get_all_workers_for_current_user_workshop: {e}")
        raise fetchErrorException
    
async def get_worker_by_id(
        worker_id: int,
        current_user: dict,
        db: AsyncSession,
):
    try:
        workshop_id = get_current_user_workshop_id(current_user)
        result = await db.execute(
            select(models.Worker)
            .filter(models.Worker.workshop_id == workshop_id)
            .filter(models.Worker.worker_id == worker_id)
        )

        db_worker = result.scalar_one_or_none()
        if db_worker is None:
            raise notFoundException
        return db_worker
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error while retrieving worker information: {e}")
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
        workshop_id = get_current_user_workshop_id(current_user)
        result = await db.execute(
            select(models.Worker).where(
                models.Worker.worker_id == worker_id,
                models.Worker.workshop_id == workshop_id
            )
        )
        db_worker = result.scalars().first()
        if not db_worker:
            raise notFoundException

        update_data = worker_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_worker, field, value)

        await db.commit()
        await db.refresh(db_worker)
        return db_worker
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in update_worker_info: {e}")
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
        workshop_id = get_current_user_workshop_id(current_user)
        result = await db.execute(
            select(models.Worker).where(
                models.Worker.worker_id == worker_id,
                models.Worker.workshop_id == workshop_id
            )
        )

        db_customer = result.scalars().first()
        if db_customer is None:
            raise notFoundException
        await db.execute(
            delete(models.Worker).where(models.Worker.worker_id == worker_id)
        )
        await db.commit()
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in delete_worker_info: {e}")
        raise fetchErrorException

# ---------------- END Current user's info functions ----------------


