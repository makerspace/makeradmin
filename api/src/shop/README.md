# Stripe

For the general introduction to how we use stripe, see the main [readme](../../../README.md)

## Makeradmin stripe relationships

The relationship between the structures such as Product in makeradmin and their conterparts in stripe are, because of differences in the various stripe apis, done in different ways.

### Product

The connection between stripe product and makeradmin product is stored in the database. It is possible to set the id of a stripe product on creation but it's not possible to change and thus basing the connection on ids being identical can break if something changes.

### Price

A part of the price object in stripe is lookup_key. This is used to keep track of the stripe prices. We set the lookup key based on the corresponding makeradmin product's id and what type of price it is (e.g. the recurring price for the subscription).

### Customer

The stripe customer api doesn't support the ways we keep track of products and prices. To keep track of the member stripe customer relationship we store the stripe customer id in the Member table in the database.

## Subscriptions

See the documentation in [stripe_subscriptions.py](stripe_subscriptions.py)
