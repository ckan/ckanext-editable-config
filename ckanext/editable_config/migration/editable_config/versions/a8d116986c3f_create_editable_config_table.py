"""create_editable_config_table

Revision ID: a8d116986c3f
Revises:
Create Date: 2023-06-18 18:19:17.682914

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a8d116986c3f"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "editable_config_option",
        sa.Column("key", sa.Text, primary_key=True),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("prev_value", sa.Text, nullable=False),
    )


def downgrade():
    op.drop_table("editable_config_option")
