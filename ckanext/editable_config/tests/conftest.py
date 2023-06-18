from __future__ import annotations

import pytest
from pytest_factoryboy import register

from ckan.tests import factories

from ckanext.editable_config.model import Option


@pytest.fixture(scope="session")
def reset_db_once(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("editable_config")


@pytest.fixture()
def clean_db(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("editable_config")


@register
class OptionFactory(factories.CKANFactory):
    class Meta:
        model = Option
        action = "editable_config_create"

    key = None
    value = None
