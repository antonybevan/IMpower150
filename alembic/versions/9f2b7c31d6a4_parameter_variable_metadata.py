"""Add parameter-level variable metadata

Revision ID: 9f2b7c31d6a4
Revises: f85d3a20e3ac
Create Date: 2026-05-29 21:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '9f2b7c31d6a4'
down_revision = 'f85d3a20e3ac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'parameter_variable_metadata',
        sa.Column('dataset', sa.String(length=50), nullable=False),
        sa.Column('variable', sa.String(length=50), nullable=False),
        sa.Column('paramcd', sa.String(length=8), nullable=False),
        sa.Column('bc_id', sa.String(length=50), nullable=False),
        sa.Column('rule_id', sa.String(length=50), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('origin', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['bc_id'], ['biomedical_concepts.bc_id']),
        sa.ForeignKeyConstraint(['rule_id'], ['derivation_rules.rule_id']),
        sa.PrimaryKeyConstraint('dataset', 'variable', 'paramcd')
    )


def downgrade() -> None:
    op.drop_table('parameter_variable_metadata')
