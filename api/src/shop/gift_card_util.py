from secrets import token_hex
from messages.message import send_message
from messages.models import MessageTemplate


def generate_gift_card_code(length=16):
    """
    Generate a unique validation code for gift cards.

    Parameters:
    - length: The length of the validation code (default is 16).

    Returns:
    A unique validation code.
    """
    return token_hex(length)[:length].upper()


def send_gift_card_email(gift_card):
    """
    Send an email to the recipient of a gift card.

    Parameters:
    - gift_card: The gift card to send an email for.
    """
    if gift_card.email:
        send_message(
            template=MessageTemplate.GIFT_CARD_PURCHASE,
            member=None,
            recipient_email=gift_card.email,
            gift_card=gift_card,
        )
    else:
        # TODO: Log this error
        # Do I need to check for this case? Is it even possible?
        print("Error: Gift card does not have a valid recipient email.")
