"""Add bank_category column

Revision ID: a2b3c4d5e6f7
Revises: c1e97a9c18c8
Create Date: 2026-05-17

"""
from alembic import op
import sqlalchemy as sa


revision = "a2b3c4d5e6f7"
down_revision = "c1e97a9c18c8"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("bank_category", sa.String(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_transactions_bank_category"),
            ["bank_category"],
            unique=False,
        )

    op.execute(
        "UPDATE transactions SET bank_category = category WHERE bank_category IS NULL"
    )


def downgrade():
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_transactions_bank_category"))
        batch_op.drop_column("bank_category")
