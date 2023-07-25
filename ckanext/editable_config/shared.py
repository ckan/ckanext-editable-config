from __future__ import annotations

import datetime
import logging
from typing import Any, Collection

from typing_extensions import TypedDict

import ckan.plugins.toolkit as tk
from ckan.cli import CKANConfigLoader
from ckan.common import config_declaration as cd
from ckan.config.declaration import Key
from ckan.plugins.core import plugins_update

from . import config

log = logging.getLogger(__name__)


class OptionDict(TypedDict):
    key: str
    value: str
    updated_at: str
    prev_value: str


def value_as_string(key: str, value: Any) -> str:
    """Convert the value into string using declared option rules."""
    # TODO: Switch to `option.str_value(value)` once PR with this form is
    # accepted and released.
    option = cd[Key.from_string(key)]
    cls = type(option)

    return cls(value).set_validators(option.get_validators()).str_value()


class _Updater:
    # use the date of last update instead of mutex. In this way we can perform
    # multiple simultaneous updates of the global config object, but it's ok,
    # since config update is idempotent. More important, most of the time we
    # won't spend extra ticks waiting for mutex acquire/release. Because config
    # updates are relatively infrequent, it's better to do double-overrides
    # once in a while instead of constantly waiting in mutex queue.

    # TODO: write bencharks for mutex vs. last updated
    # TODO: prove that race-condition is safe here
    _last_check: datetime.datetime | None

    @property
    def last_check(self):
        return self._last_check

    def __init__(self):
        self._last_check = None

    def __call__(self, removed_keys: Collection[str] | None = None) -> int:
        """Override changed config options and remove options that do not
        require customization.

        Reckon total number of modifications and reload plugins if any change
        detected.
        """
        count = self._apply_changes()
        count += self._remove_keys(removed_keys)

        if count:
            plugins_update()

        return count

    def _apply_changes(self) -> int:
        """Override config options that were updated since last check."""
        from ckanext.editable_config.model import Option

        now = datetime.datetime.utcnow()
        count = 0

        charge_timeout = datetime.timedelta(seconds=config.charge_timeout())
        if self._last_check and now - self._last_check < charge_timeout:
            return count

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
        """Restore original value(using config file) for specified options."""
        count = 0
        if not keys:
            return count

        src_conf = CKANConfigLoader(tk.config["__file__"]).get_config()
        for key in keys:
            if key in src_conf:
                # switch to the literal value from the config file.
                log.debug(
                    "Reset %s from %s to %s",
                    key,
                    tk.config[key],
                    src_conf[key],
                )

                tk.config[key] = src_conf[key]
            elif key in tk.config:
                # switch to the declared default value by removing option
                log.debug(
                    "Remove %s with value %s",
                    key,
                    tk.config[key],
                )
                tk.config.pop(key)
            else:
                # TODO: analize if it even possible to get here
                log.warning("Attempt to reset unknown option %s", key)
                continue

            count += 1

        return count


apply_config_overrides = _Updater()
