from __future__ import annotations

import ckan.plugins.toolkit as tk

EXTRA_EDITABLE = "ckanext.editable_config.options.extra_editable"
WHITELIST = "ckanext.editable_config.options.whitelist"
BLACKLIST = "ckanext.editable_config.options.blacklist"
CHARGE_TIMEOUT = "ckanext.editable_config.charge_timeout"
DISABLE_CONFIG_TAB = "ckanext.editable_config.disable_admin_config_tab"
CONVERT_CORE_OVERRIDES = "ckanext.editable_config.convert_core_overrides"


def extra_editable() -> list[str]:
    return tk.config[EXTRA_EDITABLE]


def whitelist() -> list[str]:
    return tk.config[WHITELIST]


def blacklist() -> list[str]:
    return tk.config[BLACKLIST]


def charge_timeout() -> int:
    return tk.config[CHARGE_TIMEOUT]


def disable_admin_config_tab() -> bool:
    return tk.config[DISABLE_CONFIG_TAB]


def convert_core_overrides() -> bool:
    return tk.config[CONVERT_CORE_OVERRIDES]
