from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from auth import auth
from typing import Annotated
from pathlib import Path  # Add this import

from handler.users import users
from handler.cars import cars
from handler.customers import customers
from handler.workshops import workshops
from handler.customer_car import customer_car
from handler.current_user import current_user
from handler.rate_limiter import limiter
from handler.parts import parts
from handler.workers import workers
from handler.jobs import jobs
from backend.src.logger import logger


description = """
API created for the AutoBase project.
"""

tags_metadata = [
    {
        "name": "auth",
        "description": "Operations related to user authentication and token management.",
    },
    {
        "name": "users",
        "description": "Operations related to user management. Only accessible by admin users.",
    },
    {
        "name": "current_user",
        "description": "Operations related to the currently authenticated user.",
    },
    {
        "name": "customers",
        "description": "Operations related to customer management.",
    },
    {
        "name": "cars",
        "description": "Operations related to car management.",
    },
    {
        "name": "workshops",
        "description": "Operations related to workshop management.",
    },
]

app = FastAPI(
    title="Taller API",
    description=description,
    version="1.0.0",
    openapi_tags=tags_metadata
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) 


# Rate limiting wiring
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Use absolute path to logos directory
logos_path = Path(__file__).parent / "logos"
logos_path.mkdir(exist_ok=True)  # Create if it doesn't exist

app.mount("/logos", StaticFiles(directory=str(logos_path)), name="logos")


api_route = "/api/v1"
# Include routers
app.include_router(auth.router, prefix=api_route, tags=["auth"])
app.include_router(users.router, prefix=api_route, tags=["users"])
app.include_router(current_user.router, prefix=api_route, tags=["current_user"])
app.include_router(customers.router, prefix=api_route, tags=["customers"])
app.include_router(cars.router, prefix=api_route, tags=["cars"])
app.include_router(customer_car.router, prefix=api_route, tags=["customer_car"])
app.include_router(workshops.router, prefix=api_route, tags=["workshops"])
app.include_router(workers.router, prefix=api_route, tags=["workers"])
app.include_router(parts.router, prefix=api_route, tags=["parts"])
app.include_router(jobs.router, prefix=api_route, tags=["jobs"])

@app.get("/")
async def root():
    return {"message": "Welcome to AutoBase API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
