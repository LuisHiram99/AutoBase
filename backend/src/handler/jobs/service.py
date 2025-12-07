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

# ---------------- BEGIN Jobs info functions ----------------
async def create_job_for_current_user_workshop(
    current_user: dict,
    job: schemas.JobCreateForWorkshop,
    db: AsyncSession
):
    """
    Create a job for the current logged-in user's workshop
    """
    workshop_id = get_current_user_workshop_id(current_user)
    
    # Validate that customer_car exists and belongs to a customer in the user's workshop
    result = await db.execute(
        select(models.CustomerCar, models.Customer)
        .join(models.Customer, models.CustomerCar.customer_id == models.Customer.customer_id)
        .where(models.CustomerCar.customer_car_id == job.customer_car_id)
        .where(models.Customer.workshop_id == workshop_id)
    )
    customer_car_data = result.first()
    
    if not customer_car_data:
        raise HTTPException(
            status_code=404, 
            detail="Customer car not found in your workshop"
        )
    
    create_job_model = models.Job(
        customer_car_id=job.customer_car_id,
        invoice=job.invoice,
        service_description=job.service_description,
        start_date=job.start_date,
        end_date=job.end_date,
        status=job.status,
        workshop_id=workshop_id  # Set automatically from user's workshop
    )

    db.add(create_job_model)
    await db.commit()
    await db.refresh(create_job_model)
    return create_job_model

async def get_all_jobs_for_current_user_workshop(
        db: AsyncSession, 
        current_user: dict, 
        skip: int = 0, 
        limit: int = 100):
    '''
    Construct a query to get all jobs for the current user's workshop with car information
    '''
    try:
        workshop_id = get_current_user_workshop_id(current_user)
        result = await db.execute(
            select(
                models.Job,
                models.Car,
                models.CustomerCar
            )
            .join(models.CustomerCar, models.Job.customer_car_id == models.CustomerCar.customer_car_id)
            .join(models.Car, models.CustomerCar.car_id == models.Car.car_id)
            .where(models.Job.workshop_id == workshop_id)
            .offset(skip)
            .limit(limit)
        )
        jobs_data = result.all()
        
        if not jobs_data:
            return []
        
        # Build response with car information
        jobs_with_car_info = [
            schemas.JobWithCarInfo(
                job_id=job.job_id,
                invoice=job.invoice,
                service_description=job.service_description,
                start_date=job.start_date,
                end_date=job.end_date,
                status=job.status,
                workshop_id=job.workshop_id,
                customer_car_id=job.customer_car_id,
                car_brand=car.brand,
                car_model=car.model,
                car_year=car.year,
                license_plate=customer_car.license_plate,
                car_color=customer_car.color
            )
            for job, car, customer_car in jobs_data
        ]
        
        return jobs_with_car_info
    except Exception as e:
        print(f"Database error in get_all_jobs_for_current_user_workshop: {e}")
        raise fetchErrorException
    

async def get_job_by_id(
        job_id: int,
        current_user: dict,
        db: AsyncSession,
):
    try:
        workshop_id = get_current_user_workshop_id(current_user)
        result = await db.execute(
            select(
                models.Job,
                models.Car,
                models.CustomerCar
            )
            .join(models.CustomerCar, models.Job.customer_car_id == models.CustomerCar.customer_car_id)
            .join(models.Car, models.CustomerCar.car_id == models.Car.car_id)
            .where(models.Job.workshop_id == workshop_id)
            .where(models.Job.job_id == job_id)
        )

        job_data = result.first()
        if job_data is None:
            raise notFoundException
        
        job, car, customer_car = job_data
        
        # Build response with car information
        return schemas.JobWithCarInfo(
            job_id=job.job_id,
            invoice=job.invoice,
            service_description=job.service_description,
            start_date=job.start_date,
            end_date=job.end_date,
            status=job.status,
            workshop_id=job.workshop_id,
            customer_car_id=job.customer_car_id,
            car_brand=car.brand,
            car_model=car.model,
            car_year=car.year,
            license_plate=customer_car.license_plate,
            car_color=customer_car.color
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error while retrieving job information: {e}")
        raise fetchErrorException

async def update_job_info(
    job_id: int,
    job_update: schemas.JobUpdate,
    current_user: dict,
    db: AsyncSession
):
    """
    Update a job's information for the current user's workshop
    """
    try:
        workshop_id = get_current_user_workshop_id(current_user)
        result = await db.execute(
            select(models.Job).where(
                models.Job.job_id == job_id,
                models.Job.workshop_id == workshop_id
            )
        )
        db_job = result.scalars().first()
        if not db_job:
            raise notFoundException  # Don't pass message if it's HTTPException
        
        update_data = job_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_job, field, value)

        await db.commit()
        await db.refresh(db_job)
        return db_job  # Return just db_job, not tuple
    except HTTPException:
        raise  # Let HTTPExceptions propagate
    except Exception as e:
        print(f"Database error in update_job_info: {e}")
        raise fetchErrorException
    
async def delete_job(
    job_id: int,
    current_user: dict,
    db: AsyncSession
):
    """
    Delete a job for the current user's workshop
    """
    try:
        workshop_id = get_current_user_workshop_id(current_user)
        result = await db.execute(
            select(models.Job).where(
                models.Job.job_id == job_id,
                models.Job.workshop_id == workshop_id
            )
        )
        db_job = result.scalars().first()
        if not db_job:
            raise notFoundException  # Don't pass message if it's HTTPException
        
        await db.delete(db_job)
        await db.commit()
        return {"message": "Job deleted successfully", "job_id": job_id}
    except HTTPException:
        raise  # Let HTTPExceptions propagate
    except Exception as e:
        print(f"Database error in delete_job: {e}")
        raise fetchErrorException