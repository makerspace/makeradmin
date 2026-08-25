"""Global settings system with type-safe access.

This module provides a centralized settings management system with:
- Type-safe setting definitions via SettingProperty
- Automatic database persistence via Setting model
- Caching for efficient lookups
- Validation and serialization for various types
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Type, TypeVar, get_args, get_origin

from service.api_definition import BAD_VALUE
from service.db import db_session
from service.error import UnprocessableEntity
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, validates


class Base(DeclarativeBase):
    pass


T = TypeVar("T")


class IntroBookingMethod(Enum):
    Calendly = "calendly"
    MakerspaceEvents = "makerspace_events"


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

    task_delegator_enabled: SettingProperty[bool] = SettingProperty(
        key="task_delegator_enabled",
        default=True,
        description="Enable or disable the Slack task delegator bot",
        category="slack",
        is_public=False,
    )

    thespace_mention_enabled: SettingProperty[bool] = SettingProperty(
        key="thespace_mention_enabled",
        default=True,
        description="Enable or disable the @thespace Slack mention handler",
        category="slack",
        is_public=False,
    )

    thespace_keywords: SettingProperty[List[str]] = SettingProperty(
        key="thespace_keywords",
        default=["@thespace", "someone at the space", "anyone at makerspace now", "anyone at the makerspace right now"],
        description="Keywords that trigger the @thespace mention handler",
        category="slack",
        is_public=False,
    )

    url_facebook_group: SettingProperty[str] = SettingProperty(
        key="url_facebook_group",
        default="https://www.facebook.com/groups/makerspace.se",
        description="Facebook group URL",
        category="external_links",
        is_public=True,
    )

    url_slack_help: SettingProperty[str] = SettingProperty(
        key="url_slack_help",
        default="https://wiki.makerspace.se/Slack",
        description="Slack help/info page URL",
        category="external_links",
        is_public=True,
    )

    url_slack_signup: SettingProperty[str] = SettingProperty(
        key="url_slack_signup",
        default="https://http.cat/images/501.jpg",
        description="Slack workspace signup/invite URL (invite links expire after about 400 invites, so this must be configured and rotated regularly)",
        category="external_links",
        is_public=True,
    )

    url_wiki: SettingProperty[str] = SettingProperty(
        key="url_wiki",
        default="https://wiki.makerspace.se",
        description="Wiki URL",
        category="external_links",
        is_public=True,
    )

    url_get_started_quiz: SettingProperty[str] = SettingProperty(
        key="url_get_started_quiz",
        default="https://medlem.makerspace.se/member/quiz/1",
        description="Get started quiz URL",
        category="external_links",
        is_public=True,
    )

    url_instagram: SettingProperty[str] = SettingProperty(
        key="url_instagram",
        default="https://www.instagram.com/stockholmmakerspace/",
        description="Instagram profile URL",
        category="external_links",
        is_public=True,
    )

    url_calendar: SettingProperty[str] = SettingProperty(
        key="url_calendar",
        default="https://www.makerspace.se/kalendarium",
        description="Events calendar URL",
        category="external_links",
        is_public=True,
    )

    url_calendly_book: SettingProperty[str] = SettingProperty(
        key="url_calendly_book",
        default="https://calendly.com/medlemsintroduktion/medlemsintroduktion",
        description="Calendly booking URL for member introductions",
        category="external_links",
        is_public=True,
    )

    intro_booking_method: SettingProperty[IntroBookingMethod] = SettingProperty(
        key="intro_booking_method",
        default=IntroBookingMethod.Calendly,
        description="Booking system for member introductions: 'calendly' uses the url_calendly_book page, "
        "'makerspace_events' embeds the booker at url_intro_booking_embed",
        category="external_links",
        is_public=True,
    )

    url_intro_booking_embed: SettingProperty[str] = SettingProperty(
        key="url_intro_booking_embed",
        default="https://events.makerspace.se/embed/intro",
        description="Member introduction booking embed URL, used when intro_booking_method is 'makerspace_events'",
        category="external_links",
        is_public=True,
    )

    url_memberbooth: SettingProperty[str] = SettingProperty(
        key="url_memberbooth",
        default="https://wiki.makerspace.se/Memberbooth",
        description="Memberbooth wiki page URL",
        category="external_links",
        is_public=True,
    )

    url_accessy_android: SettingProperty[str] = SettingProperty(
        key="url_accessy_android",
        default="https://play.google.com/store/apps/details?id=com.axessions.app",
        description="Accessy Android app (Google Play) URL",
        category="external_links",
        is_public=True,
    )

    url_accessy_ios: SettingProperty[str] = SettingProperty(
        key="url_accessy_ios",
        default="https://apps.apple.com/se/app/accessy/id1478132190",
        description="Accessy iOS app (App Store) URL",
        category="external_links",
        is_public=True,
    )

    url_accessy_wiki: SettingProperty[str] = SettingProperty(
        key="url_accessy_wiki",
        default="https://wiki.makerspace.se/Accessy",
        description="Accessy wiki page URL",
        category="external_links",
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
    elif isinstance(type_class, type) and issubclass(type_class, Enum):
        return type_class(value_str)

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
    elif isinstance(type_class, type) and issubclass(type_class, Enum):
        return str(value.value)

    # Handle @serde dataclasses
    if hasattr(type_class, "__dataclass_fields__"):
        from serde.json import to_json

        return to_json(value)

    # Fallback: JSON for lists, dicts, etc.
    return json.dumps(value)


_init_settings_cache()
