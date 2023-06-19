import pytest

import ckan.plugins.toolkit as tk

from ckanext.editable_config.logic import schema


@pytest.mark.parametrize(
    ("schema", "expected"),
    [
        (schema.editable_config_list, {"pattern": "*"}),
        (
            schema.editable_config_update,
            {"change": {}, "revert": [], "reset": [], "apply": True},
        ),
        (schema.editable_config_change, {"options": {}, "apply": True}),
        (schema.editable_config_revert, {"keys": [], "apply": True}),
        (schema.editable_config_reset, {"keys": [], "apply": True}),
        (schema.editable_config_apply, {"removed_keys": []}),
    ],
)
def test_empty_payload(schema, expected):
    data, _ = tk.navl_validate({}, schema())
    assert data == expected
