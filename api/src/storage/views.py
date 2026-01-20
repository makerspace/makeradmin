"""
Generic storage API endpoints.
Handles image upload, serving, and deletion.
"""

import base64
from logging import getLogger
from typing import Any, Dict

from flask import Response, g, make_response
from service.api_definition import DELETE, GET, POST, PUBLIC, USER
from service.db import db_session
from service.error import NotFound, UnprocessableEntity
from sqlalchemy import select

from storage import service
from storage.entities import upload_entity
from storage.image_service import ImageProcessingError, ImageService
from storage.models import Upload

logger = getLogger("storage")


@service.route("/image", method=POST, permission=USER)
def upload_image() -> Dict[str, Any]:
    """
    Upload and process an image.

    Generic storage endpoint with no domain knowledge.
    Categories are not validated - any string accepted.

    Request body:
        category: Category string (e.g., 'quiz', 'product')
        name: Original filename
        type: Original MIME type
        data: Base64-encoded image data

    Returns:
        {id, category, name, type, width, height, url}
    """
    from flask import request

    # Get data from request
    data_json = request.json
    category = data_json.get("category")
    name = data_json.get("name")
    type_val = data_json.get("type")
    data = data_json.get("data")

    try:
        # Decode base64
        image_data = base64.b64decode(data)
    except Exception as e:
        raise UnprocessableEntity(f"Invalid base64 data: {str(e)}", fields="data")

    try:
        # Process image
        image_service = ImageService()
        processed_data, metadata = image_service.process_image(image_data)

        # Create upload record
        upload = Upload(
            category=category,
            name=name,
            type=metadata["type"],  # Always 'image/webp' after processing
            data=processed_data,
            width=metadata["width"],
            height=metadata["height"],
        )

        db_session.add(upload)
        db_session.flush()
        db_session.commit()

        logger.info(f"Image uploaded: id={upload.id}, category={category}, name={name}, size={metadata['size']} bytes")

        return {
            "id": upload.id,
            "category": upload.category,
            "name": upload.name,
            "type": upload.type,
            "width": upload.width,
            "height": upload.height,
            "url": f"/storage/image/{upload.id}",
        }

    except ImageProcessingError as e:
        raise UnprocessableEntity(str(e), fields="data")


@service.route("/image/<int:upload_id>", method=GET, permission=PUBLIC)
def get_image(upload_id: int) -> Response:
    """
    Serve an image by ID.

    Returns:
        Image binary (WEBP) with long-term caching headers (immutable)
    """
    # Query upload
    stmt = select(Upload).where(
        Upload.id == upload_id,
        Upload.deleted_at == None,
    )
    upload = db_session.execute(stmt).scalar_one_or_none()

    if upload is None:
        raise NotFound(f"Image {upload_id} not found")

    # Create response with image data
    response = make_response(upload.data)
    response.headers["Content-Type"] = upload.type
    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"

    # Optional: Add Content-Disposition for downloads
    # response.headers['Content-Disposition'] = f'inline; filename="{upload.name}"'

    return response


@service.route("/image/<int:upload_id>", method=DELETE, permission=USER)
def delete_image(upload_id: int) -> Dict[str, str]:
    """
    Soft delete an image.

    Does not check if image is used elsewhere.
    """
    # Query upload
    stmt = select(Upload).where(
        Upload.id == upload_id,
        Upload.deleted_at == None,
    )
    upload = db_session.execute(stmt).scalar_one_or_none()

    if upload is None:
        raise NotFound(f"Image {upload_id} not found")

    # Soft delete
    from datetime import datetime

    upload.deleted_at = datetime.now()

    logger.info(f"Image deleted: id={upload.id}, category={upload.category}, name={upload.name}")

    return {"message": "Image deleted"}
