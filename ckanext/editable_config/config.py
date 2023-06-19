from __future__ import annotations

import ckan.plugins.toolkit as tk

EXTRA_EDITABLE = "ckanext.editable_config.options.extra_editable"
WHITELIST = "ckanext.editable_config.options.whitelist"
BLACKLIST = "ckanext.editable_config.options.blacklist"


def extra_editable() -> list[str]:
    return tk.config[EXTRA_EDITABLE]


def whitelist() -> list[str]:
    return tk.config[WHITELIST]


def blacklist() -> list[str]:
    return tk.config[BLACKLIST]
