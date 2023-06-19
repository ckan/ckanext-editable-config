from __future__ import annotations

from datetime import datetime
from typing import Any, cast

import sqlalchemy as sa
from typing_extensions import Self

import ckan.plugins.toolkit as tk
from ckan import model, types
from ckan.lib.dictization import table_dictize

from ckanext.editable_config import shared


class Option(tk.BaseModel):
    __tablename__ = "editable_config_option"

    key = sa.Column(sa.Text, primary_key=True)
    value = sa.Column(sa.Text, nullable=False)
    updated_at = sa.Column(sa.DateTime, nullable=False)
    prev_value = sa.Column(sa.Text, nullable=False)

    @classmethod
    def get(cls, key: str) -> Self | None:
        return cast(
            Self,
            model.Session.get(cls, key),
        )

    @classmethod
    def set(cls, key: str, value: Any) -> Self:
        option: Self
        safe_value = shared.value_as_string(key, value)

        if option := cls.get(key):
            option.value = safe_value
        else:
            option = cls(key=key, value=safe_value)

        option.prev_value = shared.value_as_string(key, tk.config[key])
        option.touch()

        return option

    def touch(self):
        self.updated_at = datetime.utcnow()

    def revert(self):
        self.value, self.prev_value = self.prev_value, self.value
        self.touch()

    def as_dict(self, context: types.Context) -> shared.OptionDict:
        return cast(shared.OptionDict, table_dictize(self, context))

    @classmethod
    def is_updated_since(cls, last_update: datetime | None) -> bool:
        return model.Session.query(cls.updated_since(last_update).exists()).scalar()

    @classmethod
    def updated_since(cls, last_update: datetime | None) -> types.Query[Self]:
        q = model.Session.query(cls)
        if last_update:
            q = q.filter(cls.updated_at > last_update)

        return q
