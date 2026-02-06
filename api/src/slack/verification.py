"""Redis-based verification system for Slack email overrides."""

import json
import logging
from datetime import timedelta
from typing import Optional

from redis_cache import redis_connection

logger = logging.getLogger("slack")

# Redis key prefix for verifications
VERIFICATION_KEY_PREFIX = "slack_email_verification:"

# Verification expiration time (15 minutes)
VERIFICATION_TTL = timedelta(minutes=15)


class PendingVerification:
    """Represents a pending Slack email verification."""

    def __init__(self, member_id: int, email: str, slack_user_id: str):
        self.member_id = member_id
        self.email = email
        self.slack_user_id = slack_user_id

    def to_dict(self) -> dict:
        return {
            "member_id": self.member_id,
            "email": self.email,
            "slack_user_id": self.slack_user_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PendingVerification":
        return cls(
            member_id=data["member_id"],
            email=data["email"],
            slack_user_id=data["slack_user_id"],
        )


def store_verification(member_id: int, email: str, slack_user_id: str) -> None:
    """
    Store a pending Slack email verification in Redis with automatic expiration.

    Args:
        member_id: The member ID requesting the verification
        email: The Slack email to verify
        slack_user_id: The Slack user ID found for this email
    """
    key = f"{VERIFICATION_KEY_PREFIX}{slack_user_id}"
    verification = PendingVerification(member_id, email, slack_user_id)
    value = json.dumps(verification.to_dict())

    redis_connection.setex(key, VERIFICATION_TTL, value)
    logger.info(f"Stored Slack email verification for member {member_id}")


def get_verification(slack_user_id: str) -> Optional[PendingVerification]:
    """
    Retrieve a pending verification from Redis.

    Args:
        slack_user_id: The Slack user ID to look up

    Returns:
        PendingVerification object if found, None if expired or not found
    """
    key = f"{VERIFICATION_KEY_PREFIX}{slack_user_id}"
    value = redis_connection.get(key)

    if not value:
        return None

    data = json.loads(value.decode("utf-8"))
    return PendingVerification.from_dict(data)


def delete_verification(slack_user_id: str) -> None:
    """
    Delete a pending verification from Redis.

    Args:
        slack_user_id: The Slack user ID to clean up
    """
    key = f"{VERIFICATION_KEY_PREFIX}{slack_user_id}"
    redis_connection.delete(key)
    logger.info(f"Deleted Slack email verification for slack user {slack_user_id}")
