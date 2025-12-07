"""add_default_workshop

Revision ID: 1ce9fd71484e
Revises: 757e44044a3e
Create Date: 2025-11-06 12:51:54.561381

"""
from typing import Sequence, Union
import os

from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext


# revision identifiers, used by Alembic.
revision: str = '1ce9fd71484e'
down_revision: Union[str, Sequence[str], None] = '757e44044a3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Insert default workshop with ID 1 (always needed as a placeholder)
    op.execute("""
        INSERT INTO workshops (workshop_id, workshop_name, address, opening_hours, closing_hours)
        VALUES (1, 'Default Workshop', 'Default Address', '09:00', '18:00')
        ON CONFLICT (workshop_id) DO NOTHING;
    """)
    
    # Only insert default users in non-production environments
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment != "production":
        # Hash default admin password using passlib (argon2)
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        hashed_admin = pwd_context.hash("admin")
        hashed_manager = pwd_context.hash("manager")

        # Use a connection to execute with parameters
        bind = op.get_bind()
        
        # Insert admin user
        bind.execute(
            sa.text("""
                INSERT INTO users (user_id, first_name, last_name, email, role, hashed_password, workshop_id)
                VALUES (:user_id, :first_name, :last_name, :email, :role, :hashed_password, :workshop_id)
                ON CONFLICT (user_id) DO NOTHING;
            """),
            {
                "user_id": 1,
                "first_name": "Admin",
                "last_name": "User",
                "email": "admin@mail.com",
                "role": "admin",
                "hashed_password": hashed_admin,
                "workshop_id": 1,
            }
        )
        
        # Insert manager user
        bind.execute(
            sa.text("""
                INSERT INTO users (user_id, first_name, last_name, email, role, hashed_password, workshop_id)
                VALUES (:user_id, :first_name, :last_name, :email, :role, :hashed_password, :workshop_id)
                ON CONFLICT (user_id) DO NOTHING;
            """),
            {
                "user_id": 2,
                "first_name": "default_manager",
                "last_name": "default_manager",
                "email": "manager@mail.com",
                "role": "manager",
                "hashed_password": hashed_manager,
                "workshop_id": 1,
            }
        )



def downgrade() -> None:
    """Downgrade schema."""
    # Remove default users
    op.execute("DELETE FROM users WHERE user_id IN (1, 2);")
    # Remove default workshop
    op.execute("DELETE FROM workshops WHERE workshop_id = 1;")
