from sqlalchemy.orm import configure_mappers

from app import models  # noqa: F401


def test_model_mappers_configure() -> None:
    configure_mappers()
