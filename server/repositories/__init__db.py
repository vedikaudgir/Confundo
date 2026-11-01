from sqlalchemy import inspect, text

from server.database import engine


EXPECTED_REVISION = "20261101_0001"


def init_db():
    inspector = inspect(engine)
    if "alembic_version" not in inspector.get_table_names():
        raise RuntimeError(
            "Database migrations have not been applied. Run `alembic upgrade head` before starting the API."
        )
    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
    if revision != EXPECTED_REVISION:
        raise RuntimeError(
            f"Database revision {revision!r} is not current. Run `alembic upgrade head` before starting the API."
        )
