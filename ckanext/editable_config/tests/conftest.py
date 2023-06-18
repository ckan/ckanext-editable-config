from __future__ import annotations
import pytest


@pytest.fixture(scope="session")
def reset_db_once(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("editable_config")


@pytest.fixture()
def clean_db(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("editable_config")
