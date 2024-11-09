"""init db

Revision ID: 6a229d505bbb
Revises: 
Create Date: 2024-05-27 14:25:33.252903

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a229d505bbb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('first_name', sa.String(), nullable=False),
    sa.Column('last_name', sa.String(), nullable=True),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('language_code', sa.String(), nullable=True),
    sa.Column('referrer', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
    sa.Column('external_id', sa.String(), nullable=True),
    sa.Column('camunda_user_id', sa.String(), nullable=True),
    sa.Column('camunda_key', sa.UUID(), nullable=False),
    sa.Column('telegram_user_id', sa.BIGINT(), nullable=True),
    sa.Column('webapp_user_id', sa.String(), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=False),
    sa.Column('is_suspicious', sa.Boolean(), nullable=False),
    sa.Column('is_block', sa.Boolean(), nullable=False),
    sa.Column('is_premium', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id', 'camunda_key'),
    sa.UniqueConstraint('camunda_user_id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('telegram_user_id'),
    sa.UniqueConstraint('webapp_user_id')
    )
    op.create_table('art',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
    sa.Column('img_picture', sa.String(), nullable=True),
    sa.Column('description_prompt', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('parent_id', sa.UUID(), nullable=True),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('reference_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('artcollection',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('symbol', sa.String(), nullable=True),
    sa.Column('base_uri', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('arts', sa.JSON(none_as_null=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('event',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('address', sa.String(), nullable=True),
    sa.Column('location', sa.String(), nullable=True),
    sa.Column('img_event_cover', sa.String(), nullable=True),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('reference_id', sa.UUID(), nullable=True),
    sa.Column('collections', sa.JSON(none_as_null=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('external_workers',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('schema', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
    sa.Column('img_picture', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('parent_id', sa.UUID(), nullable=True),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('reference_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('invite',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('strategy',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('schema', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text("TIMEZONE('utc', now())"), nullable=False),
    sa.Column('img_picture', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('parent_id', sa.UUID(), nullable=True),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('reference_id', sa.UUID(), nullable=True),
    sa.Column('total_pnl', sa.Float(), nullable=True),
    sa.Column('drawdown', sa.Float(), nullable=True),
    sa.Column('win_rate', sa.Float(), nullable=True),
    sa.Column('profit_factor', sa.Float(), nullable=True),
    sa.Column('expectancy', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('strategy')
    op.drop_table('invite')
    op.drop_table('external_workers')
    op.drop_table('event')
    op.drop_table('artcollection')
    op.drop_table('art')
    op.drop_table('user')
    # ### end Alembic commands ###
