"""fix_users_sequence

Revision ID: ee93e3a80623
Revises: 8a4aa8ecf943
Create Date: 2025-12-26 16:21:26.129014

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee93e3a80623'
down_revision: Union[str, Sequence[str], None] = '8a4aa8ecf943'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix all sequences to be in sync with existing data."""
    # Reset all sequences to be higher than the current max id values
    op.execute("SELECT setval('users_user_id_seq', (SELECT COALESCE(MAX(user_id), 0) + 1 FROM users));")
    op.execute("SELECT setval('workshops_workshop_id_seq', (SELECT COALESCE(MAX(workshop_id), 0) + 1 FROM workshops));")
    op.execute("SELECT setval('customers_customer_id_seq', (SELECT COALESCE(MAX(customer_id), 0) + 1 FROM customers));")
    op.execute("SELECT setval('workers_worker_id_seq', (SELECT COALESCE(MAX(worker_id), 0) + 1 FROM workers));")
    op.execute("SELECT setval('cars_car_id_seq', (SELECT COALESCE(MAX(car_id), 0) + 1 FROM cars));")
    op.execute("SELECT setval('customer_car_customer_car_id_seq', (SELECT COALESCE(MAX(customer_car_id), 0) + 1 FROM customer_car));")
    op.execute("SELECT setval('parts_part_id_seq', (SELECT COALESCE(MAX(part_id), 0) + 1 FROM parts));")
    op.execute("SELECT setval('jobs_job_id_seq', (SELECT COALESCE(MAX(job_id), 0) + 1 FROM jobs));")


def downgrade() -> None:
    """No rollback needed for sequence fix."""
    pass
