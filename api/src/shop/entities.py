from datetime import datetime, timezone

from membership.models import Member
from service.db import db_session
from service.entity import ASC, DESC, Entity, ExpandField
from service.error import BadRequest, NotFound

from shop.models import (
    GiftCard,
    Product,
    ProductAccountsCostCenters,
    ProductAction,
    ProductCategory,
    ProductGiftCardMapping,
    ProductImage,
    Transaction,
    TransactionAccount,
    TransactionAction,
    TransactionContent,
    TransactionCostCenter,
)
from shop.ordered_entity import OrderedEntity
from shop.product_image_entity import ProductImageEntity

category_entity = OrderedEntity(
    ProductCategory,
    default_sort_column="name",
    default_sort_order=ASC,
)


product_entity = OrderedEntity(
    Product,
    default_sort_column="name",
    default_sort_order=ASC,
    search_columns=("name", "description"),
    expand_fields={
        "product_accounting": ExpandField(
            Product.product_accounting,
            [
                ProductAccountsCostCenters.account_id,
                ProductAccountsCostCenters.cost_center_id,
                ProductAccountsCostCenters.type,
            ],
        )
    },
)


class TransactionActionEntity(Entity):
    def delete(self, entity_id, commit=True):
        entity = db_session.get(self.model, entity_id)
        if not entity:
            raise NotFound("Could not find any entity with specified parameters.")

        if entity.status is not TransactionAction.Status.pending:
            raise BadRequest("Cannot delete a transaction action that is not pending.")

        entity.status = TransactionAction.Status.cancelled
        entity.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        db_session.commit()

        return self.to_obj(entity)


product_action_entity = Entity(ProductAction)


product_image_entity = ProductImageEntity(
    ProductImage,
    search_columns=("name",),
)


transaction_entity = Entity(
    Transaction,
    expand_fields={
        "member": ExpandField(Transaction.member, [Member.firstname, Member.lastname, Member.member_number])
    },
    search_columns=("id", "created_at", "status", "member_id", "amount"),
)


transaction_content_entity = Entity(
    TransactionContent,
    default_sort_column=None,
    expand_fields={"product": ExpandField(TransactionContent.product, [Product.name])},
)


transaction_action_entity = TransactionActionEntity(
    TransactionAction,
    default_sort_column=None,
)


transaction_account_entity = OrderedEntity(
    TransactionAccount,
    default_sort_column="account",
    default_sort_order=ASC,
    search_columns=("account", "description"),
)

transaction_cost_center_entity = OrderedEntity(
    TransactionCostCenter,
    default_sort_column="cost_center",
    default_sort_order=ASC,
    search_columns=("cost_center", "description"),
)

product_accounting_entity = Entity(
    ProductAccountsCostCenters,
    default_sort_column="id",
    default_sort_order=ASC,
    search_columns=("cost_center_id", "account_id"),
)

gift_card_entity = Entity(
    GiftCard,
    default_sort_column="id",
    default_sort_order=DESC,
    search_columns=("id", "created_at", "status", "email"),
)

gift_card_content_entity = Entity(
    ProductGiftCardMapping,
    default_sort_column="id",
    default_sort_order=DESC,
    expand_fields={"product": ExpandField(ProductGiftCardMapping.product, [Product.name])},
)
