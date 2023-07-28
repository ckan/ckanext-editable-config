from __future__ import annotations

import ckan.plugins.toolkit as tk

EXTRA_EDITABLE = "ckanext.editable_config.options.extra_editable"
WHITELIST = "ckanext.editable_config.options.whitelist"
BLACKLIST = "ckanext.editable_config.options.blacklist"
CHARGE_TIMEOUT = "ckanext.editable_config.charge_timeout"
REPLACE_CONFIG_TAB = "ckanext.editable_config.replace_admin_config_tab"
DISABLE_CONFIG_TAB = "ckanext.editable_config.disable_admin_config_tab"
CONVERT_CORE_OVERRIDES = "ckanext.editable_config.convert_core_overrides"
ADDITIONAL_VALIDATORS = "ckanext.editable_config.additional_validators"


def extra_editable() -> list[str]:
    return tk.config[EXTRA_EDITABLE]


def whitelist() -> list[str]:
    return tk.config[WHITELIST]


def blacklist() -> list[str]:
    return tk.config[BLACKLIST]


def charge_timeout() -> int:
    return tk.config[CHARGE_TIMEOUT]


def replace_admin_config_tab() -> bool:
    return tk.config[REPLACE_CONFIG_TAB]


def disable_admin_config_tab() -> bool:
    return tk.config[DISABLE_CONFIG_TAB]


def convert_core_overrides() -> bool:
    return tk.config[CONVERT_CORE_OVERRIDES]


def additional_validators() -> dict[str, str]:
    return tk.config[ADDITIONAL_VALIDATORS]
