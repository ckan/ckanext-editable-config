from __future__ import annotations

from typing import Any

from flask import Blueprint
from flask.views import MethodView

import ckan.plugins.toolkit as tk
from ckan.logic import parse_params

bp = Blueprint("editable_config", __name__)


class ConfigView(MethodView):
    def _check_access(self):
        try:
            tk.check_access("sysadmin", {})
        except tk.NotAuthorized:
            tk.abort(403, tk._("Need to be system administrator to administer"))

    def _render(self, data: dict[str, Any], error: tk.ValidationError | None = None):
        options = tk.get_action("editable_config_list")({}, {})

        extra_vars: dict[str, Any] = {
            "data": data,
            "options": options,
            "errors": error.error_dict if error else None,
            "error_summary": error.error_summary if error else None,
        }

        return tk.render("editable_config/config.html", extra_vars)

    def get(self):
        self._check_access()
        return self._render({})

    def post(self):
        self._check_access()
        data = parse_params(tk.request.form)
        change = {}
        reset = []

        for key in data:
            if key.startswith("reset:"):
                clean_key = key[6:]
                change.pop(clean_key, None)
                reset.append(clean_key)

            else:
                if key in reset:
                    continue
                change[key] = data[key]

        try:
            tk.get_action("editable_config_update")(
                {},
                {"change": change, "reset": reset},
            )
        except tk.ValidationError as e:
            return self._render(data, e)

        return tk.redirect_to("editable_config.config")


bp.add_url_rule("/ckan-admin/editable-config", view_func=ConfigView.as_view("config"))
