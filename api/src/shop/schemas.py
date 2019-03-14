

purchase_schema = dict(
    type="object",
    required=['cart', 'duplicatePurchaseRand', 'expectedSum', 'stripeSource', 'stripeThreeDSecure'],
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
        duplicatePurchaseRand=dict(type="integer"),
        expectedSum=dict(type="number"),
        stripeSource=dict(type="string"),
        stripeThreeDSecure=dict(type="string"),
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
                email=dict(type="string"),
                firstname=dict(type="string"),
                lastname=dict(type="string"),
                password=dict(type="null"),
                civicregno=dict(type="string"),
                phone=dict(type="string"),
                address_street=dict(type="string"),
                address_city=dict(type="string"),
                address_zipcode=dict(type=["string", "integer"]),
                address_extra=dict(type="string"),
                address_country=dict(type="string"),
            )
        )
    )
)
