from __future__ import annotations

import datetime
import logging
from typing import Any, Iterable
import sqlalchemy as sa
from typing_extensions import TypedDict

import ckan.plugins.toolkit as tk
from ckan import model
from ckan.cli import CKANConfigLoader
from ckan.common import config_declaration as cd
from ckan.config.declaration import Key
from ckan.config.declaration.option import Flag
from ckan.config.declaration.option import Option as DeclaredOption
from ckan.plugins.core import plugins_update

from . import config

log = logging.getLogger(__name__)


class OptionDict(TypedDict):
    key: str
    value: str
    updated_at: str
    prev_value: str


def shorten_for_log(value: Any, width: int = 80, placeholder: str = "...") -> str:
    """Prepare value for logging.

    Trasforms value into string and truncates it to specified length, appending
    placeholder if result was reduced in size.
    """
    result = str(value)
    if len(result) > width + len(placeholder):
        result = result[:width] + placeholder
    return result


def get_declaration(key: str) -> DeclaredOption[Any] | None:
    """Return existing declaration or None."""
    if key in cd:
        return cd[Key.from_string(key)]

    log.warning("%s is not declared", key)
    return None


def add_validators(validators: dict[str, str]):
    """Append validators to the declared options.

    Existing validators are not overriden, they extended with the list of
    additional validators:

        >>> option = cd.declare("a").set_validators("not_empty")
        >>> add_validators({"a": "boolean_validator"})
        >>> assert option.get_validators() == "not_empty boolean_validator"

    """
    for key, names in validators.items():
        if option := get_declaration(key):
            option.append_validators(names)


def switch_editable_flag(keys: list[str], enable: bool):
    """Change the state of editable-flag for options."""
    for key in keys:
        if not (option := get_declaration(key)):
            continue

        if enable:
            option.set_flag(Flag.editable)
        else:
            option.flags &= ~Flag.editable


def convert_core_overrides(names: Iterable[str]):
    """Convert SystemInfo records into editable options."""
    try:
        change = tk.get_action("editable_config_change")
    except KeyError:
        log.debug("Do not convert core overrides because plugin is not loaded yet")
        return

    inspector = sa.inspect(model.meta.engine)
    if inspector.has_table("system_info_revision"):
        model.Session.execute(sa.delete(sa.table("system_info_revision")))

    q = model.Session.query(model.SystemInfo).filter(
        model.SystemInfo.key.in_(names),
    )
    options = {op.key: op.value for op in q}

    log.debug("Convert core overrides into editable config: %s", list(options))
    change(
        {"ignore_auth": True},
        {
            "apply": False,
            "options": options,
        },
    )
    q.delete()
    model.Session.commit()


def is_editable(key: str) -> bool:
    """Check if option is editable."""
    if option := get_declaration(key):
        return option.has_flag(Flag.editable)

    return False


def value_as_string(key: str, value: Any) -> str:
    """Convert the value into string using declared option rules."""
    # TODO: Switch to `option.str_value(value)` once PR with this form is
    # accepted and released.
    if option := get_declaration(key):
        cls = type(option)
        return cls(value).set_validators(option.get_validators()).str_value()

    return str(value)


class _Updater:
    """Callable that detects and applies config changes."""

    # use the date of last update instead of mutex. In this way we can perform
    # multiple simultaneous updates of the global config object, but it's ok,
    # since config update is idempotent. More important, most of the time we
    # won't spend extra ticks waiting for mutex acquire/release. Because config
    # updates are relatively infrequent, it's better to do double-overrides
    # once in a while instead of constantly waiting in mutex queue.

    # TODO: write bencharks for mutex vs. last updated
    # TODO: prove that race-condition is safe here
    _last_check: datetime.datetime | None
    _active_overrides: set[str]

    @property
    def last_check(self):
        return self._last_check

    def __init__(self):
        self._last_check = None
        self._active_overrides = set()

    def __call__(self) -> int:
        """Override changed config options and remove options that do not
        require customization.

        Reckon total number of modifications and reload plugins if any change
        detected.
        """
        now = datetime.datetime.utcnow()

        charge_timeout = datetime.timedelta(seconds=config.charge_timeout())
        if self._last_check and now - self._last_check < charge_timeout:
            return 0

        count = self._apply_changes()
        count += self._remove_keys()

        self._last_check = now
        if count:
            plugins_update()

        return count

    def _apply_changes(self) -> int:
        """Override config options that were updated since last check."""
        from ckanext.editable_config.model import Option

        count = 0

        if Option.is_updated_since(self._last_check):
            for option in Option.updated_since(self._last_check):
                if not is_editable(option.key):
                    log.debug(
                        "Option %s was overriden but isn't editable. Skip",
                        option.key,
                    )
                    continue

                log.debug(
                    "Change %s from %s to %s",
                    option.key,
                    shorten_for_log(tk.config[option.key]),
                    shorten_for_log(option.value),
                )
                tk.config[option.key] = option.value
                count += 1

        return count

    def _remove_keys(self) -> int:
        """Restore original value(using config file) for specified options."""
        count = 0

        src_conf = CKANConfigLoader(tk.config["__file__"]).get_config()

        try:
            editable = tk.get_action("editable_config_list")({"ignore_auth": True}, {})
        except KeyError:
            log.debug("Do not check removed overrides because plugin is not loaded yet")
            return 0

        current_overrides = {k for k, v in editable.items() if v["option"]}

        for key in self._active_overrides - current_overrides:
            if key in src_conf:
                # switch to the literal value from the config file.
                log.debug(
                    "Reset %s from %s to %s",
                    key,
                    shorten_for_log(tk.config[key]),
                    shorten_for_log(src_conf[key]),
                )

                tk.config[key] = src_conf[key]
            elif key in tk.config:
                # switch to the declared default value by removing option
                log.debug(
                    "Remove %s with value %s",
                    key,
                    shorten_for_log(tk.config[key]),
                )
                tk.config.pop(key)
            else:
                # TODO: analize if it even possible to get here
                log.warning("Attempt to reset unknown option %s", key)
                continue

            count += 1

        self._active_overrides = current_overrides
        return count


apply_config_overrides = _Updater()
