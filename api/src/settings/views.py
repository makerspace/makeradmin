"""API views for settings management."""

import json
from typing import get_origin

from service.api_definition import BAD_VALUE, GET, PUBLIC, PUT, WEBSHOP_ADMIN, Arg
from service.db import db_session
from service.error import NotFound, UnprocessableEntity

from settings import service
from settings.models import Setting, _parse_value, _serialize_value, all_setting_properties, get_setting_property


@service.route("/public", permission=PUBLIC, method=GET)
def list_public_settings():
    """List all public settings (no authentication required).

    Returns only settings where is_public=True.
    """
    db_settings = {s.key: s for s in db_session.query(Setting).all()}

    result = []
    for key, (prop, type_class) in sorted(all_setting_properties().items()):
        if not prop.is_public:
            continue

        db_setting = db_settings.get(key)
        default_str = _serialize_value(prop.default, type_class)

        result.append(
            {
                "key": key,
                "value": db_setting.value if db_setting else default_str,
            }
        )

    return result


@service.route("", permission=WEBSHOP_ADMIN, method=GET)
def list_settings():
    """List all settings with their current values and metadata.

    Returns settings ordered by category, then key.
    Admin only.
    """
    # Get all settings from DB
    db_settings = {s.key: s for s in db_session.query(Setting).all()}

    # Build response with metadata from Settings class
    result = []
    for key, (prop, type_class) in sorted(all_setting_properties().items(), key=lambda x: (x[1][0].category, x[0])):
        db_setting = db_settings.get(key)

        # Use the same serialization logic as SettingProperty.write()
        default_str = _serialize_value(prop.default, type_class)

        # Determine value type
        origin = get_origin(type_class)
        if origin is list:
            value_type_name = "list"
        elif hasattr(type_class, "__name__"):
            value_type_name = type_class.__name__
        else:
            value_type_name = str(type_class)

        result.append(
            {
                "key": key,
                "value": db_setting.value if db_setting else default_str,
                "value_type": value_type_name,
                "description": prop.description,
                "category": prop.category,
                "is_public": prop.is_public,
                "created_at": db_setting.created_at if db_setting else None,
                "updated_at": db_setting.updated_at if db_setting else None,
            }
        )

    return result


@service.route("/<string:key>", permission=WEBSHOP_ADMIN, method=GET)
def get_setting_detail(key):
    """Get a specific setting with its metadata.

    Admin only.
    """
    try:
        prop, type_class = get_setting_property(key)
    except KeyError:
        raise NotFound(f"Setting '{key}' not found in registry.")

    db_setting = db_session.get(Setting, key)

    # Use the same serialization logic as SettingProperty.write()
    default_str = _serialize_value(prop.default, type_class)

    # Determine value type
    origin = get_origin(type_class)
    if origin is list:
        value_type_name = "list"
    elif hasattr(type_class, "__name__"):
        value_type_name = type_class.__name__
    else:
        value_type_name = str(type_class)

    return {
        "key": key,
        "value": db_setting.value if db_setting else default_str,
        "value_type": value_type_name,
        "description": prop.description,
        "category": prop.category,
        "is_public": prop.is_public,
        "created_at": db_setting.created_at if db_setting else None,
        "updated_at": db_setting.updated_at if db_setting else None,
    }


@service.route("/<string:key>", permission=WEBSHOP_ADMIN, method=PUT)
def update_setting(key, value=Arg(str)):
    """Update a setting value.

    The key must exist in Settings class.
    The value is provided as a string and will be validated according to type.
    Admin only.
    """
    try:
        prop, type_class = get_setting_property(key)
    except KeyError:
        raise NotFound(f"Setting '{key}' not found in registry.")

    # Validate value according to type before parsing
    try:
        if type_class == bool:
            # Strict boolean validation - only accept 'true' or 'false'
            if value.lower() not in ("true", "false"):
                raise ValueError("Boolean value must be 'true' or 'false'")
        # Validate by attempting to parse - reuses the same logic as SettingProperty.read()
        _parse_value(value, type_class)
    except (ValueError, json.JSONDecodeError, Exception) as e:
        type_name = type_class.__name__ if hasattr(type_class, "__name__") else str(type_class)
        raise UnprocessableEntity(f"Invalid value for type {type_name}: {str(e)}", fields="value", what=BAD_VALUE)

    # Update or create setting
    setting = db_session.get(Setting, key)
    if not setting:
        setting = Setting(key=key)
        db_session.add(setting)

    setting.value = value
    db_session.commit()

    type_name = type_class.__name__ if hasattr(type_class, "__name__") else str(type_class)
    return {
        "key": key,
        "value": value,
        "value_type": type_name,
    }
