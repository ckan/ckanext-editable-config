from __future__ import annotations

import logging
import os
from typing import Iterable

import sqlalchemy as sa

import ckan.plugins.toolkit as tk
from ckan import model, plugins, types
from ckan.common import CKANConfig
from ckan.common import config_declaration as cd
from ckan.config.declaration.option import Flag
from ckan.logic import clear_actions_cache

from . import config, shared

log = logging.getLogger(__name__)
ENVVAR_DISABLE = "CKANEXT_EDITABLE_CONFIG_DISABLE"


@tk.blanket.config_declarations
@tk.blanket.actions
@tk.blanket.helpers
@tk.blanket.blueprints
@tk.blanket.auth_functions
class EditableConfigPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IConfigurable, inherit=True)
    plugins.implements(plugins.IMiddleware, inherit=True)

    _editable_config_enabled: bool = True

    # IMiddleware
    def make_middleware(self, app: types.CKANApp, config: CKANConfig) -> types.CKANApp:
        if self._editable_config_enabled:
            app.before_request(self._apply_overrides)

        return app

    def _apply_overrides(self):
        shared.apply_config_overrides()

    # IConfigurer
    def update_config(self, config_: CKANConfig):
        tk.add_template_directory(config_, "templates")
        tk.add_resource("assets", "editable_config")

        shared.switch_editable_flag(config.extra_editable(), True)
        shared.switch_editable_flag(config.blacklist(), False)

        if whitelist := config.whitelist():
            for key in cd.iter_options():
                if key in whitelist:
                    continue

                cd[key].flags &= ~Flag.editable

        shared.add_validators(config.additional_validators())

    # IConfigurable
    def configure(self, config_: CKANConfig):
        if tk.asbool(os.getenv(ENVVAR_DISABLE)):
            self._editable_config_enabled = False
            log.info(
                "editable_config disabled because of environemnt variable: %s",
                ENVVAR_DISABLE,
            )
            return

        engine = model.meta.engine
        if not engine:
            return

        inspector = sa.inspect(engine)
        self._editable_config_enabled = inspector.has_table("editable_config_option")
        if not self._editable_config_enabled:
            log.critical(
                "editable_config disabled because of missing migration: %s",
                "ckan db upgrade -p editable_config",
            )
            return

        # check if there are any conflicting config overrides from core AdminUI
        stmt = sa.select(model.SystemInfo.key)
        legacy_modified: Iterable[str] = model.Session.scalars(stmt)
        editable = {
            str(op) for op in cd.iter_options() if cd[op].has_flag(Flag.editable)
        }

        if problems := (set(legacy_modified) & editable):
            if config.convert_core_overrides():
                clear_actions_cache()
                shared.convert_core_overrides(problems)

            else:
                log.warning(
                    "Modification via core AdminUI will cause undefined behavior: %s",
                    problems,
                )

        shared.apply_config_overrides()
