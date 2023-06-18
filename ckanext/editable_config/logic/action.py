from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict

import ckan.plugins.toolkit as tk
from ckan import types
from ckan.common import CKANConfig
from ckan.common import config_declaration as cd
from ckan.config.declaration import Key
from ckan.config.declaration.option import Flag
from ckan.logic import validate

from ckanext.editable_config import shared
from ckanext.editable_config.model import Option

from . import schema


class UpdateResult(TypedDict):
    change: dict[str, shared.OptionDict]
    revert: dict[str, shared.OptionDict]
    reset: dict[str, shared.OptionDict]


@tk.side_effect_free
@validate(schema.editable_config_list)
def editable_config_list(
    context: types.Context,
    data_dict: dict[str, Any],
) -> dict[str, Any]:
    tk.check_access("editable_config_list", context, data_dict)

    result: dict[str, Any] = {}
    for key in cd.iter_options():
        option = cd[key]
        if not option.has_flag(Flag.editable):
            continue

        skey = str(key)

        result[skey] = {"value": shared.value_as_string(skey, tk.config[skey])}

    return result


@tk.side_effect_free
@validate(schema.editable_config_update)
def editable_config_update(
    context: types.Context,
    data_dict: dict[str, Any],
) -> UpdateResult:
    tk.check_access("editable_config_update", context, data_dict)

    result: UpdateResult = {
        "change": {},
        "revert": {},
        "reset": {},
    }

    result["change"] = tk.get_action("editable_config_change")(
        tk.fresh_context(context),
        {"options": data_dict["change"], "apply": False},
    )
    result["revert"] = tk.get_action("editable_config_revert")(
        tk.fresh_context(context),
        {"keys": data_dict["revert"], "apply": False},
    )
    result["reset"] = tk.get_action("editable_config_reset")(
        tk.fresh_context(context),
        {"keys": data_dict["reset"], "apply": False},
    )

    if data_dict["apply"]:
        shared.apply_config_overrides(removed_keys=list(result["reset"]))

    return result


@tk.side_effect_free
@validate(schema.editable_config_change)
def editable_config_change(
    context: types.Context,
    data_dict: dict[str, Any],
) -> dict[str, shared.OptionDict]:
    tk.check_access("editable_config_change", context, data_dict)
    sess = context["session"]
    options: list[Option] = []

    for k, v in data_dict["options"].items():
        options.append(_make_option(k, v))

    result: dict[str, shared.OptionDict] = {}
    for option in options:
        sess.add(option)
        result[option.key] = option.as_dict(tk.fresh_context(context))

    if not context.get("defer_commit"):
        sess.commit()

    if data_dict["apply"]:
        shared.apply_config_overrides()

    return result


def _make_option(key: str, value: Any):
    if key not in cd or not cd[Key.from_string(key)].has_flag(Flag.editable):
        raise tk.ValidationError({key: ["Not editable"]})

    _, errors = cd.validate(CKANConfig(tk.config, **{key: value}))
    if errors:
        raise tk.ValidationError(errors)

    return Option.set(key, value)


@tk.side_effect_free
@validate(schema.editable_config_create)
def editable_config_create(
    context: types.Context,
    data_dict: dict[str, Any],
) -> shared.OptionDict:
    tk.check_access("editable_config_create", context, data_dict)
    sess = context["session"]

    option = _make_option(data_dict["key"], data_dict["value"])
    if "prev_value" in data_dict:
        option.prev_value = data_dict["prev_value"]

    sess.add(option)

    if not context.get("defer_commit"):
        sess.commit()

    if data_dict["apply"]:
        shared.apply_config_overrides()

    return option.as_dict(tk.fresh_context(context))


@tk.side_effect_free
@validate(schema.editable_config_revert)
def editable_config_revert(
    context: types.Context,
    data_dict: dict[str, Any],
) -> dict[str, shared.OptionDict]:
    tk.check_access("editable_config_revert", context, data_dict)

    sess = context["session"]
    result: dict[str, shared.OptionDict] = {}
    options: list[Option] = []

    for key in data_dict["keys"]:
        if option := Option.get(key):
            _, errors = cd.validate(CKANConfig(tk.config, **{key: option.prev_value}))
            if errors:
                raise tk.ValidationError(errors)

            options.append(option)
        else:
            raise tk.ObjectNotFound(key)

    for option in options:
        option.revert()
        result[option.key] = option.as_dict(tk.fresh_context(context))

    if not context.get("defer_commit"):
        sess.commit()

    if data_dict["apply"]:
        shared.apply_config_overrides()

    return result


@tk.side_effect_free
@validate(schema.editable_config_reset)
def editable_config_reset(
    context: types.Context,
    data_dict: dict[str, Any],
) -> dict[str, shared.OptionDict]:
    tk.check_access("editable_config_reset", context, data_dict)
    sess = context["session"]
    result: dict[str, shared.OptionDict] = {}
    options: list[Option] = []

    for key in data_dict["keys"]:
        if option := Option.get(key):
            options.append(option)
        else:
            raise tk.ObjectNotFound(key)

    for option in options:
        sess.delete(option)
        result[option.key] = option.as_dict(tk.fresh_context(context))

    if not context.get("defer_commit"):
        sess.commit()

    if data_dict["apply"]:
        shared.apply_config_overrides(removed_keys=list(result))

    return result


@tk.side_effect_free
@validate(schema.editable_config_apply)
def editable_config_apply(
    context: types.Context,
    data_dict: dict[str, Any],
) -> dict[str, Any]:
    tk.check_access("editable_config_apply", context, data_dict)
    count = shared.apply_config_overrides(removed_keys=data_dict["removed_keys"])

    return {"count": count}