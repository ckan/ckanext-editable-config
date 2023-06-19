from __future__ import annotations

from ckan import types
from ckan.logic.schema import validator_args


@validator_args
def editable_config_list(
    default: types.ValidatorFactory,
    unicode_safe: types.Validator,
) -> types.Schema:
    return {"pattern": [default("*"), unicode_safe]}


@validator_args
def editable_config_update(
    default: types.ValidatorFactory,
    convert_to_json_if_string: types.Validator,
    json_list_or_string: types.Validator,
    list_of_strings: types.Validator,
    dict_only: types.Validator,
    boolean_validator: types.Validator,
) -> types.Schema:
    return {
        "change": [default("{}"), convert_to_json_if_string, dict_only],
        "revert": [default("[]"), json_list_or_string, list_of_strings],
        "reset": [default("[]"), json_list_or_string, list_of_strings],
        "apply": [default(True), boolean_validator],
    }


@validator_args
def editable_config_change(
    default: types.ValidatorFactory,
    convert_to_json_if_string: types.Validator,
    dict_only: types.Validator,
    boolean_validator: types.Validator,
) -> types.Schema:
    return {
        "options": [default("{}"), convert_to_json_if_string, dict_only],
        "apply": [default(True), boolean_validator],
    }


@validator_args
def editable_config_option_save(
    default: types.ValidatorFactory,
    not_empty: types.Validator,
    boolean_validator: types.Validator,
    unicode_safe: types.Validator,
    ignore_empty: types.Validator,
) -> types.Schema:
    return {
        "key": [not_empty, unicode_safe],
        "value": [not_empty, unicode_safe],
        "prev_value": [ignore_empty, unicode_safe],
        "apply": [default(True), boolean_validator],
    }


@validator_args
def editable_config_revert(
    json_list_or_string: types.Validator,
    list_of_strings: types.Validator,
    default: types.ValidatorFactory,
    boolean_validator: types.Validator,
) -> types.Schema:
    return {
        "keys": [default("[]"), json_list_or_string, list_of_strings],
        "apply": [default(True), boolean_validator],
    }


@validator_args
def editable_config_reset(
    json_list_or_string: types.Validator,
    list_of_strings: types.Validator,
    default: types.ValidatorFactory,
    boolean_validator: types.Validator,
) -> types.Schema:
    return {
        "keys": [default("[]"), json_list_or_string, list_of_strings],
        "apply": [default(True), boolean_validator],
    }


@validator_args
def editable_config_apply(
    json_list_or_string: types.Validator,
    list_of_strings: types.Validator,
    default: types.ValidatorFactory,
) -> types.Schema:
    return {
        "removed_keys": [default("[]"), json_list_or_string, list_of_strings],
    }
