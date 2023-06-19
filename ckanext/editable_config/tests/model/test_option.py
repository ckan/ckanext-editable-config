from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import ANY

import pytest

from ckanext.editable_config.model import Option


@pytest.mark.usefixtures("with_plugins", "non_clean_db")
class TestOption:
    def test_get(self, faker, option_factory):
        """Option.get returns exition option or None."""
        with option_factory.autoclean(key="ckan.site_title", value=faker.word()):
            assert Option.get("ckan.site_title")

        assert Option.get("ckan.site_title") is None

    def test_set_undeclared(self, faker):
        """Option.set raises a KeyError for undeclared option."""
        with pytest.raises(KeyError):
            Option.set(faker.bothify("undeclared key: ???"), faker.word())

    def test_set_new(self, faker, option_factory, ckan_config):
        """Option.set creates option but doesn't add it to session.

        Option.prev_value takes the current value from the config.
        """
        key = "ckan.site_url"
        value = faker.url()
        option = Option.set(key, value)
        assert not Option.get(key)

        assert option.key == key
        assert option.value == value
        assert option.prev_value == ckan_config[key]

    def test_set_existing(self, faker, autoclean_option):
        """Option.set updates existing option."""
        value = faker.sentence()
        option = Option.set(autoclean_option["key"], value)
        assert option.key == autoclean_option["key"]
        assert option.value == value

    def test_revert(self, faker, ckan_config):
        """Option.revert swaps current and previous values."""
        key = "ckan.site_url"
        value = faker.url()
        option = Option.set(key, value)
        option.revert()
        assert option.value == ckan_config[key]
        assert option.prev_value == value

    def test_dictize(self, faker, ckan_config):
        """Option.as_dict returns dictionary with option's keys"""
        option = Option.set("ckan.site_title", faker.sentence())
        expected = dict.fromkeys(["key", "value", "updated_at", "prev_value"], ANY)

        assert option.as_dict({}) == expected

    def test_is_updated_since(self, autoclean_option):
        """Option.is_updated_since checks update after specific moment. If
        moment set to None, it checks for any updates.

        """
        assert Option.is_updated_since(None)
        assert Option.is_updated_since(datetime.utcnow() - timedelta(seconds=1))
        assert not Option.is_updated_since(datetime.utcnow() + timedelta(seconds=1))

    @pytest.mark.freeze_time("2020-01-01")
    def test_updated_since_options(self, option_factory, freezer, faker):
        """Option.is_updated_since checks update after specific moment. If
        moment set to None, it checks for any updates.

        """
        assert Option.updated_since(None).count() == 0
        with option_factory.autoclean(
            key="ckan.site_description",
            value=faker.sentence(),
        ):
            assert Option.updated_since(None).count() == 1
            freezer.move_to("2020-02-01")

            with option_factory.autoclean(
                key="ckan.site_title",
                value=faker.sentence(),
            ):
                assert Option.updated_since(None).count() == 2

                assert Option.updated_since(datetime(2020, 1, 10)).count() == 1
                assert Option.updated_since(datetime(2020, 2, 10)).count() == 0
