"""Add lab links to all tables

Revision ID: 7d748ec74c5e
Revises: 36c8d561bb98
Create Date: 2025-07-16 15:53:08.324479
"""

from typing import Sequence, Union

revision = '7d748ec74c5e'
down_revision = '36c8d561bb98'
branch_labels = None
depends_on = None


from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('equipment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('laboratory_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_equipment_lab', 'laboratories', ['laboratory_id'], ['id'])

    with op.batch_alter_table('patients', schema=None) as batch_op:
        batch_op.add_column(sa.Column('laboratory_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_patients_lab', 'laboratories', ['laboratory_id'], ['id'])

    with op.batch_alter_table('test_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('laboratory_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_testrequests_lab', 'laboratories', ['laboratory_id'], ['id'])

    with op.batch_alter_table('test_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('laboratory_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_testresults_lab', 'laboratories', ['laboratory_id'], ['id'])

