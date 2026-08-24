"""004_document_management

Revision ID: 004_document_management
Revises: 003_postgis
Create Date: 2026-08-23 17:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004_document_management"
down_revision: Union[str, None] = "003_postgis"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("stored_file_name", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("file_path", sa.String(length=500), nullable=True))
    op.add_column("documents", sa.Column("mime_type", sa.String(length=100), nullable=True))
    op.add_column("documents", sa.Column("file_size", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("description", sa.String(length=1000), nullable=True))
    op.add_column("documents", sa.Column("version", sa.String(length=20), nullable=False, server_default="1.0"))


def downgrade() -> None:
    op.drop_column("documents", "version")
    op.drop_column("documents", "description")
    op.drop_column("documents", "file_size")
    op.drop_column("documents", "mime_type")
    op.drop_column("documents", "file_path")
    op.drop_column("documents", "stored_file_name")

