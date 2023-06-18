from __future__ import annotations

import ckan.plugins.toolkit as tk


def extra_editable() -> list[str]:
    return tk.config["ckanext.editable_config.options.extra_editable"]


def whitelist() -> list[str]:
    return tk.config["ckanext.editable_config.options.whitelist"]


def blacklist() -> list[str]:
    return tk.config["ckanext.editable_config.options.blacklist"]
