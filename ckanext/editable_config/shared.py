from __future__ import annotations

import datetime
import logging
from typing import Any

from typing_extensions import TypedDict

import ckan.plugins.toolkit as tk
from ckan.cli import CKANConfigLoader
from ckan.common import config_declaration as cd
from ckan.config.declaration import Key
from ckan.config.declaration.option import Option as DeclaredOption
from ckan.plugins.core import plugins_update

log = logging.getLogger(__name__)


class OptionDict(TypedDict):
    key: str
    value: str
    updated_at: str
    prev_value: str


def value_as_string(key: str, value: Any) -> str:
    option = cd[Key.from_string(key)]

    return DeclaredOption(value).set_validators(option.get_validators()).str_value()


class _Updater:
    _last_update: datetime.datetime | None

    def __init__(self):
        self._last_update = None

    def __call__(self, removed_keys: list[str] | None = None) -> int:
        from ckanext.editable_config.model import Option

        count = 0

        if Option.is_updated_since(self._last_update):
            for option in Option.updated_since(self._last_update):
                log.debug(
                    "Change %s from %s to %s",
                    option.key,
                    tk.config[option.key],
                    option.value,
                )
                tk.config[option.key] = option.value
                count += 1

            self._last_update = datetime.datetime.utcnow()

        if removed_keys:
            src_conf = CKANConfigLoader(tk.config["__file__"]).get_config()
            for key in removed_keys:
                if key in src_conf:
                    log.debug(
                        "Reset %s from %s to %s",
                        key,
                        tk.config[key],
                        src_conf[key],
                    )

                    tk.config[key] = src_conf[key]
                else:
                    log.debug(
                        "Remove %s with value %s",
                        key,
                        tk.config[key],
                    )
                    tk.config.pop(key)
                count += 1

        if count:
            plugins_update()

        return count


apply_config_overrides = _Updater()
