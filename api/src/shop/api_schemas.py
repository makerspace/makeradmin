from jsonschema import validate, ValidationError

from service.config import debug_mode
from service.error import UnprocessableEntity


purchase_schema = dict(
    type="object",
    required=['cart', 'expected_sum', 'stripe_payment_method_id'],
    additionalProperties=False,
    properties=dict(
        cart=dict(
            type="array",
            items=dict(
                type="object",
                required=['count', 'id'],
                additionalProperties=False,
                properties=dict(
                    count=dict(type="integer"),
                    id=dict(type="integer"),
                )
            ),
        ),
        expected_sum=dict(type="number"),
        stripe_payment_method_id=dict(type="string"),
    )
)


register_schema = dict(
    type="object",
    required=['purchase'],
    additionalProperties=False,
    properties=dict(
        purchase=purchase_schema,
        member=dict(
            type="object",
            required=['email', 'firstname'],
            additionalProperties=False,
            properties=dict(
                email=dict(
                    type="string",
                    pattern="^[a-zA-Z0-9.!#$%&'*+\\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}"
                            "[a-zA-Z0-9])?(?:\\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
                ),
                firstname=dict(type="string"),
                lastname=dict(type="string"),
                password=dict(type="null"),
                civicregno=dict(type="string"),
                phone=dict(type="string"),
                address_street=dict(type="string"),
                address_city=dict(type="string"),
                address_zipcode=dict(type=["null", "integer"]),
                address_extra=dict(type="string"),
                address_country=dict(type="string"),
            )
        )
    )
)


def validate_data(schema, data):
    try:
        validate(data, schema=schema)
    except ValidationError as e:
        raise UnprocessableEntity(message=f"Data sent in request not in correct format.",
                                  log=debug_mode() and str(e))
