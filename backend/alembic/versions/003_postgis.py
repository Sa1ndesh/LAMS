"""003_postgis

Revision ID: 003_postgis
Revises: 002_authentication
Create Date: 2026-08-23 15:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_postgis"
down_revision: Union[str, None] = "002_authentication"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        op.execute("ALTER TABLE land_parcels ADD COLUMN IF NOT EXISTS geometry geometry(Polygon, 4326);")
        op.execute("CREATE INDEX IF NOT EXISTS idx_land_parcels_geometry ON land_parcels USING GIST (geometry);")
    else:
        with op.batch_alter_table("land_parcels") as batch_op:
            batch_op.add_column(sa.Column("geometry", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        op.execute("DROP INDEX IF EXISTS idx_land_parcels_geometry;")
        op.execute("ALTER TABLE land_parcels DROP COLUMN IF EXISTS geometry;")
    else:
        with op.batch_alter_table("land_parcels") as batch_op:
            batch_op.drop_column("geometry")

