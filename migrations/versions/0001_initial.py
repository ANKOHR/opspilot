"""Create the initial OpsPilot schema."""

from alembic import op

from opspilot_api import models  # noqa: F401
from opspilot_api.database import Base

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Use the SQLAlchemy metadata as the initial schema source."""
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
