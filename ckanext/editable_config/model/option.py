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
        """Search for option."""
        return cast(
            Self,
            model.Session.get(cls, key),
        )

    @classmethod
    def set(cls, key: str, value: Any) -> Self:
        """Create/update an option."""
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
        """Update modification date of the option."""
        self.updated_at = datetime.utcnow()

    def revert(self):
        """Swap current and previous values of the option."""
        self.value, self.prev_value = self.prev_value, self.value
        self.touch()

    def as_dict(self, context: types.Context) -> shared.OptionDict:
        """Convert option object into form appropriate for API response."""
        return cast(shared.OptionDict, table_dictize(self, context))

    @classmethod
    def is_updated_since(cls, last_update: datetime | None) -> bool:
        """Check if there are any registered config overrides.

        If optional `last_update` is provided, check for updates that were made
        after this moment.
        """
        q: Any = cls.updated_since(last_update).exists()
        return model.Session.query(q).scalar()

    @classmethod
    def updated_since(cls, last_update: datetime | None) -> types.Query[Self]:
        """All overriden config options.

        If optional `last_update` is provided, return only options that were
        updated after this moment.

        """
        q = model.Session.query(cls)
        if last_update:
            q = q.filter(cls.updated_at > last_update)

        return q
