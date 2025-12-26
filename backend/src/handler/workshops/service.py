from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import os
import uuid
from pathlib import Path

from db import models, schemas
from exceptions.exceptions import notFoundException, fetchErrorException


def validate_workshop_fields(workshop: schemas.WorkshopCreate | schemas.WorkshopUpdate):
    """
    Validate required fields for creating or updating a workshop
    """
    # For WorkshopCreate, workshop_name is required. For WorkshopUpdate, it's optional
    if isinstance(workshop, schemas.WorkshopCreate):
        if not workshop.workshop_name or not workshop.workshop_name.strip():
            raise HTTPException(status_code=422, detail="Workshop name cannot be empty")
    elif isinstance(workshop, schemas.WorkshopUpdate):
        # Only validate workshop_name if it's provided in the update
        if workshop.workshop_name is not None and (not workshop.workshop_name or not workshop.workshop_name.strip()):
            raise HTTPException(status_code=422, detail="Workshop name cannot be empty")
    
    if workshop.workshop_name and len(workshop.workshop_name) > 100:
        raise HTTPException(status_code=422, detail="Workshop name exceeds maximum length of 100 characters")
    if workshop.address and len(workshop.address) > 200:
        raise HTTPException(status_code=422, detail="Address exceeds maximum length of 200 characters")
    if workshop.opening_hours and len(workshop.opening_hours) > 50:
        raise HTTPException(status_code=422, detail="Opening hours exceeds maximum length of 50 characters")
    if workshop.closing_hours and len(workshop.closing_hours) > 50:
        raise HTTPException(status_code=422, detail="Closing hours exceeds maximum length of 50 characters")    


# ---------------- All workshops functions (ADMIN REQUIRED)----------------
async def create_workshop(
        workshop: schemas.WorkshopCreate,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to create a new workshop
    '''
    try:
        validate_workshop_fields(workshop)
        db_workshop = models.Workshop(**workshop.model_dump())
        db.add(db_workshop)
        await db.commit()
        await db.refresh(db_workshop)
        return db_workshop
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in create_workshop: {e}")
        raise fetchErrorException
    
async def get_all_workshops(
        db: AsyncSession, 
        current_user: dict, 
        skip: int = 0, 
        limit: int = 100):
    '''
    Construct a query to get all workshops
    '''
    try:
        result = await db.execute(
            select(models.Workshop).offset(skip).limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        print(f"Database error in get_all_workshops: {e}")
        raise fetchErrorException
    
async def get_workshop_by_id(
        workshop_id: int,
        db: AsyncSession, 
        current_user: dict):
    '''
    Construct a query to get a workshop by ID
    '''
    try:
        result = await db.execute(
            select(models.Workshop).filter(models.Workshop.workshop_id == workshop_id)
        )
        # Get workshop data
        db_workshop = result.scalar_one_or_none()
        # If workshop not found, raise 404
        if db_workshop is None:
            raise notFoundException
        return db_workshop
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in get_workshop_by_id: {e}")
        raise fetchErrorException
    
async def update_workshop(
        workshop_id: int,
        workshop_update: schemas.WorkshopUpdate,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to update a workshop's information
    '''
    try:
        validate_workshop_fields(workshop_update)
        workshop_data = await get_workshop_by_id(workshop_id, db, current_user)
        if workshop_data is None:
            raise notFoundException
            # Prepare update data
        update_data = workshop_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workshop_data, field, value)

        await db.commit()
        await db.refresh(workshop_data)
        return workshop_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in update_workshop: {e}")
        raise fetchErrorException
    
async def delete_workshop(
        workshop_id: int,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to delete a workshop
    '''
    try:
        workshop_data = await get_workshop_by_id(workshop_id, db, current_user)
        if workshop_data is None:
            raise notFoundException
        await db.execute(
            delete(models.Workshop).where(models.Workshop.workshop_id == workshop_id)
        )
        await db.commit()
        return workshop_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in delete_workshop: {e}")
        raise fetchErrorException
    
# ---------------- End of all workshops functions FOR ADMINS ----------------

# ---------------- Current user's workshop functions ----------------
def get_current_user_workshop_id(user: dict) -> int:
    """
    Utility function to get the workshop ID of the current user
    """
    return user.get("workshop_id")

async def create_current_user_workshop(
    current_user: dict,
    workshop: schemas.WorkshopCreate,
    db: AsyncSession
):
    """
    Create a workshop for the current logged-in user
    """
    try: 
        validate_workshop_fields(workshop)
        if get_current_user_workshop_id(current_user) != 1:
            raise HTTPException(status_code=400, detail="User already has a workshop")
        
        create_workshop_model = models.Workshop(
            workshop_name=workshop.workshop_name,
            address=workshop.address,
            opening_hours=workshop.opening_hours,
            closing_hours=workshop.closing_hours
        )
        db.add(create_workshop_model)
        await db.commit()
        await db.refresh(create_workshop_model)

        # Update user's workshop_id
        result = await db.execute(
            select(models.User).filter(models.User.user_id == current_user["user_id"])
        )
        db_user = result.scalar_one_or_none()
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        db_user.workshop_id = create_workshop_model.workshop_id
        await db.commit()
        await db.refresh(db_user)
        return create_workshop_model
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in create_current_user_workshop: {e}")
        raise fetchErrorException


async def upload_current_user_workshop_logo(
    current_user: dict,
    logo_file: UploadFile,
    db: AsyncSession
):
    """
    Upload or update the logo for the current logged-in user's workshop
    Saves the file to backend/logos/ folder and stores the URL path in database
    """
    try: 
        if get_current_user_workshop_id(current_user) == 1:
            raise HTTPException(status_code=400, detail="User has no workshop to update")
        
        # Validate file type
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        file_extension = Path(logo_file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Only JPG, PNG, GIF, and WebP files are allowed."
            )
        
        # Create logos directory if it doesn't exist
        logos_dir = Path("logos")
        logos_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = logos_dir / unique_filename
        
        # Save file to disk
        try:
            content = await logo_file.read()
            with open(file_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
        # Create URL path for database
        logo_url = f"/logos/{unique_filename}"
        
        # Get and update workshop
        result = await db.execute(
            select(models.Workshop).filter(models.Workshop.workshop_id == current_user["workshop_id"])
        )
        db_workshop = result.scalars().first()
        if not db_workshop:
            # Clean up uploaded file if workshop not found
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=404, detail="Workshop not found")
        
        # Remove old logo file if it exists
        if db_workshop.workshop_logo:
            old_file_path = Path(db_workshop.workshop_logo.lstrip("/"))
            if old_file_path.exists():
                try:
                    old_file_path.unlink()
                except Exception:
                    pass  # Continue even if old file deletion fails
        
        db_workshop.workshop_logo = logo_url

        await db.commit()
        await db.refresh(db_workshop)
        return db_workshop
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in upload_current_user_workshop_logo: {e}")
        raise fetchErrorException


async def get_current_user_workshop_logo(
    current_user: dict,
    db: AsyncSession
):
    """
    Get the logo URL for the workshop associated with the current logged-in user
    """
    try:
        if get_current_user_workshop_id(current_user) == 1:
            raise HTTPException(status_code=400, detail="User has no workshop")
        
        result = await db.execute(
            select(models.Workshop).filter(models.Workshop.workshop_id == current_user["workshop_id"])
        )
        workshop = result.scalars().first()
        if not workshop:
            raise notFoundException
        
        return {
            "workshop_id": workshop.workshop_id,
            "workshop_logo": workshop.workshop_logo
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in get_current_user_workshop_logo: {e}")
        raise fetchErrorException


async def get_current_user_workshop(
    current_user: dict,
    db: AsyncSession
):
    """
    Get the workshop associated with the current logged-in user
    """
    try:
        result = await db.execute(
            select(models.Workshop).filter(models.Workshop.workshop_id == current_user["workshop_id"])
        )
        workshop = result.scalars().first()
        if not workshop:
            raise notFoundException
        return [workshop]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in get_current_user_workshop: {e}")
        raise fetchErrorException

async def patch_current_user_workshop(
    current_user: dict,
    workshop_update: schemas.WorkshopUpdate,
    db: AsyncSession
):
    """
    Update the workshop associated with the current logged-in user
    """
    try:
        validate_workshop_fields(workshop_update)
        if get_current_user_workshop_id(current_user) == 1:
            raise HTTPException(status_code=400, detail="User has no workshop to update")
        
        result = await db.execute(
            select(models.Workshop).filter(models.Workshop.workshop_id == current_user["workshop_id"])
        )
        db_workshop = result.scalars().first()
        if not db_workshop:
            raise HTTPException(status_code=404, detail="Workshop not found")
        
        update_data = workshop_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_workshop, field, value)

        await db.commit()
        await db.refresh(db_workshop)
        return db_workshop
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in patch_current_user_workshop: {e}")
        raise fetchErrorException
# ---------------- End of current user's workshop functions ----------------

# ---------------- Current user's workshop parts functions ----------------

async def create_current_user_workshop_part(
    current_user: dict,
    part: schemas.PartWorkshopCreate,
    db: AsyncSession
    ):
    """
    Create a part associated with the current logged-in user's workshop
    """
    try: 
        workshop_id = get_current_user_workshop_id(current_user)
        
        # Check if this part already exists in the workshop
        existing_check = await db.execute(
            select(models.PartWorkshop)
            .filter(
                models.PartWorkshop.part_id == part.part_id,
                models.PartWorkshop.workshop_id == workshop_id
            )
        )
        existing_part = existing_check.scalar_one_or_none()
        
        if existing_part:
            raise HTTPException(
                status_code=400,
                detail=f"Part with ID {part.part_id} already exists in this workshop. Use PATCH to update it."
            )
        
        create_part_model = models.PartWorkshop(
            part_id=part.part_id,
            quantity=part.quantity,
            purchase_price=part.purchase_price,
            sale_price=part.sale_price,
            workshop_id=workshop_id  # Set automatically from user's workshop
        )

        db.add(create_part_model)
        await db.commit()
        await db.refresh(create_part_model)
        
        # Fetch the complete part data with join to return proper schema
        result = await db.execute(
            select(models.PartWorkshop, models.Part)
            .join(models.Part, models.PartWorkshop.part_id == models.Part.part_id)
            .filter(
                models.PartWorkshop.part_id == create_part_model.part_id,
                models.PartWorkshop.workshop_id == workshop_id
            )
        )
        part_workshop, part_data = result.first()
        
        # Combine data from both tables
        return schemas.PartWorkshop(
            part_id=part_workshop.part_id,
            workshop_id=part_workshop.workshop_id,
            quantity=part_workshop.quantity,
            purchase_price=part_workshop.purchase_price,
            sale_price=part_workshop.sale_price,
            part_name=part_data.part_name,
            brand=part_data.brand,
            description=part_data.description,
            category=part_data.category
        )
    except HTTPException:
        raise  
    except Exception as e:
        print(f"Database error in create_current_user_workshop_part: {e}")
        raise fetchErrorException

async def get_current_user_workshop_parts(
    current_user: dict,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
):
    """
    Get parts associated with the current logged-in user's workshop
    """
    try: 
        workshop_id = get_current_user_workshop_id(current_user)
        result = await db.execute(
            select(models.PartWorkshop, models.Part)
            .join(models.Part, models.PartWorkshop.part_id == models.Part.part_id)
            .filter(models.PartWorkshop.workshop_id == workshop_id)
            .offset(skip)
            .limit(limit)
        )
        parts_data = result.all()
        
        # Combine data from both tables
        return [
            schemas.PartWorkshop(
                part_id=part_workshop.part_id,
                workshop_id=part_workshop.workshop_id,
                quantity=part_workshop.quantity,
                purchase_price=part_workshop.purchase_price,
                sale_price=part_workshop.sale_price,
                part_name=part.part_name,
                brand=part.brand,
                description=part.description,
                category=part.category
            )
            for part_workshop, part in parts_data
        ]
    except HTTPException:
        raise  
    except Exception as e:
        print(f"Database error in get_current_user_workshop_parts: {e}")
        raise fetchErrorException

async def update_current_user_workshop_part(
    current_user: dict,
    part_id: int,
    part_update: schemas.PartWorkshopUpdate,
    db: AsyncSession
):
    """
    Patch a part associated with the current logged-in user's workshop
    """
    try: 
        workshop_id = get_current_user_workshop_id(current_user)

        result = await db.execute(
            select(models.PartWorkshop, models.Part)
            .join(models.Part, models.PartWorkshop.part_id == models.Part.part_id)
            .filter(
                models.PartWorkshop.part_id == part_id,
                models.PartWorkshop.workshop_id == workshop_id
            )
        )
        part_data = result.first()
        
        if not part_data:
            raise HTTPException(status_code=404, detail="Part not found in this workshop")
        
        part_workshop, part = part_data

        update_data = part_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(part_workshop, field, value)

        await db.commit()
        await db.refresh(part_workshop)

        return schemas.PartWorkshop(
            part_id=part_workshop.part_id,
            workshop_id=part_workshop.workshop_id,
            quantity=part_workshop.quantity,
            purchase_price=part_workshop.purchase_price,
            sale_price=part_workshop.sale_price,
            part_name=part.part_name,
            brand=part.brand,
            description=part.description,
            category=part.category
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in update_current_user_workshop_part: {e}")
        raise fetchErrorException

async def delete_current_user_workshop_part(
    current_user: dict,
    part_id: int,
    db: AsyncSession
):
    """
    Delete a part associated with the current logged-in user's workshop
    """
    try: 
        workshop_id = get_current_user_workshop_id(current_user)

        result = await db.execute(
            select(models.PartWorkshop, models.Part)
            .join(models.Part, models.PartWorkshop.part_id == models.Part.part_id)
            .filter(
                models.PartWorkshop.part_id == part_id,
                models.PartWorkshop.workshop_id == workshop_id
            )
        )
        part_data = result.first()
        
        if not part_data:
            raise HTTPException(status_code=404, detail="Part not found in this workshop")
        
        part_workshop, part = part_data

        await db.execute(
            delete(models.PartWorkshop).where(
                models.PartWorkshop.part_id == part_id,
                models.PartWorkshop.workshop_id == workshop_id
            )
        )
        await db.commit()
        return schemas.PartWorkshop(
            part_id=part_workshop.part_id,
            workshop_id=part_workshop.workshop_id,
            quantity=part_workshop.quantity,
            purchase_price=part_workshop.purchase_price,
            sale_price=part_workshop.sale_price,
            part_name=part.part_name,
            brand=part.brand,
            description=part.description,
            category=part.category
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in delete_current_user_workshop_part: {e}")
        raise fetchErrorException
