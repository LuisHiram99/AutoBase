from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Annotated
from auth.auth import get_current_user, admin_required, pwd_context
from auth.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from . import service
from ..rate_limiter import limiter



from db import models, schemas
from db.database import get_db

router = APIRouter()

# ---------------- Workers endpoints ----------------
@router.post('/workers/', response_model=schemas.Worker)
@limiter.limit("15/minute")
async def create_worker(
    request: Request,
    worker: schemas.WorkerCreateForWorkshop,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await service.add_worker_to_current_user_workshop(current_user, worker, db)

@router.get('/workers/', response_model=List[schemas.Worker])
@limiter.limit("15/minute")
async def read_workers(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    return await service.get_all_workers_for_current_user_workshop(db, current_user, skip, limit)

@router.get("/workers/{worker_id}", response_model=schemas.Worker)
@limiter.limit('15/minute')
async def read_worker_by_id(
    request: Request,
    worker_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    
    return await service.get_worker_by_id(worker_id, current_user, db)



@router.patch('/workers/{worker_id}', response_model=schemas.Worker)
@limiter.limit("15/minute")
async def update_worker(
    request: Request,
    worker_id: int,
    worker_update: schemas.WorkerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await service.update_worker_info(worker_id, worker_update, current_user, db)

@router.delete('/workers/{worker_id}', response_model=schemas.Worker)
@limiter.limit("15/minute")
async def delete_worker(
    request: Request,
    worker_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await service.delete_worker_info(worker_id, current_user, db)

# ---------------- End of workers endpoints ----------------