import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from fnmatch import fnmatch
from logging import getLogger
from typing import Any, Dict, List, Optional, TypedDict

import requests
from redis_cache import redis_connection
from serde import from_dict, serde
from serde.json import from_json, to_json
from service.config import config

logger = getLogger("trello")

# Global constant for the board URL (set this to your Trello board URL)
# Expect TRELLO_BOARD_URL like https://trello.com/b/{board_id}/...
TRELLO_BOARD_URL = config.get("TRELLO_BOARD_URL_TASKS", default="")
TRELLO_BOARD_ID = TRELLO_BOARD_URL.rstrip("/").split("/")[-2] if "/b/" in TRELLO_BOARD_URL else TRELLO_BOARD_URL

TRELLO_KEY = config.get("TRELLO_KEY")
TRELLO_TOKEN = config.get("TRELLO_TOKEN")
TRELLO_API_BASE = "https://api.trello.com/1"

TEMPLATE_LIST_NAME = "* Templates"
PRIMARY_SOURCE_LIST_NAME = "Available Tasks"
SOURCE_LIST_NAME = "Available Tasks*"
DONE_LIST_NAME = "Done"


class TrelloList(TypedDict):
    id: str
    name: str


def _auth_params() -> Dict[str, str]:
    return {"key": TRELLO_KEY, "token": TRELLO_TOKEN}


@serde
class Label:
    id: str
    name: str
    color: str
    uses: int | None = None
    idBoard: str | None = None


@serde
class PluginDataEntry:
    id: str
    idPlugin: str
    value: str


@serde
class TrelloAttachment:
    id: str
    name: str
    url: str
    mimeType: str


@serde
class TrelloCard:
    id: str
    name: str
    idList: str
    labels: List[Label]
    desc: Optional[str]
    attachments: Optional[List[TrelloAttachment]]
    pluginData: Optional[List[PluginDataEntry]]


def download_attachment(attachment: TrelloAttachment) -> bytes:
    headers = {"Authorization": f'OAuth oauth_consumer_key="{TRELLO_KEY}", oauth_token="{TRELLO_TOKEN}"'}
    response = requests.get(attachment.url, timeout=10, headers=headers)
    response.raise_for_status()
    return response.content


def trello_id_to_timestamp(trello_id: str) -> datetime:
    # Trello ID is a base16-encoded string; first 8 chars are timestamp in seconds since epoch
    ts_hex = trello_id[:8]
    return datetime.fromtimestamp(int(ts_hex, 16))


def _fetch_cards_from_trello() -> List[TrelloCard]:
    if TRELLO_BOARD_URL == "":
        return []

    # Fetch cards on the board in lists; get labels and list info
    # Find board id from TRELLO_BOARD_URL path
    url = f"{TRELLO_API_BASE}/boards/{TRELLO_BOARD_ID}/cards"
    params = {"fields": "name,idList,labels,desc", "pluginData": "1", "attachments": "1", **_auth_params()}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()

    return from_dict(List[TrelloCard], r.json())


def get_all_labels() -> List[Label]:
    if TRELLO_BOARD_URL == "":
        return []

    # Fetch all labels for the board
    url = f"{TRELLO_API_BASE}/boards/{TRELLO_BOARD_ID}/labels"
    params = {"fields": "id,name,color", **_auth_params()}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()

    return from_dict(List[Label], r.json())


def get_list_ids_by_name(name: str) -> list[str]:
    if TRELLO_BOARD_URL == "":
        return []

    # Return id of list
    url = f"{TRELLO_API_BASE}/boards/{TRELLO_BOARD_ID}/lists"
    r = requests.get(url, params={"fields": "name", **_auth_params()}, timeout=10)
    r.raise_for_status()

    data: List[TrelloList] = r.json()
    result = []
    for lst in data:
        if fnmatch(lst.get("name", ""), name):
            result.append(lst["id"])
    return result


def get_list_id_by_name(name: str) -> Optional[str]:
    lists = get_list_ids_by_name(name)
    if not lists:
        return None
    if len(lists) > 1:
        logger.error(f"Multiple lists found on Trello matching name '{name}'")
        return None
    return lists[0]


def cached_cards(list_name: str) -> List[TrelloCard]:
    if TRELLO_BOARD_URL == "":
        return []

    cache_key = f"tasks:cards:{list_name.replace(' ', '_').replace('*', 'star').lower()}"
    cached_data = redis_connection.get(cache_key)

    if cached_data:
        return from_json(List[TrelloCard], cached_data)

    cards = _fetch_cards_from_trello()
    list_ids = get_list_ids_by_name(list_name)
    if not list_ids:
        raise RuntimeError(f"No lists matching '{list_name}' found on Trello board")
    cards = [c for c in cards if c.idList in list_ids]

    redis_connection.setex(cache_key, timedelta(hours=3), to_json(cards))
    return cards


def get_card(card_id: str) -> TrelloCard:
    url = f"{TRELLO_API_BASE}/cards/{card_id}"
    params = {"fields": "name,idList,labels,desc", "pluginData": "1", "attachments": "1", **_auth_params()}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()

    return from_dict(TrelloCard, r.json())


def delete_card(card_id: str) -> None:
    """
    Delete a card from Trello using its ID.
    """
    url = f"{TRELLO_API_BASE}/cards/{card_id}"
    response = requests.delete(url, params=_auth_params(), timeout=10)
    response.raise_for_status()


def refresh_cache() -> None:
    # Force fresh fetch (used before updates)
    keys = redis_connection.keys("tasks:cards:*")
    for key in keys:
        redis_connection.delete(key)


def move_card_to_done(card_id: str) -> None:
    done_id = get_list_id_by_name(DONE_LIST_NAME)
    if not done_id:
        raise RuntimeError("Done list not found on Trello board")
    url = f"{TRELLO_API_BASE}/cards/{card_id}"
    resp = requests.put(url, params={"idList": done_id, **_auth_params()}, timeout=10)
    resp.raise_for_status()
    refresh_cache()


def add_comment_to_card(card_id: str, text: str) -> None:
    url = f"{TRELLO_API_BASE}/cards/{card_id}/actions/comments"
    resp = requests.post(url, params={"text": text, **_auth_params()}, timeout=10)
    resp.raise_for_status()


if __name__ == "__main__":
    # simple test: print cached todo cards
    todo_cards = cached_cards(SOURCE_LIST_NAME)
    print(f"Found {len(todo_cards)} TODO cards:")
    for card in todo_cards:
        print(f"- {card.name} (id: {card.id})")
