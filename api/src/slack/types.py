from typing import Optional

from serde import serde


@serde
class SlackFile:
    id: str
    url: str


@serde
class SlackSelectedOption:
    value: str


@serde
class SlackInteractionAction:
    action_id: str
    value: str | None = None
    selected_option: SlackSelectedOption | None = None


@serde
class SlackMessage:
    ts: str


@serde
class SlackUser:
    id: str


@serde
class SlackChannel:
    id: str


@serde
class SlackViewStateValue:
    type: str
    selected_options: Optional[list[SlackSelectedOption]] = None


@serde
class SlackViewState:
    values: dict[str, dict[str, SlackViewStateValue]]


@serde
class SlackInteraction:
    actions: list[SlackInteractionAction]
    user: SlackUser
    message: SlackMessage
    trigger_id: str
    channel: SlackChannel
    state: Optional[SlackViewState] = None
