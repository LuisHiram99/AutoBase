from fastapi import Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import uuid
from pathlib import Path
from logger.logger import get_logger

from db import models, schemas
from exceptions.exceptions import notFoundException, fetchErrorException

logger = get_logger()
# ---------------- All workshops functions (ADMIN REQUIRED)----------------
async def create_workshop(
        workshop: schemas.WorkshopCreate,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to create a new workshop
    '''
    try:
        logger.debug(f"[ADMIN FUNC] Creating workshop: {workshop.workshop_name} by ADMIN user {current_user['user_id']}")

        # Create workshop model
        db_workshop = models.Workshop(**workshop.model_dump())
        # Add and commit workshop to database
        db.add(db_workshop)
        await db.commit()
        await db.refresh(db_workshop)
        logger.info(f"[ADMIN FUNC] Workshop created with ID: {db_workshop.workshop_id} by ADMIN user {current_user['user_id']}")
        return db_workshop
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in create_workshop: {e}", 
                        extra={"user_id": current_user["user_id"], "endpoint": "create_workshop"})
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
        logger.debug(f"[ADMIN FUNC] Fetching all workshops by ADMIN user{current_user['user_id']}")
        result = await db.execute(
            select(models.Workshop).offset(skip).limit(limit)
        )
        db_workshops = result.scalars().all()
        logger.info(f"[ADMIN FUNC] Fetched {len(db_workshops)} workshops by ADMIN user {current_user['user_id']}")
        return db_workshops
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_all_workshops: {e}", 
                        extra={"user_id": current_user["user_id"], "endpoint": "get_all_workshops"})
        raise fetchErrorException
    
async def get_workshop_by_id(
        workshop_id: int,
        db: AsyncSession, 
        current_user: dict):
    '''
    Construct a query to get a workshop by ID
    '''
    try:
        logger.debug(f"[ADMIN FUNC] Fetching workshop by ID: {workshop_id} by ADMIN user {current_user['user_id']}")

        # Execute query to get workshop by ID
        result = await db.execute(
            select(models.Workshop).filter(models.Workshop.workshop_id == workshop_id)
        )
        # Get workshop data
        db_workshop = result.scalar_one_or_none()
        # If workshop not found, raise 404
        if db_workshop is None:
            logger.error(f"[ADMIN FUNC] Workshop ID: {workshop_id} not found by ADMIN user {current_user['user_id']}",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_workshop_by_id"})
            raise notFoundException
        return db_workshop
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_workshop_by_id: {e}", 
                        extra={"user_id": current_user["user_id"], "endpoint": "get_workshop_by_id"})
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
        logger.debug(f"[ADMIN FUNC] Updating workshop ID: {workshop_id} by ADMIN user {current_user['user_id']}")

        # Get workshop data by ID
        workshop_data = await get_workshop_by_id(workshop_id, db, current_user)

        # If workshop not found, raise 404
        if workshop_data is None:
            logger.error(f"[ADMIN FUNC] Workshop ID: {workshop_id} not found for update by ADMIN user {current_user['user_id']}",
                         extra={"user_id": current_user["user_id"], "endpoint": "update_workshop"})
            raise notFoundException
        # Prepare update data
        update_data = workshop_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workshop_data, field, value)

        # Commit data to database
        await db.commit()
        await db.refresh(workshop_data)
        logger.info(f"[ADMIN FUNC] Workshop ID: {workshop_id} updated by ADMIN user {current_user['user_id']}")
        return workshop_data
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in update_workshop: {e}", 
                        extra={"user_id": current_user["user_id"], "endpoint": "update_workshop"})
        raise fetchErrorException
    
async def delete_workshop(
        workshop_id: int,
        db: AsyncSession,
        current_user: dict):
    '''
    Construct a query to delete a workshop
    '''
    try:
        logger.debug(f"[ADMIN FUNC] Deleting workshop ID: {workshop_id} by ADMIN user {current_user['user_id']}")

        # Get workshop data by ID
        workshop_data = await get_workshop_by_id(workshop_id, db, current_user)
        # If workshop not found, raise 404
        if workshop_data is None:
            logger.error(f"[ADMIN FUNC] Workshop ID: {workshop_id} not found for deletion by ADMIN user {current_user['user_id']}",
                            extra={"user_id": current_user["user_id"], "endpoint": "delete_workshop"})
            raise notFoundException
        
        # Delete workshop from database
        await db.execute(
            delete(models.Workshop).where(models.Workshop.workshop_id == workshop_id)
        )
        # Commit changes
        await db.commit()
        logger.info(f"[ADMIN FUNC] Workshop ID: {workshop_id} deleted by ADMIN user {current_user['user_id']}")
        return workshop_data
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in delete_workshop: {e}", 
                        extra={"user_id": current_user["user_id"], "endpoint": "delete_workshop"})
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
        logger.debug(f"Creating workshop for user {current_user['user_id']}")

        # If user already has a workshop, raise error
        if get_current_user_workshop_id(current_user) != 1:
            logger.error(f"User {current_user['user_id']} already has a workshop",
                            extra={"user_id": current_user["user_id"], "endpoint": "create_current_user_workshop"})
            raise HTTPException(status_code=400, detail="User already has a workshop")
        
        # Create workshop model
        create_workshop_model = models.Workshop(
            workshop_name=workshop.workshop_name,
            address=workshop.address,
            opening_hours=workshop.opening_hours,
            closing_hours=workshop.closing_hours
        )
        # Add and commit workshop to database
        db.add(create_workshop_model)
        await db.commit()
        await db.refresh(create_workshop_model)

        # Update user's workshop_id
        result = await db.execute(
            select(models.User).filter(models.User.user_id == current_user["user_id"])
        )
        db_user = result.scalar_one_or_none()
        if db_user is None:
            logger.error(f"User {current_user['user_id']} not found when assigning workshop",
                         extra={"user_id": current_user["user_id"], "endpoint": "create_current_user_workshop"})
            raise HTTPException(status_code=404, detail="User not found")

        db_user.workshop_id = create_workshop_model.workshop_id

        # Commit user update to database
        await db.commit()
        await db.refresh(db_user)

        logger.info(f"Workshop created with ID: {create_workshop_model.workshop_id} for user {current_user['user_id']}")
        return create_workshop_model
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in create_current_user_workshop: {e}", 
                        extra={"user_id": current_user["user_id"], "endpoint": "create_current_user_workshop"})
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
        logger.debug(f"Uploading logo for user {current_user['user_id']}")
        if get_current_user_workshop_id(current_user) == 1:
            logger.error(f"User {current_user['user_id']} has no workshop to upload logo for",
                         extra={"user_id": current_user["user_id"], "endpoint": "upload_current_user_workshop_logo"})
            raise HTTPException(status_code=400, detail="User has no workshop to update")
        
        # Validate file type
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        file_extension = Path(logo_file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            logger.error(f"User {current_user['user_id']} attempted to upload invalid file type: {file_extension}",
                            extra={"user_id": current_user["user_id"], "endpoint": "upload_current_user_workshop_logo"})
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
            logger.error(f"Failed to save logo file for user {current_user['user_id']}: {e}",
                         extra={"user_id": current_user["user_id"], "endpoint": "upload_current_user_workshop_logo"})
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
            logger.error(f"Workshop for user {current_user['user_id']} not found when uploading logo",
                         extra={"user_id": current_user["user_id"], "endpoint": "upload_current_user_workshop_logo"})
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
        logger.info(f"User {current_user['user_id']} uploaded new logo for workshop {db_workshop.workshop_id}",
                    extra={"user_id": current_user["user_id"], "endpoint": "upload_current_user_workshop_logo"})
        # Commit changes to database
        await db.commit()
        await db.refresh(db_workshop)
        return db_workshop
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in upload_current_user_workshop_logo: {e}",
                        extra={"user_id": current_user["user_id"], "endpoint": "upload_current_user_workshop_logo"})
        raise fetchErrorException


async def get_current_user_workshop_logo(
    current_user: dict,
    db: AsyncSession
):
    """
    Get the logo URL for the workshop associated with the current logged-in user
    """
    try:
        logger.debug(f"Fetching logo for user {current_user['user_id']}")
        if get_current_user_workshop_id(current_user) == 1:
            logger.error(f"User {current_user['user_id']} has no workshop to fetch logo for",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_logo"})
            raise HTTPException(status_code=400, detail="User has no workshop")
        
        # Get workshop logo
        result = await db.execute(
            select(models.Workshop).filter(models.Workshop.workshop_id == current_user["workshop_id"])
        )
        workshop = result.scalars().first()
        # If workshop not found, raise 404
        if not workshop:
            logger.error(f"Workshop for user {current_user['user_id']} not found when fetching logo",
                            extra={"user_id": current_user["user_id"],   "endpoint": "get_current_user_workshop_logo"})
            raise notFoundException
        
        logger.info(f"User {current_user['user_id']} fetched logo for workshop {workshop.workshop_id}")
        return {
            "workshop_id": workshop.workshop_id,
            "workshop_logo": workshop.workshop_logo
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_current_user_workshop_logo: {e}",
                        extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_logo"})
        raise fetchErrorException


async def get_current_user_workshop(
    current_user: dict,
    db: AsyncSession
):
    """
    Get the workshop associated with the current logged-in user
    """
    try:
        logger.debug(f"Fetching workshop for user {current_user['user_id']}")
        if current_user['workshop_id'] == 1:
            logger.error(f"User {current_user['user_id']} has no workshop to fetch",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop"})
            raise HTTPException(status_code=400, detail="User has no workshop")

        result = await db.execute(
            select(models.Workshop).filter(models.Workshop.workshop_id == current_user["workshop_id"])
        )
        workshop = result.scalars().first()

        if not workshop:
            logger.error(f"Workshop for user {current_user['user_id']} not found when fetching",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop"})
            raise notFoundException
        logger.info(f"User {current_user['user_id']} fetched workshop {workshop.workshop_id}")
        return [workshop]  # Return as list to match endpoint response type
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in get_current_user_workshop: {e}",
                        extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop"})
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
        logger.debug(f"Updating workshop for user {current_user['user_id']}")
        if current_user["workshop_id"] == 1:
            logger.error(f"User {current_user['user_id']} has no workshop to update",
                         extra={"user_id": current_user["user_id"], "endpoint": "patch_current_user_workshop"})
            raise HTTPException(status_code=400, detail="User has no workshop to update")
        
        # Query workshop by current user's workshop_id
        result = await db.execute(
            select(models.Workshop).filter(models.Workshop.workshop_id == current_user["workshop_id"])
        )
        db_workshop = result.scalars().first()
        # if no workshop found, raise 404
        if not db_workshop:
            logger.error(f"Workshop for user {current_user['user_id']} not found when updating",
                            extra={"user_id": current_user["user_id"], "endpoint": "patch_current_user_workshop"})
            raise HTTPException(status_code=404, detail="Workshop not found")
        

        # Update workshop fields
        update_data = workshop_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_workshop, field, value)
        # Commit changes to database
        await db.commit()
        await db.refresh(db_workshop)
        logger.info(f"User {current_user['user_id']} updated workshop {db_workshop.workshop_id}")
        return db_workshop
    except HTTPException:
        raise
    except Exception as e:
        logger.critical(f"Database error in patch_current_user_workshop: {e}",
                        extra={"user_id": current_user["user_id"], "endpoint": "patch_current_user_workshop"})
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
        logger.debug(f"Creating part {part.part_id} for user {current_user['user_id']}'s workshop")
        workshop_id = get_current_user_workshop_id(current_user)

        if workshop_id == 1:
            logger.error(f"User {current_user['user_id']} has no workshop to add part to",
                         extra={"user_id": current_user["user_id"], "endpoint": "create_current_user_workshop_part"})
            raise HTTPException(status_code=400, detail="User has no workshop to add parts to")
        
        # Check if this part already exists in the workshop
        existing_check = await db.execute(
            select(models.PartWorkshop)
            .filter(
                models.PartWorkshop.part_id == part.part_id,
                models.PartWorkshop.workshop_id == workshop_id
            )
        )
        existing_part = existing_check.scalar_one_or_none()
        
        # If the part already exists, raise error   
        if existing_part:
            logger.error(f"Part {part.part_id} already exists in workshop {workshop_id} for user {current_user['user_id']}",
                         extra={"user_id": current_user["user_id"], "endpoint": "create_current_user_workshop_part"})
            raise HTTPException(
                status_code=400,
                detail=f"Part with ID {part.part_id} already exists in this workshop. Use PATCH to update it."
            )
        
        # Create PartWorkshop model
        create_part_model = models.PartWorkshop(
            part_id=part.part_id,
            quantity=part.quantity,
            purchase_price=part.purchase_price,
            sale_price=part.sale_price,
            workshop_id=workshop_id  # Set automatically from user's workshop
        )

        # Add and commit to database
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
        
        logger.info(f"Part {part.part_id} created in workshop {workshop_id} for user {current_user['user_id']}")
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
        logger.critical(f"Database error in create_current_user_workshop_part: {e}",
                        extra ={"user_id": current_user["user_id"], "endpoint": "create_current_user_workshop_part"})
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
        logger.debug(f"Fetching parts for user {current_user['user_id']}'s workshop")

        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error(f"User {current_user['user_id']} has no workshop to fetch parts from",
                         extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_parts"})
            raise HTTPException(status_code=400, detail="User has no workshop to fetch parts from")
        
        # Query parts with join to get part details
        result = await db.execute(
            select(models.PartWorkshop, models.Part)
            .join(models.Part, models.PartWorkshop.part_id == models.Part.part_id)
            .filter(models.PartWorkshop.workshop_id == workshop_id)
            .offset(skip)
            .limit(limit)
        )
        parts_data = result.all()
        
        logger.info(f"Fetched {len(parts_data)} parts for workshop {workshop_id} of user {current_user['user_id']}")
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
        logger.critical(f"Database error in get_current_user_workshop_parts: {e}",
                        extra={"user_id": current_user["user_id"], "endpoint": "get_current_user_workshop_parts"})
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
        logger.debug(f"Updating part {part_id} for user {current_user['user_id']}'s workshop")  
        workshop_id = get_current_user_workshop_id(current_user)

        if workshop_id == 1:
            logger.error(f"User {current_user['user_id']} has no workshop to update part in",
                         extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_workshop_part"})
            raise HTTPException(status_code=400, detail="User has no workshop to update parts in")

        # Query to get the parts in the workshop by ID
        result = await db.execute(
            select(models.PartWorkshop, models.Part)
            .join(models.Part, models.PartWorkshop.part_id == models.Part.part_id)
            .filter(
                models.PartWorkshop.part_id == part_id,
                models.PartWorkshop.workshop_id == workshop_id
            )
        )
        # Query results
        part_data = result.first()
        
        # If part not found, raise 404
        if not part_data:
            logger.error(f"Part {part_id} not found in workshop {workshop_id} for user {current_user['user_id']}",
                         extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_workshop_part"})
            raise HTTPException(status_code=404, detail="Part not found in this workshop")
        
        # Update fields
        part_workshop, part = part_data
        update_data = part_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(part_workshop, field, value)

        # Commit changes to database
        await db.commit()
        await db.refresh(part_workshop)


        logger.info(f"Part {part_id} updated in workshop {workshop_id} for user {current_user['user_id']}")
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
        logger.critical(f"Database error in update_current_user_workshop_part: {e}",
                        extra={"user_id": current_user["user_id"], "endpoint": "update_current_user_workshop_part"})
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
        logger.debug(f"Deleting part {part_id} for user {current_user['user_id']}'s workshop")

        workshop_id = get_current_user_workshop_id(current_user)
        if workshop_id == 1:
            logger.error(f"User {current_user['user_id']} has no workshop to delete part from",
                         extra={"user_id": current_user["user_id"], "endpoint": "delete_current_user_workshop_part"})
            raise HTTPException(status_code=400, detail="User has no workshop to delete parts from")
        
        # Query to get the part in the workshop by ID
        result = await db.execute(
            select(models.PartWorkshop, models.Part)
            .join(models.Part, models.PartWorkshop.part_id == models.Part.part_id)
            .filter(
                models.PartWorkshop.part_id == part_id,
                models.PartWorkshop.workshop_id == workshop_id
            )
        )
        # Query results
        part_data = result.first()
        
        #If part not found, raise 404
        if not part_data:
            logger.error(f"Part {part_id} not found in workshop {workshop_id} for user {current_user['user_id']}",
                            extra={"user_id": current_user["user_id"], "endpoint": "delete_current_user_workshop_part"})
            raise HTTPException(status_code=404, detail="Part not found in this workshop")
        
        part_workshop, part = part_data
        # Delete part from database
        await db.execute(
            delete(models.PartWorkshop).where(
                models.PartWorkshop.part_id == part_id,
                models.PartWorkshop.workshop_id == workshop_id
            )
        )
        await db.commit()

        logger.info(f"Part {part_id} deleted from workshop {workshop_id} for user {current_user['user_id']}")
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
        logger.critical(f"Database error in delete_current_user_workshop_part: {e}",
                        extra={"user_id": current_user["user_id"], "endpoint": "delete_current_user_workshop_part"})
        raise fetchErrorException
