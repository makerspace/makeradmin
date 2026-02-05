import logging
import re
import time
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional

import requests
from membership.models import Member, SlackEmailOverride
from multiaccessy.models import PhysicalAccessEntry
from PIL import Image
from redis_cache import redis_connection
from service.config import config
from service.db import db_session
from service.error import BadRequest, UnprocessableEntity
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from sqlalchemy import distinct, select
from trello import trello

logger = logging.getLogger("slack")

IMAGE_CACHE_VERSION = 5
SLACK_UPLOADED_FILE_TTL = timedelta(days=60)


def get_slack_email_for_member(member: Member) -> str:
    """Get the email to use for Slack lookups, checking override table first."""
    override = db_session.execute(
        select(SlackEmailOverride).where(SlackEmailOverride.member_id == member.member_id)
    ).scalar_one_or_none()

    if override:
        return override.slack_email
    return member.email


def member_from_slack_user_id(slack_client: WebClient, slack_user_id: str) -> Member | None:
    """Get Member object from Slack user ID."""
    try:
        user_info = slack_client.users_info(user=slack_user_id)
        email = user_info["user"]["profile"]["email"]
    except SlackApiError as e:
        logger.error(f"Failed to get Slack user info: {e.response['error']}")
        raise BadRequest("Failed to get user info from Slack")

    return db_session.execute(select(Member).where(Member.email == email)).scalar_one_or_none()


def lookup_slack_user_by_email(slack_client: WebClient, email: str) -> Optional[str]:
    # Look up Slack user by email
    cache_key = f"slack_user_id:{email}"
    cached_id = redis_connection.get(cache_key)
    if cached_id:
        return cached_id.decode("utf-8")

    try:
        response = slack_client.users_lookupByEmail(email=email)
        id: str = response["user"]["id"]
        redis_connection.setex(cache_key, timedelta(hours=24), id)
        return id
    except SlackApiError as e:
        logger.error(f"Failed to look up Slack user by email {email}: {e.response['error']}")
        return None


def lookup_slack_users(slack_client: WebClient, member: list[Member]) -> list[str]:
    slack_user_ids: list[str] = []
    for m in member:
        email = get_slack_email_for_member(m)
        slack_user_id = lookup_slack_user_by_email(slack_client, email)
        if slack_user_id:
            slack_user_ids.append(slack_user_id)
    return slack_user_ids


def get_slack_client() -> Optional[WebClient]:
    token = config.get("SLACK_BOT_TOKEN")
    if not token:
        return None
    return WebClient(token=token)


def upload_image_to_slack(slack_client: WebClient, trello_attachment: trello.TrelloAttachment) -> Optional[str]:
    """
    Download an image from Trello and upload it to Slack. Cache the Slack URL in Redis.
    """
    logger.info(f"Uploading Trello image {trello_attachment.url} to Slack...")
    cache_key = f"slack_image_cache:{IMAGE_CACHE_VERSION}:{trello_attachment.url}"
    cached_slack_url = redis_connection.get(cache_key)

    if cached_slack_url:
        # Refresh the expiration time for the cached Slack URL
        redis_connection.expire(cache_key, SLACK_UPLOADED_FILE_TTL)
        return cached_slack_url.decode("utf-8")

    # Download the image from Trello
    try:
        data = trello.download_attachment(trello_attachment)
    except requests.RequestException as e:
        logger.error(f"Failed to download Trello attachment {trello_attachment.url}: {e}")
        return None

    logger.info(f"\tDownloaded {len(data)} bytes from Trello.")

    # Resize the image to at most 1000px wide or tall
    try:
        image = Image.open(BytesIO(data))
        original_size = image.size
        image.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
        resized_buffer = BytesIO()
        image.save(resized_buffer, format="PNG" if image.has_transparency_data else image.format or "JPEG")
        data = resized_buffer.getvalue()
        logger.info(f"Resized image from {original_size} to {image.size}")
    except Exception as e:
        logger.error(f"Failed to resize image: {e}")
        return None

    # Upload the image to Slack
    try:
        slack_response = slack_client.files_upload_v2(
            file=data,
            filename=trello_attachment.name,
            title=trello_attachment.name,
        )
        slack_url: str | None = slack_response["file"]["permalink"]
        slack_image_id: str | None = slack_response["file"]["id"]
        if not slack_url or not slack_image_id:
            logger.error(f"Failed to upload image to Slack: {slack_response}")
            return None

        # Poll the file info until the mimetype is set. The upload is asynchronous and will fail if we try to use the file too quickly.
        # See https://github.com/slackapi/java-slack-sdk/issues/1349
        for _ in range(10):  # Retry up to 10 times
            try:
                file_info = slack_client.files_info(file=slack_image_id)
                mime_type = file_info["file"].get("mimetype")
                if mime_type:
                    break
            except SlackApiError as e:
                logger.error(f"Failed to fetch file info for Slack file {slack_image_id}: {e.response['error']}")
                return None
            time.sleep(2)  # Wait for 2 seconds before retrying
        else:
            logger.error(f"Timed out waiting for mimetype to be set for Slack file {slack_image_id}")
            return None

        # Cache the Slack URL in Redis
        # res = SlackFile(id=slack_image_id, url=slack_url)
        redis_connection.setex(cache_key, SLACK_UPLOADED_FILE_TTL, slack_url)

        logger.info(f"\tUploaded image to Slack: {slack_url} (id={slack_image_id})")
        return slack_url
    except SlackApiError as e:
        logger.error(f"Failed to upload image to Slack: {e.response['error']}")
        return None


def convert_trello_markdown_to_slack_markdown(text: str) -> str:
    """Ah, yes. Markdown. The one true universal format that everyone agrees on..."""
    # Convert markdown links to Slack format
    # [link text](url "optional title") -> <url|link text>
    text = re.sub(r'\[(.*?)\]\((\S+)(?:\s+".*?")?\)', r"<\2|\1>", text)

    # Convert Trello bold (**bold**) to Slack bold (*bold*)
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)

    return text


def format_member_mention_list(
    slack_members: list[str],
) -> str:
    """
    Format a list of members as Slack user mentions.

    Args:
        slack_client: The Slack client to use for looking up users
        members: List of Member objects
        max_members: Maximum number of members to mention

    Returns:
        A formatted string like "<@user1>, <@user2> or <@user3>", or an empty string if no members found
    """
    if not slack_members:
        return ""

    if len(slack_members) == 1:
        return f"<@{slack_members[0]}>"
    else:
        result = ", ".join(f"<@{m}>" for m in slack_members[:-1])
        result += f" or <@{slack_members[-1]}>"
        return result


def get_members_currently_at_space(duration_at_space_heuristic: timedelta) -> list[Member]:
    """
    Get all members who are currently at the space based on recent door entries.

    Args:
        duration_at_space_heuristic: How long after a door entry a member is considered "at the space"

    Returns:
        List of Member objects currently at the space
    """
    cutoff_time = datetime.now() - duration_at_space_heuristic

    # Get all members who have opened a door recently
    member_ids = (
        db_session.execute(
            select(distinct(PhysicalAccessEntry.member_id)).where(
                PhysicalAccessEntry.member_id.isnot(None),
                PhysicalAccessEntry.created_at >= cutoff_time,
            )
        )
        .scalars()
        .all()
    )

    # Fetch the actual Member objects
    members = []
    for member_id in member_ids:
        member = db_session.get(Member, member_id)
        if member:
            members.append(member)

    return members


def join_all_public_channels(slack_client: WebClient) -> None:
    """
    Have the bot join all public channels in the workspace.
    This allows the bot to respond to @theSpace mentions in all channels.

    Note: This only works for public channels. Private channels still require manual invitation.
    """
    try:
        # Get list of all public channels
        cursor = None
        joined_count = 0
        skipped_count = 0

        while True:
            response = slack_client.conversations_list(
                types="public_channel",
                exclude_archived=True,
                limit=200,
                cursor=cursor,
            )

            channels = response.get("channels", [])

            for channel in channels:
                channel_id = channel["id"]
                channel_name = channel["name"]
                is_member = channel.get("is_member", False)

                if not is_member:
                    try:
                        slack_client.conversations_join(channel=channel_id)
                        logger.info(f"Joined public channel: #{channel_name}")
                        joined_count += 1
                    except SlackApiError as e:
                        if e.response["error"] == "already_in_channel":
                            skipped_count += 1
                        else:
                            logger.warning(f"Could not join #{channel_name}: {e.response['error']}")
                else:
                    skipped_count += 1

            # Check if there are more channels to fetch
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        logger.info(f"Finished joining public channels: {joined_count} joined, {skipped_count} already a member")

    except SlackApiError as e:
        logger.error(f"Failed to join public channels: {e.response['error']}")
    except Exception as e:
        logger.exception(f"Error joining public channels: {e}")
