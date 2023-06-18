from __future__ import annotations

import logging
import os

import sqlalchemy as sa

import ckan.plugins.toolkit as tk
from ckan import model, plugins, types
from ckan.common import CKANConfig
from ckan.common import config_declaration as cd
from ckan.config.declaration import Key
from ckan.config.declaration.option import Flag

from . import config, shared

log = logging.getLogger(__name__)
ENVVAR_DISABLE = "CKANEXT_EDITABLE_CONFIG_DISABLE"


@tk.blanket.config_declarations
@tk.blanket.actions
@tk.blanket.auth_functions
class EditableConfigPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IConfigurable, inherit=True)
    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.IConfigDeclaration, inherit=True)

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
        self._update_editable_flag(config.extra_editable(), True)
        self._update_editable_flag(config.blacklist(), False)

        if whitelist := config.whitelist():
            for key in cd.iter_options():
                if key in whitelist:
                    continue

                cd[key].flags &= ~Flag.editable

    def _update_editable_flag(self, keys: list[str], enable: bool):
        for key in keys:
            if key not in cd:
                log.warning("%s is not declared", key)
                continue
            option = cd[Key.from_string(key)]
            if enable:
                option.set_flag(Flag.editable)
            else:
                option.flags &= ~Flag.editable

    # IConfigurable
    def configure(self, config_: CKANConfig):
        if tk.asbool(os.getenv(ENVVAR_DISABLE)):
            self._editable_config_enabled = False
            log.info(
                "editable_config disabled because of environemnt variable: %s",
                ENVVAR_DISABLE,
            )

        inspector = sa.inspect(model.meta.engine)
        self._editable_config_enabled = inspector.has_table("editable_config_option")
        if not self._editable_config_enabled:
            log.critical(
                "editable_config disabled because of missing migration: %s",
                "ckan db upgrade -p editable_config",
            )
            return

        shared.apply_config_overrides()
