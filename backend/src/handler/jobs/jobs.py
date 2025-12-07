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

# ---------------- Jobs endpoints ----------------
@router.post('/jobs/', response_model=schemas.Job)
@limiter.limit("10/minute")
async def create_job(
    request: Request,
    job: schemas.JobCreateForWorkshop,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await service.create_job_for_current_user_workshop(current_user, job, db)

@router.get('/jobs/', response_model=List[schemas.JobWithCarInfo])
@limiter.limit("10/minute")
async def read_jobs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    return await service.get_all_jobs_for_current_user_workshop(db, current_user, skip, limit)

@router.get("/jobs/{job_id}", response_model=schemas.JobWithCarInfo)
@limiter.limit('10/minute')
async def read_job_by_id(
    request: Request,
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    
    return await service.get_job_by_id(job_id, current_user, db)

@router.patch('/jobs/{job_id}', response_model=schemas.Job)
@limiter.limit("10/minute")
async def update_job(
    request: Request,
    job_id: int,
    job_update: schemas.JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await service.update_job_info(job_id, job_update, current_user, db)

@router.delete('/jobs/{job_id}', response_model=dict)
@limiter.limit("10/minute")
async def delete_job(
    request: Request,
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await service.delete_job(job_id, current_user, db)