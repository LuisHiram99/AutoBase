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
    """Fix users sequence to be in sync with existing data."""
    # Reset the sequence to be higher than the current max user_id
    op.execute("SELECT setval('users_user_id_seq', (SELECT COALESCE(MAX(user_id), 0) + 1 FROM users));")


def downgrade() -> None:
    """No rollback needed for sequence fix."""
    pass
