"""create ktp_ocr table

Revision ID: 002
Revises: 001
Create Date: 2026-04-13

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'ktp_ocr',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('ktp_img', sa.String(255), nullable=False, server_default=''),
        sa.Column('raw_text', sa.Text, nullable=False, server_default=''),
        sa.Column('name', sa.String(255), nullable=False, server_default=''),
        sa.Column('nik', sa.String(20), nullable=False, server_default=''),
        sa.Column('province', sa.String(100), nullable=False, server_default=''),
        sa.Column('birthdate', sa.String(200), nullable=False, server_default=''),
        sa.Column('virgin', sa.String(100), nullable=False, server_default=''),
        sa.Column('status', sa.String(100), nullable=False, server_default=''),
        sa.Column('birthplace', sa.String(255), nullable=False, server_default=''),
        sa.Column('city', sa.String(100), nullable=False, server_default=''),
        sa.Column('sub_district', sa.String(100), nullable=False, server_default=''),
        sa.Column('village', sa.String(100), nullable=False, server_default=''),
        sa.Column('address', sa.Text, nullable=False, server_default=''),
        sa.Column('rt', sa.String(10), nullable=False, server_default=''),
        sa.Column('rw', sa.String(10), nullable=False, server_default=''),
        sa.Column('religion', sa.String(100), nullable=False, server_default=''),
        sa.Column('job', sa.String(100), nullable=False, server_default=''),
        sa.Column('citizenship', sa.String(100), nullable=False, server_default=''),
        sa.Column('valid_until', sa.String(100), nullable=False, server_default=''),
        sa.Column('rating', sa.SmallInteger, nullable=False, server_default='0'),
        sa.Column('is_valid', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('is_changed', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

def downgrade() -> None:
    op.drop_table('ktp_ocr')
