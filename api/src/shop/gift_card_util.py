from secrets import token_hex


def generate_gift_card_code(length=16):
    """
    Generate a unique validation code for gift cards.

    Parameters:
    - length: The length of the validation code (default is 16).

    Returns:
    A unique validation code.
    """
    return token_hex(length)[:length]