import pytest

import ckan.plugins.toolkit as tk
from ckan.tests.helpers import call_action

from ckanext.editable_config import config, shared


@pytest.mark.ckan_config(config.WHITELIST, ["ckan.site_title", "ckan.site_description"])
@pytest.mark.usefixtures("with_plugins", "non_clean_db")
class TestList:
    def test_default(self):
        result = call_action("editable_config_list")
        assert set(result) == {"ckan.site_title", "ckan.site_description"}

    def test_pattern(self):
        result = call_action("editable_config_list", pattern="*title")
        assert set(result) == {"ckan.site_title"}


@pytest.mark.usefixtures("with_plugins", "non_clean_db", "with_autoclean")
class TestUpdate:
    def test_empty(self):
        result = call_action("editable_config_update")
        assert not any(v for v in result.values())
        assert shared.apply_config_overrides() == 0

    def test_one_per_group(self, faker, option_factory, ckan_config):
        revert_option = option_factory(
            key="ckan.site_description",
            value=faker.sentence(),
        )
        reset_option = option_factory(key="ckan.site_about", value=faker.sentence())

        result = call_action(
            "editable_config_update",
            change={"ckan.site_title": faker.sentence()},
            revert=[revert_option["key"]],
            reset=[reset_option["key"]],
            apply=False,
        )

        assert shared.apply_config_overrides(removed_keys=result["reset"]) == 3

        assert (
            ckan_config["ckan.site_title"]
            == result["change"]["ckan.site_title"]["value"]
        )
        assert ckan_config[revert_option["key"]] == revert_option["prev_value"]
        assert ckan_config[reset_option["key"]] is None


@pytest.mark.usefixtures("with_plugins", "non_clean_db", "with_autoclean")
class TestChange:
    def test_undeclared(self, option_factory, faker):
        """Undeclared options are not allowed."""
        with pytest.raises(tk.ValidationError):
            call_action("editable_config_change", options={faker.word(): faker.word()})

    def test_not_editable(self, option_factory, faker):
        """Non-editable options are not allowed."""
        with pytest.raises(tk.ValidationError):
            call_action(
                "editable_config_change",
                options={"ckan.site_url": faker.url()},
            )

    @pytest.mark.ckan_config(config.EXTRA_EDITABLE, "ckan.datasets_per_page")
    def test_invalid(self, option_factory, faker):
        """Options are validated"""
        with pytest.raises(tk.ValidationError):
            call_action(
                "editable_config_change",
                options={"ckan.datasets_per_page": faker.word()},
            )

    def test_valid(self, faker, ckan_config):
        """It works with valid option."""
        title = faker.sentence()
        call_action("editable_config_change", options={"ckan.site_title": title})
        assert ckan_config["ckan.site_title"] == title

    @pytest.mark.ckan_config(config.EXTRA_EDITABLE, "ckan.datasets_per_page")
    @pytest.mark.ckan_config(
        config.ADDITIONAL_VALIDATORS,
        {"ckan.datasets_per_page": "is_positive_integer"},
    )
    def test_additional_validators(self):
        """Options are validated"""
        with pytest.raises(tk.ValidationError):
            call_action(
                "editable_config_change",
                options={"ckan.datasets_per_page": -1},
            )
        call_action(
            "editable_config_change",
            options={"ckan.datasets_per_page": 1},
        )


@pytest.mark.usefixtures("with_plugins", "non_clean_db", "with_autoclean")
class TestRevert:
    def test_revert_missing(self):
        with pytest.raises(tk.ObjectNotFound):
            call_action("editable_config_revert", keys=["ckan.site_title"])

    def test_revert_initial(self, ckan_config, faker, option_factory):
        initial = ckan_config["ckan.site_title"]
        updated = faker.sentence()
        option_factory(key="ckan.site_title", value=updated)

        result = call_action("editable_config_revert", keys=["ckan.site_title"])
        assert result["ckan.site_title"]["value"] == initial
        assert result["ckan.site_title"]["prev_value"] == updated


@pytest.mark.usefixtures("with_plugins", "non_clean_db", "with_autoclean")
class TestReset:
    def test_reset_missing(self):
        with pytest.raises(tk.ObjectNotFound):
            call_action("editable_config_reset", keys=["ckan.site_title"])

    def test_resert_initial(self, ckan_config, faker, option_factory):
        initial = ckan_config["ckan.site_title"]
        updated = faker.sentence()
        option_factory(key="ckan.site_title", value=updated)

        result = call_action("editable_config_reset", keys=["ckan.site_title"])
        assert result["ckan.site_title"]["value"] == updated
        assert result["ckan.site_title"]["prev_value"] == initial
        assert ckan_config["ckan.site_title"] == initial
