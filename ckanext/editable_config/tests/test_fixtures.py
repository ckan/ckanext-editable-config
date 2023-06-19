from __future__ import annotations

from unittest.mock import ANY

import pytest

import ckan.plugins.toolkit as tk
from ckan.common import config_declaration as cd


@pytest.mark.usefixtures("with_plugins", "non_clean_db")
class TestOptionFactory:
    def test_key_and_value_required(self, option_factory):
        """OptionFactory requires key and value."""
        with pytest.raises(tk.ValidationError) as e:
            option_factory()

        assert "key" in e.value.error_dict
        assert "value" in e.value.error_dict

    def test_key_cannot_be_undeclared(self, option_factory, faker):
        """Undeclared options are not allowed."""
        while (key := faker.word()) in cd:
            continue

        with pytest.raises(tk.ValidationError) as e:
            option_factory(key=key, value=faker.word())

        assert e.value.error_dict == {key: [ANY]}

    def test_key_must_be_editable(self, option_factory, faker):
        """Non-editable options are not allowed."""
        key = "ckan.site_url"
        with pytest.raises(tk.ValidationError) as e:
            option_factory(key=key, value=faker.word())

        assert e.value.error_dict == {key: [ANY]}

    def test_autoclean(self, option_factory, faker, ckan_config):
        """OptionFactory.autoclean contextmanager removes option and restores
        config.

        """
        title = faker.bothify("editable config title: ??????")
        with option_factory.autoclean(key="ckan.site_title", value=title):
            assert ckan_config["ckan.site_title"] == title

        assert ckan_config["ckan.site_title"] != title
