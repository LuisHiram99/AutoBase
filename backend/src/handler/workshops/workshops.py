from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List 
from auth.auth import get_current_user, is_admin, admin_required
from . import service
from ..rate_limiter import limiter


from db import models, schemas
from db.database import get_db

router = APIRouter()


# ---------------- All workshop endpoints ----------------
@router.post("/workshops/", response_model=schemas.Workshop, summary="Create new Workshop")
@limiter.limit("15/minute")
async def create_workshop( 
    request: Request,
    workshop: schemas.WorkshopCreate, 
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    """ 
    Create a new workshop
    """
    if not is_admin(current_user):
        return await service.create_current_user_workshop(current_user, workshop, db)
    else:
        return await service.create_workshop(workshop, db, current_user)

@router.get("/workshops/", response_model=List[schemas.Workshop])
@limiter.limit("15/minute")
async def read_workshops(
    request: Request,
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(get_current_user), 
    skip: int = 0, 
    limit: int = 100):
    """
    Get all workshops with pagination
    """
    if not is_admin(current_user):
        return await service.get_current_user_workshop(current_user, db)
    else:
        return await service.get_all_workshops(db, current_user, skip, limit)
    
@router.post("/workshops/logo", response_model=schemas.Workshop)
@limiter.limit("15/minute")
async def upload_workshop_logo(
    request: Request,
    logo_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    """
    Upload or update the logo of the current user's workshop
    """
    return await service.upload_current_user_workshop_logo(current_user, logo_file, db)
    
@router.get("/workshops/logo", response_model=schemas.WorkshopLogo)
@limiter.limit("15/minute")
async def get_workshop_logo(
    request: Request,
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    """
    Get the logo of the current user's workshop
    """
    return await service.get_current_user_workshop_logo(current_user, db)



# ---------------- Current user's workshop parts endpoint (must be before {workshop_id} routes) ----------------
@router.post("/workshops/parts", response_model=schemas.PartWorkshop, summary="Create part for current user's workshop")
@limiter.limit("15/minute")
async def create_current_user_workshop_part(
    request: Request,
    part: schemas.PartWorkshopCreate,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
    
):
    """
    Create a part associated with the currently authenticated user's workshop
    """
    return await service.create_current_user_workshop_part(user, part, db)

@router.get("/workshops/parts", response_model=List[schemas.PartWorkshop], summary="Get parts of current user's workshop")
@limiter.limit("15/minute")
async def read_current_user_workshop_parts(
    request: Request,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the parts associated with the currently authenticated user's workshop
    """
    return await service.get_current_user_workshop_parts(user, db)

@router.patch("/workshops/parts/{part_id}", response_model=schemas.PartWorkshop, summary="Update part of current user's workshop")
@limiter.limit("15/minute")
async def update_current_user_workshop_part(
    request: Request,
    part_id: int,
    part_update: schemas.PartWorkshopUpdate,
    user = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """
    Update a part associated with the currently authenticated user's workshop
    """
    return await service.update_current_user_workshop_part(user, part_id, part_update, db)

@router.delete("/workshops/parts/{part_id}", response_model=schemas.PartWorkshop, summary="Delete part of current user's workshop")
@limiter.limit("15/minute")
async def delete_current_user_workshop_part(
    request: Request,
    part_id: int,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a part associated with the currently authenticated user's workshop
    """
    return await service.delete_current_user_workshop_part(user, part_id, db)

    
@router.patch("/workshops/me", response_model=schemas.Workshop)
@limiter.limit("15/minute")
async def update_current_user_workshop(
    request: Request,
    workshop_update: schemas.WorkshopUpdate, 
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    """
    Update the current user's workshop information
    """
    return await service.patch_current_user_workshop(current_user, workshop_update, db)

@router.get("/workshops/{workshop_id}", response_model=schemas.Workshop)
@limiter.limit("15/minute")
async def read_workshop(
    request: Request,
    workshop_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(admin_required)):
    """
    Get a specific workshop by ID
    """
    return await service.get_workshop_by_id(workshop_id, db, current_user)

@router.patch("/workshops/{workshop_id}", response_model=schemas.Workshop)
@limiter.limit("15/minute")
async def update_workshop(
    request: Request,
    workshop_id: int, 
    workshop_update: schemas.WorkshopUpdate, 
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(admin_required)
):
    """
    Update a workshop's information
    """
    return await service.update_workshop(workshop_id, workshop_update, db, current_user)

@router.delete("/workshops/{workshop_id}", response_model=schemas.Workshop)
@limiter.limit("15/minute")
async def delete_workshop(
    request: Request,
    workshop_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user = Depends(admin_required)):
    """
    Delete a workshop
    """
    return await service.delete_workshop(workshop_id, db, current_user)

# ---------------- End of current user's workshop parts endpoints ----------------