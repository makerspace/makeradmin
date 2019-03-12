

purchase_schema = dict(
    type="object",
    required=['cart', 'duplicatePurchaseRand', 'expectedSum', 'stripeSource', 'stripeThreeDSecure'],
    properties=dict(
        cart=dict(
            type="array",
            items=dict(
                type="object",
                required=['count', 'id'],
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
    properties=dict(
        purchase=purchase_schema,
        member=dict(
            type="object",
            properties=dict(
                email=dict(type="string"),
                firstname=dict(type="string"),
                lastname=dict(type="string"),
                civicregno=dict(type="string"),
                phone=dict(type="string"),
                address_street=dict(type="string"),
                address_city=dict(type="string"),
                address_zipcode=dict(type="string"),
                address_extra=dict(type="string"),
            )
        )
    )
)


