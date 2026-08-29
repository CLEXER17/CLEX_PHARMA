"""initial schema"""


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    from app.db.models import Base
    from app.db.session import engine

    Base.metadata.create_all(engine)


def downgrade():
    from app.db.models import Base
    from app.db.session import engine

    Base.metadata.drop_all(engine)
