"""fix delete cascade

Revision ID: 5e408b4b24b9
Revises: bbe2b8f6a080
Create Date: 2025-05-10 23:41:00.779601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e408b4b24b9'
down_revision: Union[str, None] = 'bbe2b8f6a080'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'department_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_constraint('users_department_id_fkey', 'users', type_='foreignkey')
    op.create_foreign_key(None, 'users', 'departments', ['department_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.create_foreign_key('users_department_id_fkey', 'users', 'departments', ['department_id'], ['id'], ondelete='CASCADE')
    op.alter_column('users', 'department_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
