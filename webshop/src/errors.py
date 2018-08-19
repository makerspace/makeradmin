from service import BackendException
from decimal import Decimal


class TooSmallAmount(BackendException):
    def __init__(self):
        super().__init__(sv="För litet belopp. Det minsta beloppet som kan handlas för är 50 cent (ca 5 kr).")


class TooLargeAmount(BackendException):
    def __init__(self, threshold: int) -> None:
        super().__init__(sv=f"Köp för över {threshold} kr är inte tillåtna för att undvika misstag."
                            f" Behöver du köpa för så mycket, dela upp köpet i mindre delar.",
                         en=f"Not allowing purchases above {threshold} kr to avoid mistakes.")


class NonMatchingSums(BackendException):
    def __init__(self, expected_sum: Decimal, actual_sum: Decimal) -> None:
        super().__init__(sv=f"Den förväntade summan att betala var {expected_sum}, men produkterna i varukorgen kostar egentligen totalt {actual_sum}.",
                         en=f"Expected total amount to pay to be {expected_sum} but the cart items actually sum to {actual_sum}.")


class NotMember(BackendException):
    def __init__(self):
        super().__init__(sv="Du måste vara en medlem för att kunna köpa material och verktyg.",
                         en="You must be a member to purchase materials and tools.")


class DuplicateTransaction(BackendException):
    def __init__(self):
        super().__init__(sv="Du har redan gjort en betalning för detta.")


class MissingJson(BackendException):
    def __init__(self):
        super().__init__(sv="Ingen json data skickades med anropet. Detta ser ut som en bugg.")


class NotPurelyCents(BackendException):
    def __init__(self, value: Decimal) -> None:
        super().__init__(sv=f"Beloppet kunde inte konverteras till ett helt antal ören ({value}).")


class NotAllowedToPurchase(BackendException):
    def __init__(self, product):
        super().__init__(sv=f"Det är inte tillåtet att köpa produkten med id {product['id']}.")


class CartMustContainNItems(BackendException):
    def __init__(self, n: int) -> None:
        super().__init__(sv=f"Köpet måste innehålla exakt {n} sak.")


class NonNegativeItemCount(BackendException):
    def __init__(self, item: str) -> None:
        super().__init__(sv=f"Kan endast köpa ett positivt antal av produkt {item}.",
                         en=f"Can only buy positive amounts of item {item}.")


class InvalidItemCount(BackendException):
    def __init__(self, item: str, required_count: int, count: int) -> None:
        super().__init__(sv=f"Produkten {item} kan endast köpas exakt {required_count} åt gången,"
                            f" i varukorgen så fanns {count} enheter.",
                         en=f"Can only buy exactly {required_count} of item {item}, found {count}.")


class InvalidItemCountMultiple(BackendException):
    def __init__(self, item: str, smallest_multiple: int, count: int) -> None:
        super().__init__(sv=f"Produkten {item} kan endast köpas i multipler av {smallest_multiple},"
                            f" i varukorgen så fanns {count} enheter.",
                         en=f"Can only buy item {item} in multiples of {smallest_multiple}, found {count}.")


class RoundingError(BackendException):
    def __init__(self):
        super().__init__(sv="Ett avrundningsfel skedde när priset skulle beräknas.",
                         en="Rounding ocurred during price calculations.")


class EmptyCart(BackendException):
    def __init__(self):
        super().__init__(sv="Inga produkter i varukorgen.",
                         en="No items in cart.")


class NoSuchItem(BackendException):
    def __init__(self, item: str) -> None:
        super().__init__(sv=f"Produkten {item} finns inte.",
                         en=f"Item {item} does not exist.")


class PaymentFailed(BackendException):
    def __init__(self, error: str=None) -> None:
        if error is not None:
            super().__init__(sv=f"Betalningen misslyckades, stripe säger {error}.",
                             en=f"Payment failed, stripe says {error}.")
        else:
            super().__init__(sv=f"Betalningen misslyckades.", en=f"Payment failed.")
