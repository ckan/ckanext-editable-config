from datetime import timedelta
from typing import get_type_hints

import pytest

from ckan.tests.helpers import call_action

from ckanext.editable_config import config, shared
from ckanext.editable_config.model import Option


def test_optional_dict_is_up_to_date(faker):
    option = Option.set("ckan.site_title", faker.sentence()).as_dict({})
    assert option.keys() == get_type_hints(shared.OptionDict).keys()


@pytest.mark.ckan_config("ckan.requests.timeout", 10)
@pytest.mark.ckan_config("ckan.plugins", ["text_view", "image_view"])
def test_value_as_string():
    assert shared.value_as_string("ckan.site_title", 123) == "123"
    assert shared.value_as_string("ckan.requests.timeout", 123) == "123"
    assert shared.value_as_string("ckan.plugins", ["hello", "world"]) == "hello world"


@pytest.mark.usefixtures("with_plugins", "non_clean_db")
class TestUpdater:
    def test_apply_new_updates(self, faker, ckan_config, freezer, autoclean_option):
        """New updates are applied."""
        freezer.move_to(timedelta(seconds=1))
        key = autoclean_option["key"]
        value = faker.sentence()

        call_action("editable_config_change", options={key: value}, apply=False)
        assert ckan_config[key] != value
        assert shared.apply_config_overrides() == 1
        assert ckan_config[key] == value

    @pytest.mark.ckan_config(config.CHARGE_TIMEOUT, 10)
    def test_charge_timeout(self, faker, freezer, autoclean_option):
        """New updates are applied."""
        freezer.move_to(timedelta(seconds=5))

        call_action(
            "editable_config_change",
            options={autoclean_option["key"]: faker.sentence()},
            apply=False,
        )
        assert shared.apply_config_overrides() == 0

        freezer.move_to(timedelta(seconds=6))
        assert shared.apply_config_overrides() == 1

    def test_apply_old_updates(self, faker, ckan_config, freezer, autoclean_option):
        """Old updates are ignored."""
        freezer.move_to(timedelta(days=-1))
        key = autoclean_option["key"]
        value = faker.sentence()
        call_action("editable_config_change", options={key: value}, apply=False)
        assert shared.apply_config_overrides() == 0
        assert ckan_config[key] != value

    def test_reset_configured_option(self, ckan_config, autoclean_option):
        """Config overrides for option in config file can are removed."""
        key = autoclean_option["key"]
        assert shared.apply_config_overrides(removed_keys=[key]) == 1
        assert ckan_config[key] != autoclean_option["value"]

    def test_reset_added_option(self, faker, ckan_config, option_factory):
        """Config overrides for option not available in the config file are removed."""
        key = "ckan.site_intro_text"

        with option_factory.autoclean(key=key, value=faker.sentence()) as option:
            assert shared.apply_config_overrides(removed_keys=[key]) == 1
            assert ckan_config[key] != option["value"]

    @pytest.mark.ckan_config("ckan.site_title", "hello world")
    def test_reset_original_option(self, faker, ckan_config):
        """Config options can be restored to the state of config file even when
        changed elsewhere.

        """
        key = "ckan.site_title"
        assert ckan_config[key] == "hello world"
        assert shared.apply_config_overrides(removed_keys=[key]) == 1
        assert ckan_config[key] != "hello world"
