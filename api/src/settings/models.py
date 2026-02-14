"""Global settings system with type-safe access.

This module provides a centralized settings management system with:
- Type-safe setting definitions via SettingProperty
- Automatic database persistence via Setting model
- Caching for efficient lookups
- Validation and serialization for various types
"""

import json
from datetime import datetime
from typing import Any, Dict, Generic, List, Type, TypeVar, get_args, get_origin

from service.api_definition import BAD_VALUE
from service.db import db_session
from service.error import UnprocessableEntity
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, validates


class Base(DeclarativeBase):
    pass


T = TypeVar("T")


class SettingProperty(Generic[T]):
    """Type-safe setting property with explicit read/write methods."""

    def __init__(self, key: str, default: T, description: str, category: str = "general", is_public: bool = False):
        self.key = key
        self.default = default
        self.description = description
        self.category = category
        self.is_public = is_public
        self._type_class = None  # Set by _init_settings_cache()

    def read(self) -> T:
        """Read setting value from database with type conversion."""
        setting = db_session.get(Setting, self.key)
        if not setting:
            return self.default

        return _parse_value(setting.value, self._type_class)

    def write(self, value: T) -> None:
        """Write setting value to database with type conversion."""
        setting = db_session.get(Setting, self.key)
        if not setting:
            setting = Setting(key=self.key)
            db_session.add(setting)

        setting.value = _serialize_value(value, self._type_class)
        db_session.commit()


class GlobalSettings:
    """Global settings with type-safe access.

    This class is the single source of truth for all settings.
    No separate registry needed.

    Usage:
        settings = Settings()
        text = settings.banner_text.read()  # Type: str
        settings.banner_text.write("Welcome!")  # Type-safe
    """

    banner_text: SettingProperty[str] = SettingProperty(
        key="banner_text",
        default="",
        description="Text displayed as a banner on the member portal home page",
        category="banner",
        is_public=True,
    )

    banner_enabled: SettingProperty[bool] = SettingProperty(
        key="banner_enabled",
        default=False,
        description="Enable or disable the banner display",
        category="banner",
        is_public=True,
    )


# Cache settings lookup at module initialization
_SETTINGS_CACHE: Dict[str, tuple[SettingProperty, Type]] = {}


def _init_settings_cache() -> None:
    """Build cache and attach types to properties."""
    for name, annotation in GlobalSettings.__annotations__.items():
        if get_origin(annotation) is SettingProperty:
            prop = getattr(GlobalSettings, name)
            type_arg = get_args(annotation)[0]
            prop._type_class = type_arg  # Cache type on property
            _SETTINGS_CACHE[prop.key] = (prop, type_arg)


def get_setting_property(key: str) -> tuple[SettingProperty, Type]:
    """Get setting property and type by key (from cache)."""
    if key not in _SETTINGS_CACHE:
        raise KeyError(f"Setting '{key}' not found")
    return _SETTINGS_CACHE[key]


def all_setting_properties() -> Dict[str, tuple[SettingProperty, Type]]:
    """Get all setting properties (from cache)."""
    return _SETTINGS_CACHE


class Setting(Base):
    """Database table for storing setting values.

    All metadata lives in Settings class. This table only stores string values.
    """

    __tablename__ = "core_settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @validates("key")
    def validate_key(self, key_attr: str, key_value: str) -> str:
        """Ensure key exists in Settings class."""
        if key_value not in _SETTINGS_CACHE:
            raise UnprocessableEntity(
                f"Setting key '{key_value}' not defined in Settings class.", fields=key_attr, what=BAD_VALUE
            )
        return key_value

    def __repr__(self) -> str:
        return f"Setting(key={self.key}, value={self.value})"


# Helper functions for typed value conversion (used by SettingProperty methods)
def _parse_value(value_str: str, type_class: Type) -> Any:
    """Parse string value to typed value."""
    if type_class == bool:
        return value_str.lower() in ("true", "1", "yes")
    elif type_class == int:
        return int(value_str)
    elif type_class == str:
        return value_str

    # Handle generic types (list, dict, list[str], etc.)
    origin = get_origin(type_class)
    if origin in (list, dict, List):
        return json.loads(value_str)

    # Handle @serde dataclasses
    if hasattr(type_class, "__dataclass_fields__"):
        from serde.json import from_json

        return from_json(type_class, value_str)

    # Fallback: try JSON
    try:
        return json.loads(value_str)
    except json.JSONDecodeError:
        return value_str


def _serialize_value(value: Any, type_class: Type) -> str:
    """Serialize typed value to string."""
    if type_class == bool:
        return "true" if value else "false"
    elif type_class == int:
        return str(int(value))
    elif type_class == str:
        return str(value) if value is not None else ""

    # Handle @serde dataclasses
    if hasattr(type_class, "__dataclass_fields__"):
        from serde.json import to_json

        return to_json(value)

    # Fallback: JSON for lists, dicts, etc.
    return json.dumps(value)


_init_settings_cache()
