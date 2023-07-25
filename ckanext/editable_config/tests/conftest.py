from __future__ import annotations

import contextlib
from typing import Any

import pytest
from pytest_factoryboy import register

from ckan import model
from ckan.tests import factories
from ckan.tests.helpers import call_action

from ckanext.editable_config.model import Option
from ckanext.editable_config.shared import apply_config_overrides


@pytest.fixture(autouse=True)
def reset_last_check():
    """Remove freezetime dates in future from config_overrides."""
    apply_config_overrides._last_check = None


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
        action = "editable_config_option_save"

    key = None
    value = None

    @classmethod
    @contextlib.contextmanager
    def autoclean(cls, *args, **kwargs):
        option: dict[str, Any] = cls(*args, **kwargs)
        try:
            yield option
        finally:
            call_action("editable_config_reset", keys=[option["key"]])


@pytest.fixture()
def autoclean_option(option_factory, faker):
    with option_factory.autoclean(
        key="ckan.site_title",
        value=faker.sentence(),
    ) as option:
        yield option


@pytest.fixture()
def with_autoclean():
    yield
    model.Session.query(Option).delete()
    model.Session.commit()
