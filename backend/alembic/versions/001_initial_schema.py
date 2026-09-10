"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-10 19:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Complaints Table
    op.create_table(
        'complaints',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'COMMITTED', name='complaintstatus', native_enum=False), nullable=False),
        sa.Column('qms_reference_number', sa.String(length=50), nullable=True),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('complaint_source', sa.String(length=100), nullable=True),
        sa.Column('contact_info', sa.String(length=255), nullable=True),
        sa.Column('complaint_date', sa.String(length=50), nullable=True),
        sa.Column('product_name', sa.String(length=255), nullable=True),
        sa.Column('strength_grade', sa.String(length=100), nullable=True),
        sa.Column('batch_number', sa.String(length=100), nullable=True),
        sa.Column('manufacturing_date', sa.String(length=50), nullable=True),
        sa.Column('expiry_date', sa.String(length=50), nullable=True),
        sa.Column('affected_quantity', sa.String(length=100), nullable=True),
        sa.Column('manufacturing_facility', sa.String(length=255), nullable=True),
        sa.Column('packaging_info', sa.String(length=255), nullable=True),
        sa.Column('complaint_category', sa.String(length=100), nullable=True),
        sa.Column('defect_type', sa.String(length=100), nullable=True),
        sa.Column('complaint_description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('qms_reference_number')
    )
    op.create_index(op.f('ix_complaints_batch_number'), 'complaints', ['batch_number'], unique=False)
    op.create_index(op.f('ix_complaints_created_at'), 'complaints', ['created_at'], unique=False)
    op.create_index(op.f('ix_complaints_customer_name'), 'complaints', ['customer_name'], unique=False)
    op.create_index(op.f('ix_complaints_product_name'), 'complaints', ['product_name'], unique=False)
    op.create_index(op.f('ix_complaints_status'), 'complaints', ['status'], unique=False)

    # 2. Risk Assessments Table
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('complaint_id', sa.String(length=36), nullable=False),
        sa.Column('severity_suggested', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='riskseverity', native_enum=False), nullable=False),
        sa.Column('complaint_category', sa.String(length=100), nullable=False),
        sa.Column('suggested_next_action', sa.Text(), nullable=False),
        sa.Column('risk_details', sa.Text(), nullable=False),
        sa.Column('requires_quarantine', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('complaint_id')
    )

    # 3. Complaint Documents Table
    op.create_table(
        'complaint_documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('complaint_id', sa.String(length=36), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. QMS Ledger Table
    op.create_table(
        'qms_ledger',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('complaint_id', sa.String(length=36), nullable=False),
        sa.Column('qms_reference_number', sa.String(length=50), nullable=False),
        sa.Column('committed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('frozen_payload_json', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('complaint_id'),
        sa.UniqueConstraint('qms_reference_number')
    )


def downgrade() -> None:
    op.drop_table('qms_ledger')
    op.drop_table('complaint_documents')
    op.drop_table('risk_assessments')
    op.drop_index(op.f('ix_complaints_status'), table_name='complaints')
    op.drop_index(op.f('ix_complaints_product_name'), table_name='complaints')
    op.drop_index(op.f('ix_complaints_customer_name'), table_name='complaints')
    op.drop_index(op.f('ix_complaints_created_at'), table_name='complaints')
    op.drop_index(op.f('ix_complaints_batch_number'), table_name='complaints')
    op.drop_table('complaints')
