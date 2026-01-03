from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db import models, schemas
from exceptions.exceptions import fetchErrorException
from ..workshops.service import get_current_user_workshop_id
from db import models, schemas
from logger.logger import get_logger

logger = get_logger()

# ---------------- BEGIN Jobs info functions ----------------
async def create_job_for_current_user_workshop(
    current_user: dict,
    job: schemas.JobCreateForWorkshop,
    db: AsyncSession
):
    """
    Create a job for the current logged-in user's workshop
    """
    try:
        logger.debug(f"Attempting to create job for workshop by user ID: {current_user['user_id']}")
        # Get the workshop ID associated with the current user
        workshop_id = get_current_user_workshop_id(current_user)
        # If user has no workshop, raise error
        if workshop_id == 1:
            logger.error("User does not have an associated workshop.",
                         extra={"user_id": current_user['user_id'], "endpoint": "delete_job"})
            raise HTTPException(status_code=400, detail="User does not have an associated workshop.")

        # Validate that customer_car exists and belongs to a customer in the user's workshop
        result = await db.execute(
            select(models.CustomerCar, models.Customer)
            .join(models.Customer, models.CustomerCar.customer_id == models.Customer.customer_id)
            .where(models.CustomerCar.customer_car_id == job.customer_car_id)
            .where(models.Customer.workshop_id == workshop_id)
        )
        customer_car_data = result.first()
        
        if not customer_car_data:
            logger.error(f"Customer car ID {job.customer_car_id} not found in workshop ID {workshop_id}",
                         extra={"user_id": current_user['user_id'], "endpoint": "create_job_for_current_user_workshop"})
            raise HTTPException(
                status_code=404, 
                detail="Customer car not found in your workshop"
            )
        # Create the job
        create_job_model = models.Job(
            customer_car_id=job.customer_car_id,
            invoice=job.invoice,
            service_description=job.service_description,
            start_date=job.start_date,
            end_date=job.end_date,
            status=job.status,
            workshop_id=workshop_id  
        )
        # Add and commit the new job to the database
        db.add(create_job_model)
        await db.commit()
        await db.refresh(create_job_model)
        logger.info(f"Successfully created job ID {create_job_model.job_id} in workshop ID {workshop_id}",
                    extra={"user_id": current_user['user_id'], "endpoint": "create_job_for_current_user_workshop"})
        return create_job_model
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in create_job_for_current_user_workshop: {e}",
                        extra={"user_id": current_user['user_id'], "endpoint": "create_job_for_current_user_workshop"})
        raise fetchErrorException

async def get_all_jobs_for_current_user_workshop(
        db: AsyncSession, 
        current_user: dict, 
        skip: int = 0, 
        limit: int = 100):
    '''
    Construct a query to get all jobs for the current user's workshop with car information
    '''
    try:
        logger.debug(f"Attempting to retrieve all jobs for workshop by user ID: {current_user['user_id']}")
        # Get the workshop ID associated with the current user
        workshop_id = get_current_user_workshop_id(current_user)
        # If user has no workshop, raise error
        if workshop_id == 1:
            logger.error("User does not have an associated workshop.",
                         extra={"user_id": current_user['user_id'], "endpoint": "delete_job"})
            raise HTTPException(status_code=400, detail="User does not have an associated workshop.") 
        
        # Query to get jobs with car information
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
        # Query result
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
        logger.info(f"Successfully retrieved {len(jobs_with_car_info)} jobs for workshop ID {workshop_id}",
                    extra={"user_id": current_user['user_id'], "endpoint": "get_all_jobs_for_current_user_workshop"})
        return jobs_with_car_info
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_all_jobs_for_current_user_workshop: {e}",
                        extra={"user_id": current_user['user_id'], "endpoint": "get_all_jobs_for_current_user_workshop"})
        raise fetchErrorException
    

async def get_job_by_id(
        job_id: int,
        current_user: dict,
        db: AsyncSession,
):
    """
    Get a job by ID for the current user's workshop
    """
    try:
        logger.debug(f"Attempting to retrieve job with ID: {job_id} by user ID: {current_user['user_id']}")
        # Get the workshop ID associated with the current user
        workshop_id = get_current_user_workshop_id(current_user)
        # If user has no workshop, raise error
        if workshop_id == 1:
            logger.error("User does not have an associated workshop.",
                         extra={"user_id": current_user['user_id'], "endpoint": "delete_job"})
            raise HTTPException(status_code=400, detail="User does not have an associated workshop.")
        
        # Query to get the job with car information
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
        # Query result
        job_data = result.first()

        # If job not found, raise 404
        if job_data is None:
            logger.error(f"Job ID {job_id} not found in workshop ID {workshop_id}",
                         extra={"user_id": current_user['user_id'], "endpoint": "get_job_by_id"})   
            raise HTTPException(status_code=404, detail="Job not found in your workshop.")
        
        job, car, customer_car = job_data
        logger.info(f"Successfully retrieved job ID {job_id} in workshop ID {workshop_id}")
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
        logger.critical(f"Database error while retrieving job information: {e}",
                        extra={"user_id": current_user['user_id'], "endpoint": "get_job_by_id"})
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
        logger.debug(f"Attempting to update job with ID: {job_id} by user ID: {current_user['user_id']}")

        # Get the workshop ID associated with the current user
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error("User does not have an associated workshop.",
                         extra={"user_id": current_user['user_id'], "endpoint": "update_job_info"})
            raise HTTPException(status_code=400, detail="User does not have an associated workshop.")
        
        # Check if the job exists and belongs to the user's workshop
        result = await db.execute(
            select(models.Job).where(
                models.Job.job_id == job_id,
                models.Job.workshop_id == workshop_id
            )
        )
        db_job = result.scalars().first()
        # If job not found, raise 404
        if not db_job:
            logger.error(f"Job ID {job_id} not found in workshop ID {workshop_id}",
                         extra={"user_id": current_user['user_id'], "endpoint": "update_job_info"})
            raise HTTPException(status_code=404, detail="Job not found in your workshop.")        
        
        # Update job fields
        update_data = job_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_job, field, value)
        # commit changes to dabase
        await db.commit()
        await db.refresh(db_job)
        logger.info(f"Successfully updated job ID {job_id} in workshop ID {workshop_id}",
                    extra={"user_id": current_user['user_id'], "endpoint": "update_job_info"})
        return db_job  
    except HTTPException:
        raise  
    except Exception as e:
        logger.critical(f"Database error in update_job_info: {e}",
                        extra={"user_id": current_user['user_id'], "endpoint": "update_job_info"})
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
        logger.debug(f"Attempting to delete job with ID: {job_id}")

        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error("User does not have an associated workshop.",
                         extra={"user_id": current_user['user_id'], "endpoint": "delete_job"})
            raise HTTPException(status_code=400, detail="User does not have an associated workshop.")
        
        # Check if the job exists and belongs to the user's workshop
        result = await db.execute(
            select(models.Job).where(
                models.Job.job_id == job_id,
                models.Job.workshop_id == workshop_id
            )
        )
        db_job = result.scalars().first()
        # If job not found, raise notFoundException
        if not db_job:
            logger.error(f"Job ID {job_id} not found in workshop ID {workshop_id}",
                         extra={"user_id": current_user['user_id'], "endpoint": "delete_job"})
            raise HTTPException(status_code=404, detail="Job not found in your workshop.") 
        
        # Proceed to delete the job
        await db.delete(db_job)
        await db.commit()

        logger.info(f"Successfully deleted job ID {job_id} from workshop ID {workshop_id}")
        return {"message": "Job deleted successfully", "job_id": job_id}
    except HTTPException:
        raise  
    except Exception as e:
        logger.critical(f"Database error in delete_job: {e}",
                     extra={"user_id": current_user['user_id'], "endpoint": "delete_job"})
        raise fetchErrorException