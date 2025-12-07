from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum


class RoleEnum(str, Enum):
    admin = "admin"
    manager = "manager"
    worker = "worker"




# --------------------- Customer ----------------------
# Base Pydantic Models (For Create/Update operations)

class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: Optional[str] = None
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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    workshop_id: Optional[int] = None

class CustomerCreateForWorkshop(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: Optional[str] = None

class CustomerUpdateForWorkshop(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: Optional[str] = None


# --------------------- End of Customer ----------------------

# --------------------- User ----------------------

class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
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
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    password: str  # plain password for creation; will be hashed in the handler
    role: RoleEnum
    workshop_id: int

    model_config = {"json_schema_extra": {"example": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "password": "secretpassword",
        "role": "admin",
        "workshop_id": 1
    }}}

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[RoleEnum] = None
    workshop_id: Optional[int] = None

class CurrentUserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None

class CurrentUserPassword(BaseModel):
    old_password: str
    new_password: str

# --------------------- Car and CustomerCar ----------------------


class CarBase(BaseModel):
    year: int
    brand: str
    model: str

class Car(CarBase):
    car_id: int

    model_config = {"from_attributes": True}


class CarCreate(CarBase):
    pass

class CarUpdate(BaseModel):
    year: Optional[int] = None
    brand: Optional[str] = None
    model: Optional[str] = None

# ---
class CustomerCarBase(BaseModel):
    customer_id: int
    car_id: int
    license_plate: str
    color: Optional[str] = None

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
    year: int
    brand: str
    model: str

class CustomerCarCreate(CustomerCarBase):
    pass

class CustomerCarUpdate(CustomerCarBase):
    pass

class CustomerCarResponse(BaseModel):
    customer_car_id: int
    customer_id: int
    car_id: int
    license_plate: str
    color: Optional[str] = None

    model_config = {"from_attributes": True}

class CustomerCarAssign(BaseModel):
    car_id: int
    license_plate: str
    color: Optional[str] = None




# ---------------------- Workshop ----------------------
class WorkshopBase(BaseModel):
    workshop_name: str
    address: Optional[str] = None
    opening_hours: Optional[str] = None
    closing_hours: Optional[str] = None


class Workshop(WorkshopBase):
    workshop_id: int

    model_config = {"from_attributes": True}


class WorkshopCreate(WorkshopBase):
    pass


class WorkshopUpdate(BaseModel):
    workshop_name: Optional[str] = None
    address: Optional[str] = None
    opening_hours: Optional[str] = None
    closing_hours: Optional[str] = None

#---------------------- Part and PartWorkshop ----------------------
class PartBase(BaseModel):
    part_name: str
    brand: str
    description: Optional[str] = None
    category: Optional[str] = None

class Part(PartBase):
    part_id: int

    model_config = {"from_attributes": True}

class PartCreate(PartBase):
    pass

class PartUpdate(BaseModel):
    part_name: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

# ---------------------- PartWorkshop ----------------------

class PartWorkshopBase(BaseModel):
    part_id: int
    quantity: int
    purchase_price: int
    sale_price: int

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
    quantity: Optional[int] = None
    purchase_price: Optional[int] = None
    sale_price: Optional[int] = None

# --------------------- End of Part and PartWorkshop ----------------------

# --------------------- Worker ----------------------
class WorkerBase(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    position: str
    nickname: Optional[str] = None
    workshop_id: int

class Worker(WorkerBase):
    worker_id : int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class WorkerCreate(WorkerBase):
    workshop_id: int

class WorkerCreateForWorkshop(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    position: str
    nickname: Optional[str] = None

class WorkerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    nickname: Optional[str] = None

# --------------------- End of Worker ----------------------

# --------------------- Jobs ----------------------
class StatusEnum(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class JobBase(BaseModel):
    invoice: str
    service_description: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    status: StatusEnum

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
    invoice: Optional[str] = None
    service_description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
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