"""changin User model

Revision ID: 7315bec58a0c
Revises: 2da2b9a16a2f
Create Date: 2024-04-07 23:40:13.454847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7315bec58a0c'
down_revision: Union[str, None] = '2da2b9a16a2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'art_description_prompt')
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))
    op.add_column('users', sa.Column('camunda_user_id', sa.String(), nullable=False))
    op.add_column('users', sa.Column('camunda_key', sa.String(), nullable=False))
    op.add_column('users', sa.Column('telegram_user_id', sa.String(), nullable=False))
    op.add_column('users', sa.Column('webapp_user_id', sa.String(), nullable=False))
    op.alter_column('users', 'id',
               existing_type=sa.INTEGER(),
               type_=sa.String(),
               existing_nullable=False)
    op.drop_constraint('users_id_key', 'users', type_='unique')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('users_id_key', 'users', ['id'])
    op.alter_column('users', 'id',
               existing_type=sa.String(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.drop_column('users', 'webapp_user_id')
    op.drop_column('users', 'telegram_user_id')
    op.drop_column('users', 'camunda_key')
    op.drop_column('users', 'camunda_user_id')
    op.drop_column('users', 'email')
    op.add_column('events', sa.Column('art_description_prompt', sa.VARCHAR(), autoincrement=False, nullable=True))
