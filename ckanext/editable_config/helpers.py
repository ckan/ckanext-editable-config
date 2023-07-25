from __future__ import annotations

from . import config


def editable_config_disable_admin_config_tab() -> bool:
    return config.disable_admin_config_tab()
