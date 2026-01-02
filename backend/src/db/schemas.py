from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from enum import Enum


class RoleEnum(str, Enum):
    admin = "admin"
    manager = "manager"
    worker = "worker"




# --------------------- Customer ----------------------
# Base Pydantic Models (For Create/Update operations)

class CustomerBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=1, max_length=20)
    email: Optional[EmailStr] = Field(None, max_length=100)
    workshop_id: int 

class Customer(CustomerBase):
    customer_id: int
    workshop_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

# Models for creating new records
class CustomerCreate(CustomerBase):
    workshop_id: int

class CustomerUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, min_length=1, max_length=20)
    email: Optional[EmailStr] = Field(None, max_length=100)
    workshop_id: Optional[int] = None

class CustomerCreateForWorkshop(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=1, max_length=20)
    email: Optional[str] = Field(None, max_length=100)

class CustomerUpdateForWorkshop(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=1, max_length=20)
    email: Optional[str] = Field(None, max_length=100)


# --------------------- End of Customer ----------------------

# --------------------- User ----------------------

class UserBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = Field(None, max_length=100)
    role: RoleEnum 
    workshop_id: int

class User(UserBase):
    user_id: int

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"example": {
            "user_id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "role": "admin",
            "workshop_id": 1
        }}
    }

class UserCreate(BaseModel):
    first_name: str = Field(..., example="John", min_length=2, max_length=100)
    last_name: str = Field(..., example="Doe", min_length=2, max_length=100)
    email: EmailStr = Field(..., example="john@example.com", max_length=100)
    password: str = Field(..., example="Secretpassword12!", min_length=10, max_length=100)
    role: RoleEnum
    workshop_id: int

    model_config = {"json_schema_extra": {"example": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "password": "Secretpassword1!",
        "role": "admin",
        "workshop_id": 1
    }}}


    
    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, v):
        if v is None:
            return v
        
        errors = []
        if not any(c.isupper() for c in v):
            errors.append('uppercase letter')
        if not any(c.islower() for c in v):
            errors.append('lowercase letter')
        if not any(c.isdigit() for c in v):
            errors.append('number')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            errors.append('special character')
        
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        return v

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=10, max_length=100)

    role: Optional[RoleEnum] = None
    workshop_id: Optional[int] = None

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, v):
        if v is None:
            return v
        
        errors = []
        if not any(c.isupper() for c in v):
            errors.append('uppercase letter')
        if not any(c.islower() for c in v):
            errors.append('lowercase letter')
        if not any(c.isdigit() for c in v):
            errors.append('number')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            errors.append('special character')
        
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        return v

class CurrentUserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, example="John", min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, example="Doe", min_length=2, max_length=100)
    email: Optional[EmailStr] = Field(None, example="john@example.com", max_length=100)

class CurrentUserPassword(BaseModel):
    old_password: str = Field(..., example="Oldpassword1!", min_length=10, max_length=100)
    new_password: str = Field(..., example="Newpassword1!", min_length=10, max_length=100)

    @field_validator('new_password')
    @classmethod
    def validate_password_complexity(cls, v):
        if v is None:
            return v
        
        errors = []
        if not any(c.isupper() for c in v):
            errors.append('uppercase letter')
        if not any(c.islower() for c in v):
            errors.append('lowercase letter')
        if not any(c.isdigit() for c in v):
            errors.append('number')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            errors.append('special character')
        
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        return v
    
# --------------------- Car and CustomerCar ----------------------


class CarBase(BaseModel):
    year: int = Field(..., ge=1900, le=datetime.now().year + 1)
    brand: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)

class Car(CarBase):
    car_id: int

    model_config = {"from_attributes": True}


class CarCreate(CarBase):
    pass

class CarUpdate(BaseModel):
    year: Optional[int] = Field(None, ge=1900, le=datetime.now().year + 1)
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    model: Optional[str] = Field(None, min_length=1, max_length=100)

# ---
class CustomerCarBase(BaseModel):
    customer_id: int
    car_id: int
    license_plate: str = Field(..., min_length=1, max_length=20)
    color: Optional[str] = Field(None, max_length=50)

class CustomerCar(CustomerCarBase):
    customer_car_id: int

    model_config = {"from_attributes": True}

class CustomerCarWithCarInfo(CustomerCarBase):
    customer_car_id: int
    car_brand: str
    car_model: str
    car_year: int

    model_config = {"from_attributes": True}

class CarCreateForWorkshop(BaseModel):
    year: int = Field(..., ge=1900, le=datetime.now().year + 1)
    brand: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)

class CustomerCarCreate(CustomerCarBase):
    pass

class CustomerCarUpdate(CustomerCarBase):
    pass

class CustomerCarResponse(BaseModel):
    customer_car_id: int
    customer_id: int
    car_id: int
    license_plate: str = Field(..., min_length=1, max_length=20)
    color: Optional[str] = Field(None, max_length=50)

    model_config = {"from_attributes": True}

class CustomerCarAssign(BaseModel):
    car_id: int
    license_plate: str = Field(..., min_length=1, max_length=20)
    color: Optional[str] = Field(None, max_length=50)




# ---------------------- Workshop ----------------------
class WorkshopBase(BaseModel):
    workshop_name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=200)
    opening_hours: Optional[str] = Field(None, max_length=20)
    closing_hours: Optional[str] = Field(None, max_length=20)
    workshop_logo: Optional[str] = Field(None, max_length=255)


class Workshop(WorkshopBase):
    workshop_id: int

    model_config = {"from_attributes": True}


class WorkshopCreate(WorkshopBase):
    pass


class WorkshopUpdate(BaseModel):
    workshop_name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=200)
    opening_hours: Optional[str] = Field(None, max_length=20)
    closing_hours: Optional[str] = Field(None, max_length=20)

class WorkshopLogo(BaseModel):
    workshop_id: int
    workshop_logo: Optional[str] = None

    model_config = {"from_attributes": True}

class WorkshopLogoUpdate(BaseModel):
    # This schema is not needed for file uploads since we use UploadFile
    # But keeping it for backwards compatibility if needed elsewhere
    workshop_logo: Optional[str] = None

#---------------------- Part and PartWorkshop ----------------------
class PartBase(BaseModel):
    part_name: str = Field(..., min_length=1, max_length=100)
    brand: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)

class Part(PartBase):
    part_id: int

    model_config = {"from_attributes": True}

class PartCreate(PartBase):
    pass

class PartUpdate(BaseModel):
    part_name: Optional[str] = Field(None, min_length=1, max_length=100)
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)

# ---------------------- PartWorkshop ----------------------

class PartWorkshopBase(BaseModel):
    part_id: int = Field(..., ge=0)
    quantity: int = Field(..., ge=0)
    purchase_price: int = Field(..., ge=0)
    sale_price: int = Field(..., ge=0)

class PartWorkshop(PartBase):
    part_id: int
    workshop_id: int
    quantity: int
    purchase_price: int
    sale_price: int

    model_config = {"from_attributes": True}

class PartWorkshopCreate(PartWorkshopBase):
    pass

class PartWorkshopUpdate(BaseModel):
    quantity: Optional[int] = Field(None, ge=0)
    purchase_price: Optional[int] = Field(None, ge=0)
    sale_price: Optional[int] = Field(None, ge=0)

# --------------------- End of Part and PartWorkshop ----------------------

# --------------------- Worker ----------------------
class WorkerBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    position: str = Field(..., min_length=1, max_length=100)
    nickname: Optional[str] = Field(None, max_length=50)
    workshop_id: int

class Worker(WorkerBase):
    worker_id : int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class WorkerCreate(WorkerBase):
    workshop_id: int

class WorkerCreateForWorkshop(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    position: str = Field(..., min_length=1, max_length=100)
    nickname: Optional[str] = Field(None, max_length=50)
    
class WorkerUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, min_length=1, max_length=100)
    nickname: Optional[str] = Field(None, max_length=50)
# --------------------- End of Worker ----------------------

# --------------------- Jobs ----------------------
class StatusEnum(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class JobBase(BaseModel):
    invoice: str = Field(..., min_length=1, max_length=100)
    service_description: Optional[str] = Field(None, max_length=255)
    start_date: str = Field(..., min_length=1, max_length=20)
    end_date: Optional[str] = Field(None, max_length=20)
    status: StatusEnum = Field(...)

class Job(JobBase):
    job_id: int
    workshop_id: int
    customer_car_id: int

    model_config = {"from_attributes": True}

class JobWithCarInfo(JobBase):
    job_id: int
    workshop_id: int
    customer_car_id: int
    car_brand: str
    car_model: str
    car_year: int
    license_plate: str
    car_color: Optional[str] = None

    model_config = {"from_attributes": True}

class JobCreate(BaseModel):
    customer_car_id: int
    invoice: str
    service_description: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    status: StatusEnum
    workshop_id: int

class JobCreateForWorkshop(BaseModel):
    customer_car_id: int
    invoice: str
    service_description: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    status: StatusEnum

class JobUpdate(BaseModel):
    invoice: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r'^[A-Z0-9\-_]+$')
    service_description: Optional[str] = Field(None, max_length=255)
    start_date: Optional[str] = Field(None, min_length=1, max_length=20)
    end_date: Optional[str] = Field(None, max_length=20)
    status: Optional[StatusEnum] = None

# --------------------- Job Parts ----------------------
class JobPartsBase(BaseModel):
    job_id: int
    part_id: int
    quantity_used: int = 1

class JobParts(JobPartsBase):
    model_config = {"from_attributes": True}

class JobPartsCreate(BaseModel):
    part_id: int
    quantity_used: int = 1

class JobPartsUpdate(BaseModel):
    quantity_used: Optional[int] = None

# --------------------- Job Workers ----------------------
class JobWorkersBase(BaseModel):
    job_id: int
    worker_id: int
    job_role: str

class JobWorkers(JobWorkersBase):
    model_config = {"from_attributes": True}

class JobWorkersCreate(BaseModel):
    worker_id: int
    job_role: str

class JobWorkersUpdate(BaseModel):
    job_role: Optional[str] = None

# --------------------- End of Jobs ----------------------