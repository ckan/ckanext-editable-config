from __future__ import annotations

from typing import Any

from ckan import authz, types


def editable_config_access(
    context: types.Context,
    data_dict: dict[str, Any],
) -> types.AuthResult:
    return authz.is_authorized("sysadmin", context, data_dict)


def editable_config_last_check(
    context: types.Context,
    data_dict: dict[str, Any],
) -> types.AuthResult:
    return authz.is_authorized("editable_config_access", context, data_dict)


def editable_config_list(
    context: types.Context,
    data_dict: dict[str, Any],
) -> types.AuthResult:
    return authz.is_authorized("editable_config_access", context, data_dict)


def editable_config_option_save(
    context: types.Context,
    data_dict: dict[str, Any],
) -> types.AuthResult:
    return authz.is_authorized("editable_config_access", context, data_dict)


def editable_config_update(
    context: types.Context,
    data_dict: dict[str, Any],
) -> types.AuthResult:
    return authz.is_authorized("editable_config_access", context, data_dict)


def editable_config_change(
    context: types.Context,
    data_dict: dict[str, Any],
) -> types.AuthResult:
    return authz.is_authorized("editable_config_access", context, data_dict)


def editable_config_revert(
    context: types.Context,
    data_dict: dict[str, Any],
) -> types.AuthResult:
    return authz.is_authorized("editable_config_access", context, data_dict)


def editable_config_reset(
    context: types.Context,
    data_dict: dict[str, Any],
) -> types.AuthResult:
    return authz.is_authorized("editable_config_access", context, data_dict)


def editable_config_apply(
    context: types.Context,
    data_dict: dict[str, Any],
) -> types.AuthResult:
    return authz.is_authorized("editable_config_access", context, data_dict)
