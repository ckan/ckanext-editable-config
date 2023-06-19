from __future__ import annotations

import datetime
import logging
from typing import Any, Collection

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
    _last_check: datetime.datetime | None

    def __init__(self):
        self._last_check = None

    def __call__(self, removed_keys: Collection[str] | None = None) -> int:
        count = self._apply_changes()
        count += self._remove_keys(removed_keys)

        if count:
            plugins_update()

        return count

    def _apply_changes(self) -> int:
        from ckanext.editable_config.model import Option

        now = datetime.datetime.utcnow()
        count = 0

        if Option.is_updated_since(self._last_check):
            for option in Option.updated_since(self._last_check):
                log.debug(
                    "Change %s from %s to %s",
                    option.key,
                    tk.config[option.key],
                    option.value,
                )
                tk.config[option.key] = option.value
                count += 1

        self._last_check = now
        return count

    def _remove_keys(self, keys: Collection[str] | None) -> int:
        count = 0
        if not keys:
            return count

        src_conf = CKANConfigLoader(tk.config["__file__"]).get_config()
        for key in keys:
            if key in src_conf:
                log.debug(
                    "Reset %s from %s to %s",
                    key,
                    tk.config[key],
                    src_conf[key],
                )

                tk.config[key] = src_conf[key]
            elif key in tk.config:
                log.debug(
                    "Remove %s with value %s",
                    key,
                    tk.config[key],
                )
                tk.config.pop(key)
            else:
                log.warning("Attempt to reset unknown option %s", key)
                continue

            count += 1

        return count


apply_config_overrides = _Updater()
