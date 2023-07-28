from __future__ import annotations

from typing import Any

from ckan.common import config_declaration as cd

from . import config


def editable_config_disable_admin_config_tab() -> bool:
    return config.disable_admin_config_tab()


def editable_config_replace_admin_config_tab() -> bool:
    return config.replace_admin_config_tab()


def editable_config_option_description(name: Any) -> str | None:
    text = cd[name].description
    if text:
        text = text.replace(".. note::", '<i class="fa fa-info-circle"></i>').replace(
            ".. warning::",
            '<i class="fa fa-warning"></i>',
        )

    return text
