from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from db import models, schemas
from exceptions.exceptions import fetchErrorException
from ..workshops.service import get_current_user_workshop_id
from logger.logger import get_logger
from typing import List

logger = get_logger()

# ---------------- All customers ADMIN functions ----------------
async def create_customer(
        customer: schemas.CustomerCreate,
        db: AsyncSession,
        current_user: dict) -> models.Customer:
    '''
    Construct a query to create a new customer
    '''
    try:
        logger.debug(f"[ADMIN FUNC] Creating customer for workshop ID {customer.workshop_id} by admin user")     
        # Create customer model   
        db_customer = models.Customer(**customer.model_dump())
        # Add and commit to database
        db.add(db_customer)
        await db.commit()
        await db.refresh(db_customer)
        logger.info(f"[ADMIN FUNC] Customer created with ID {db_customer.customer_id} by admin user")
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in create_customer: {e}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "create_customer"})
        raise fetchErrorException
    
async def get_all_customers(
        db: AsyncSession, 
        current_user: dict, 
        skip: int = 0, 
        limit: int = 100):
    '''
    Construct a query to get all customers
    '''
    try:
        logger.debug(f"[ADMIN FUNC] Fetching all customers with skip={skip} and limit={limit} by admin user")
        # Get all customers
        result = await db.execute(
            select(models.Customer).offset(skip).limit(limit)
        )
        # Query result
        customers = result.scalars().all()
        logger.info(f"[ADMIN FUNC] Fetched {len(customers)} customers by admin user", 
                    extra={"user_id": current_user["user_id"], "endpoint": "get_all_customers"})
        return customers
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_all_customers: {e}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_all_customers"})
        raise fetchErrorException
    
async def get_customer_by_id(
        customer_id: int,
        db: AsyncSession, 
        current_user: dict) -> models.Customer:
    '''
    Construct a query to get a customer by ID
    '''
    try:
        logger.debug(f"[ADMIN FUNC] Fetching customer with ID {customer_id} by admin user")
        result = await db.execute(
            select(models.Customer).filter(models.Customer.customer_id == customer_id)
        )
        # Get customer data
        db_customer = result.scalar_one_or_none()
        # If customer not found, raise 404
        if db_customer is None:
            logger.error(f"[ADMIN FUNC] Customer with ID {customer_id} not found", 
                         extra={"user_id": current_user["user_id"], "endpoint": "get_customer_by_id"})
            raise HTTPException(status_code=404, detail="Customer not found")
        logger.info(f"[ADMIN FUNC] Customer with ID {customer_id} fetched by admin user", 
                    extra={"user_id": current_user["user_id"], "endpoint": "get_customer_by_id"})
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_customer_by_id: {e}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_customer_by_id"})
        raise fetchErrorException
    
async def update_customer(
        customer_id: int, 
        customer_update: schemas.CustomerUpdate,
        db: AsyncSession,
        current_user: dict) -> models.Customer:
    '''
    Construct a query to update a customer's information
    '''
    try:
        logger.debug(f"[ADMIN FUNC] Updating customer with ID {customer_id} by admin user")
        # Get existing customer data
        customer_data = await get_customer_by_id(customer_id, db, current_user)
        # Prepare update data
        update_data = customer_update.model_dump(exclude_unset=True)
        # update Fields
        for key, value in update_data.items():
            setattr(customer_data, key, value)
        # Commit changes to database
        await db.commit()
        await db.refresh(customer_data)
        logger.info(f"[ADMIN FUNC] Customer with ID {customer_id} updated by admin user")
        return customer_data
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in update_customer: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "update_customer"})
        raise fetchErrorException
    
async def delete_customer(
        customer_id: int,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to delete a customer
    '''
    try:
        logger.debug(f"[ADMIN FUNC] Deleting customer with ID {customer_id} by admin user")

        # Get customer to delete
        result = await db.execute(
            select(models.Customer).filter(models.Customer.customer_id == customer_id)
        )
        # Query result
        db_customer = result.scalar_one_or_none()
        # If customer not found, raise 404
        if db_customer is None:
            logger.error(f"[ADMIN FUNC] Customer with ID {customer_id} not found", 
                         extra={"user_id": current_user["user_id"], "endpoint": "delete_customer"})
            raise HTTPException(status_code=404, detail="Customer not found")
        # Delete the customer
        await db.execute(
            delete(models.Customer).where(models.Customer.customer_id == customer_id)
        )
        # Commit changes
        await db.commit()
        logger.info(f"[ADMIN FUNC] Customer with ID {customer_id} deleted") 
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in delete_customer: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "delete_customer"})
        raise fetchErrorException

# ---------------- All customers functions ----------------
async def create_current_user_workshop_customer(
    current_user: dict,
    customer: schemas.CustomerCreate,
    db: AsyncSession
) -> models.Customer:
    """
    Create a customer for the current logged-in user's workshop
    """
    try:
        logger.debug(f"Creating customer for workshop {get_current_user_workshop_id(current_user)}")
        # Get current user's workshop ID
        workshop_id = get_current_user_workshop_id(current_user)
        # If user has no workshop, raise 400
        if workshop_id == 1:
            logger.error(f"Current user {current_user['user_id']} has no associated workshop and tried to access customers",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customers"})
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        
        # Create customer model
        create_customer_model = models.Customer(
            first_name=customer.first_name,
            last_name=customer.last_name,
            phone=customer.phone,
            email=customer.email,
            workshop_id=workshop_id  # Set automatically from user's workshop
        )
        # Add customer to database
        db.add(create_customer_model)
        await db.commit()
        await db.refresh(create_customer_model)

        logger.info(f"Customer created with ID {create_customer_model.customer_id} for workshop {workshop_id}")
        return create_customer_model
    except HTTPException:
        raise   
    except Exception as e:
        logger.critical(f"Database error in create_current_user_workshop_customer: {e}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "create_current_user_workshop_customer"})
        raise fetchErrorException
    
async def get_current_user_workshop_customers(
    current_user: dict,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[models.Customer]:
    """
    Get customers associated with the current logged-in user's workshop
    """
    try: 
        logger.debug(f"Fetching customers for workshop {get_current_user_workshop_id(current_user)}")
        # Get current user's workshop ID
        workshop_id = get_current_user_workshop_id(current_user)
        # If user has no workshop, raise 400
        if workshop_id == 1:
            logger.error(f"Current user {current_user['user_id']} has no associated workshop and tried to access customers",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customers"})
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        # Query customers for the user's workshop
        result = await db.execute(
            select(models.Customer)
            .filter(models.Customer.workshop_id == workshop_id)
            .offset(skip)
            .limit(limit)
        )
        # Query result
        customers = result.scalars().all()
        logger.info(f"Fetched {len(customers)} customers for workshop {workshop_id}")
        return customers
    except HTTPException:
        raise   
    except Exception as e:
        logger.critical(f"Database error in get_current_user_workshop_customers: {e}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customers"})
        raise fetchErrorException
    
async def get_current_user_workshop_customer_by_id(
        customer_id: int, 
        db: AsyncSession, 
        current_user: dict) -> models.Customer:
    """
    Get a specific customer by ID for the current logged-in user's workshop
    """
    try: 
        logger.debug(f"Fetching customer with ID {customer_id} for workshop {get_current_user_workshop_id(current_user)}")
        # Get current user's workshop ID
        workshop_id = get_current_user_workshop_id(current_user)
        # If user has no workshop, raise 400
        if workshop_id == 1:   
            logger.error(f"Current user {current_user['user_id']} has no associated workshop and tried to access customer with ID {customer_id}",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customer_by_id"})
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        
        # Verify the customer belongs to the user's workshop
        result = await db.execute(
            select(models.Customer)
            .filter(models.Customer.customer_id == customer_id)
            .filter(models.Customer.workshop_id == workshop_id)
        )
        # Query result
        db_customer = result.scalar_one_or_none()
        # If customer not found or does not belong to user's workshop, raise 404
        if db_customer is None:
            logger.error(f"Customer with ID {customer_id} not found in workshop {workshop_id}", 
                         extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customer_by_id"})
            raise HTTPException(status_code=404, detail="Customer not found")
        
        logger.info(f"Customer with ID {customer_id} fetched for workshop {workshop_id}")
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_current_user_workshop_customer_by_id: {e}", 
                     extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_customer_by_id"})
        raise fetchErrorException

async def update_current_user_workshop_customer_by_id(
        customer_id: int, 
        customer_update: schemas.CustomerUpdate,
        db: AsyncSession, 
        current_user: dict) -> models.Customer:
    """
    Update a specific customer by ID for the current logged-in user's workshop
    """
    try: 
        logger.debug(f"Updating customer with ID {customer_id} for workshop {get_current_user_workshop_id(current_user)}")

        # Get current user's workshop ID
        workshop_id = get_current_user_workshop_id(current_user)
        # If user has no workshop, raise 400
        if workshop_id == 1:   
            logger.error(f"Current user {current_user['user_id']} has no associated workshop and tried to update customer with ID {customer_id}",
                         extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_workshop_customer_by_id"})
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        
        # Verify the customer belongs to the user's workshop
        result = await db.execute(
            select(models.Customer)
            .filter(models.Customer.customer_id == customer_id)
            .filter(models.Customer.workshop_id == workshop_id)
        )
        # Query result
        customer_data = result.scalar_one_or_none()
        # If customer not found or does not belong to user's workshop, raise 404
        if customer_data is None:
            logger.error(f"Customer with ID {customer_id} not found in workshop {workshop_id}", 
                         extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_workshop_customer_by_id"})
            raise HTTPException(status_code=404, detail="Customer not found")
        # Update fields
        update_data = customer_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(customer_data, key, value)

        # Commit changes to database
        await db.commit()
        await db.refresh(customer_data)
        logger.info(f"Customer with ID {customer_id} updated for workshop {workshop_id}")
        return customer_data
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in update_current_user_workshop_customer_by_id: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_workshop_customer_by_id"})
        raise fetchErrorException

async def delete_current_user_workshop_customer(
    current_user: dict,
    customer_id: int,
    db: AsyncSession
):
    """
    Delete a customer for the current logged-in user's workshop
    """
    try: 
        logger.debug(f"Deleting customer with ID {customer_id} for workshop {get_current_user_workshop_id(current_user)}")
        # Get current user's workshop ID
        workshop_id = get_current_user_workshop_id(current_user)
        # If user has no workshop, raise 400
        if workshop_id == 1:
            logger.error("User does not have an associated workshop.",
                         extra={"user_id": current_user["user_id"], "endpoint": "delete_current_user_workshop_customer"})
            raise HTTPException(status_code=400, detail="User does not have an associated workshop.")

        # Verify the customer belongs to the user's workshop
        result = await db.execute(
            select(models.Customer).filter(
                models.Customer.customer_id == customer_id,
                models.Customer.workshop_id == workshop_id
            )
        )
        # Query result
        db_customer = result.scalar_one_or_none()

        # If customer not found in the workshop, raise 404
        if db_customer is None:
            logger.error(f"Customer with ID {customer_id} not found in workshop {workshop_id}", 
                         extra={"user_id": current_user["user_id"], "endpoint": "delete_current_user_workshop_customer"})
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Delete the customer
        await db.execute(
            delete(models.Customer).where(models.Customer.customer_id == customer_id)
        )
        # Commit changes to database
        await db.commit()
        logger.info(f"Customer with ID {customer_id} deleted from workshop {workshop_id}")
        return db_customer
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in delete_current_user_workshop_customer: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "delete_current_user_workshop_customer"})
        raise fetchErrorException

async def assign_customer_to_car(
        customer_id: int,  
        car_data: schemas.CustomerCarAssign, 
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to assign a customer to a car
    '''
    try:
        logger.debug(f"Assigning car ID {car_data.car_id} to customer ID {customer_id}")
        
        # Get current user's workshop ID
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error(f"Current user {current_user['user_id']} has no associated workshop",
                         extra={"user_id": current_user["user_id"], "endpoint": "assign_customer_to_car"})
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        
        # First verify the customer belongs to the user's workshop
        result = await db.execute(
            select(models.Customer)
            .filter(models.Customer.customer_id == customer_id)
            .filter(models.Customer.workshop_id == workshop_id)
        )
        # Query result
        customer = result.scalar_one_or_none()

        # If customer not found in the workshop, raise 404
        if not customer:
            logger.error(f"Customer with ID {customer_id} not found", 
                         extra={"user_id": current_user["user_id"], "endpoint": "assign_customer_to_car"})
            raise HTTPException(status_code=404, detail="Customer not found")
        # Now verify the car exists
        result = await db.execute(
            select(models.Car).filter(models.Car.car_id == car_data.car_id)
        )
        # Query result
        car = result.scalar_one_or_none()
        # If car not found, raise 404
        if not car:
            logger.error(f"Car with ID {car_data.car_id} not found", 
                         extra={"user_id": current_user["user_id"], "endpoint": "assign_customer_to_car"})
            raise HTTPException(status_code=404, detail="Car not found")
        
        # Create relationship 
        customer_car = models.CustomerCar(
            customer_id=customer_id,
            car_id=car_data.car_id,
            license_plate=car_data.license_plate,
            color=car_data.color
        )

        # Add and commit to database    
        db.add(customer_car)
        await db.commit()
        await db.refresh(customer_car)
        logger.info(f"Assigned car ID {car_data.car_id} to customer ID {customer_id}")
        return customer_car
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in assign_customer_to_car: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "assign_customer_to_car"})
        raise fetchErrorException
    
async def get_cars_by_customer(
        customer_id: int,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to get all cars associated with a customer in the current user's workshop
    '''
    try:
        logger.debug(f"Fetching cars for customer ID {customer_id}")
        
        # Get current user's workshop ID
        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error(f"Current user {current_user['user_id']} has no associated workshop",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_cars_by_customer"})
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        
        # First verify the customer belongs to the user's workshop
        result = await db.execute(
            select(models.Customer)
            .filter(models.Customer.customer_id == customer_id)
            .filter(models.Customer.workshop_id == workshop_id)
        )
        # Query result
        customer = result.scalar_one_or_none()
        # If customer not found in the workshop, raise 404
        if not customer:
            logger.error(f"Customer with ID {customer_id} not found in workshop {workshop_id}", 
                         extra={"user_id": current_user["user_id"], "endpoint": "get_cars_by_customer"})
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Now get the cars for this customer
        result = await db.execute(
            select(models.Car).join(models.CustomerCar).filter(models.CustomerCar.customer_id == customer_id)
        )
        cars = result.scalars().all()
        logger.info(f"Fetched {len(cars)} cars for customer ID {customer_id}")
        return cars
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_cars_by_customer: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "get_cars_by_customer"})
        raise fetchErrorException
    
async def get_customer_full_car_info_by_id(
        customer_id: int,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to get full car information for a customer's cars
    '''
    try:
        logger.debug(f"Fetching full car info for customer ID {customer_id}")
        
        # Get current user's workshop ID
        workshop_id = get_current_user_workshop_id(current_user)
        # If no workshop associated, raise error
        if workshop_id == 1:
            logger.error(f"Current user {current_user['user_id']} has no associated workshop",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_customer_full_car_info_by_id"})
            raise HTTPException(status_code=400, detail="Current user is not associated with any workshop")
        
        # Verify customer belongs to user's workshop
        customer = await db.execute(
            select(models.Customer)
            .filter(models.Customer.customer_id == customer_id)
            .filter(models.Customer.workshop_id == workshop_id)
        )
        # Query result
        customer_obj = customer.scalar_one_or_none()

        # If customer not found in the workshop, raise 404
        if not customer_obj:
            logger.error(f"Customer with ID {customer_id} not found in workshop {workshop_id}", 
                         extra={"user_id": current_user["user_id"], "endpoint": "get_customer_full_car_info_by_id"})
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Fetch full car info
        result = await db.execute(
            select(models.CustomerCar, models.Car)
            .join(models.Car, models.CustomerCar.car_id == models.Car.car_id)
            .filter(models.CustomerCar.customer_id == customer_id)
        )
        
        # Build list of CustomerCarWithCarInfo schemas
        customer_cars_with_info = [
            schemas.CustomerCarWithCarInfo(
                customer_car_id=customer_car.customer_car_id,
                customer_id=customer_car.customer_id,
                car_id=customer_car.car_id,
                license_plate=customer_car.license_plate,
                color=customer_car.color,
                car_brand=car.brand,
                car_model=car.model,
                car_year=car.year
            )
            for customer_car, car in result.all()
        ]
        
        logger.info(f"Fetched {len(customer_cars_with_info)} cars with full info for customer ID {customer_id}")
        return customer_cars_with_info
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_customer_full_car_info: {e}",
                     extra={"user_id": current_user["user_id"], "endpoint": "get_customer_full_car_info_by_id"})
        raise fetchErrorException