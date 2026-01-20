"""
Entity definitions for storage module.
"""

from service.entity import Entity, not_empty

from storage.models import Upload

# Entity for Upload
upload_entity = Entity(
    Upload,
    default_sort_column=None,
    validation=dict(
        category=not_empty,
        name=not_empty,
        type=not_empty,
        data=not_empty,
    ),
    # Note: Image processing is handled in views before entity creation
)
