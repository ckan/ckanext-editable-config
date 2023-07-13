from __future__ import annotations

import ckan.plugins.toolkit as tk

def editable_config_disable_admin_config_tab() -> bool:
    return tk.config["ckanext.editable_config.disable_admin_config_tab"]
