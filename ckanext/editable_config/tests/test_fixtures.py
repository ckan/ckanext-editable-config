from __future__ import annotations

from unittest.mock import ANY

import pytest

import ckan.plugins.toolkit as tk
from ckan.common import config_declaration as cd


@pytest.mark.usefixtures("with_plugins", "non_clean_db")
class TestOptionFactory:
    def test_key_and_value_required(self, option_factory):
        with pytest.raises(tk.ValidationError) as e:
            option_factory()

        assert "key" in e.value.error_dict
        assert "value" in e.value.error_dict

    def test_key_cannot_be_undeclared(self, option_factory, faker):
        while (key := faker.word()) in cd:
            continue

        with pytest.raises(tk.ValidationError) as e:
            option_factory(key=key, value=faker.word())

        assert e.value.error_dict == {key: [ANY]}

    def test_key_valid_option(self, option_factory, faker):
        assert option_factory(key="ckan.site_title", value="hello")
