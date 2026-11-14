"""Store design prompts as text.

Revision ID: 42ab87c1d9e3
Revises: 9279ad8b0134
Create Date: 2026-11-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "42ab87c1d9e3"
down_revision: Union[str, Sequence[str], None] = "9279ad8b0134"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("design_versions") as batch_op:
            batch_op.alter_column(
                "prompt_used",
                existing_type=sa.DateTime(),
                type_=sa.Text(),
            )
    else:
        op.alter_column(
            "design_versions",
            "prompt_used",
            existing_type=sa.DateTime(),
            type_=sa.Text(),
            postgresql_using="prompt_used::text",
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("design_versions") as batch_op:
            batch_op.alter_column(
                "prompt_used",
                existing_type=sa.Text(),
                type_=sa.DateTime(),
            )
    else:
        op.alter_column(
            "design_versions",
            "prompt_used",
            existing_type=sa.Text(),
            type_=sa.DateTime(),
            postgresql_using="prompt_used::timestamp",
        )
