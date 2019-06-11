from jsonschema import validate, ValidationError

from service.config import debug_mode
from service.error import UnprocessableEntity

STRIPE_3D_SECURE_REQUIRED = 'required'
STRIPE_3D_SECURE_RECOMMENDED = 'recommended'
STRIPE_3D_SECURE_OPTIONAL = 'optional'
STRIPE_3D_SECURE_NOT_SUPPORTED = 'not_supported'


purchase_schema = dict(
    type="object",
    required=['cart', 'expected_sum', 'stripe_card_source_id', 'stripe_card_3d_secure'],
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
        stripe_card_source_id=dict(type="string"),
        stripe_card_3d_secure=dict(enum=[
            STRIPE_3D_SECURE_REQUIRED,
            STRIPE_3D_SECURE_RECOMMENDED,
            STRIPE_3D_SECURE_OPTIONAL,
            STRIPE_3D_SECURE_NOT_SUPPORTED,
        ]),
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
