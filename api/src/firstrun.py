import argparse
from datetime import datetime, timedelta
from getpass import getpass
from typing import Any, Dict, Generic, Literal, Optional, Tuple, TypeVar, cast

from basic_types.enums import PriceLevel
from init_db import init_db
from membership.models import Group, Member, Permission
from membership.permissions import register_permissions
from membership.views import member_entity
from service.api_definition import ALL_PERMISSIONS
from service.config import config
from service.db import db_session
from service.logging import logger
from shop.accounting.accounting import AccountingEntryType
from shop.models import (
    GiftCard,
    Product,
    ProductAccountsCostCenters,
    ProductAction,
    ProductCategory,
    ProductGiftCardMapping,
    Transaction,
    TransactionAccount,
    TransactionAction,
    TransactionContent,
    TransactionCostcenter,
)
from sqlalchemy import func

YELLOW = "\u001b[33m"
GREEN = "\u001b[32m"
RED = "\u001b[31m"
BLUE = "\u001b[34m"
RESET = "\u001b[0m"


def banner(color: Any, message: str) -> None:
    line = "#" * (len(message) + (1 + 3) * 2)
    print(color)
    print(line)
    print("### " + message + " ###")
    print(line)
    print(RESET)


def get_or_create(model: Any, defaults: Optional[Any] = None, **kwargs: Any) -> Any:
    entity = db_session.query(model).filter_by(**kwargs).first()
    if entity:
        return entity

    entity = model(**{**kwargs, **defaults}) if defaults else model(**{**kwargs})
    db_session.add(entity)
    db_session.flush()
    return entity


def create_db() -> None:
    banner(BLUE, "Making Sure Database Tables Exist")
    init_db()


def admin_group() -> Any:
    banner(BLUE, "Adding Admin Permissions")

    logger.info(f"Adding permissions: {ALL_PERMISSIONS}")
    register_permissions(ALL_PERMISSIONS)

    logger.info("Creating admin group.")
    admins = get_or_create(Group, name="admins", defaults=dict(title="Admins"))
    for permission in db_session.query(Permission):
        admins.permissions.append(permission)

    db_session.commit()
    return admins


def create_admin(admins: Any) -> None:
    banner(BLUE, "Admin User")

    while True:
        s = input(
            "Do you want to create a new admin user"
            " (you can later use the create_user.py script to create users)? [Y/n]: "
        )
        if s in ["n", "no"]:
            return
        if s in {"", "y", "yes"}:
            break

    while True:
        try:
            member = member_entity.create(
                dict(
                    firstname=input("First name: "),
                    lastname=input("Last name: "),
                    email=input("Email: "),
                    unhashed_password=getpass("Password: "),
                    pending_activation=False,
                    price_level=PriceLevel.Normal.value,
                )
            )
            member_id = member["member_id"]

            logger.info(f"Adding new member {member_id} to admin group.")
            admins.members.append(db_session.query(Member).get(member_id))
            db_session.commit()
            break
        except Exception as e:
            # This may fail when for example the password was too weak
            print(e)
            print("Something went wrong while creating the new user. Please try again.")


def create_members() -> None:
    banner(RED, "Creating Fake Members")

    get_or_create(
        Member,
        email="first1.last1@gmail.com",
        defaults=dict(
            member_number=1001,
            firstname="first1",
            lastname="last1",
            price_level="normal",
            pending_activation=False,
        ),
    )
    get_or_create(
        Member,
        email="first2.last2@gmail.com",
        defaults=dict(
            member_number=1002,
            firstname="first2",
            lastname="last2",
            price_level="normal",
            pending_activation=False,
        ),
    )
    get_or_create(
        Member,
        email="first3.last3@gmail.com",
        defaults=dict(
            member_number=1003,
            firstname="first3",
            lastname="last3",
            price_level="low_income_discount",
            pending_activation=False,
        ),
    )

    db_session.commit()


def create_shop_products() -> None:
    banner(BLUE, "Creating Fake Shop Categories")

    display_order_category = db_session.query(func.max(ProductCategory.display_order)).scalar() or 0
    member_category = get_or_create(
        ProductCategory, name="Membership", defaults=dict(display_order=display_order_category + 1)
    )
    consumption_category = get_or_create(
        ProductCategory, name="Consumption", defaults=dict(display_order=display_order_category + 2)
    )
    tools_category = get_or_create(
        ProductCategory, name="Tools", defaults=dict(display_order=display_order_category + 3)
    )
    others_category = get_or_create(
        ProductCategory, name="Other", defaults=dict(display_order=display_order_category + 4)
    )

    banner(BLUE, "Creating Fake Shop Products")

    display_order_product = db_session.query(func.max(Product.display_order)).scalar() or 0
    prod1 = get_or_create(
        Product,
        name="Base membership",
        defaults=dict(
            price=200,
            unit="år",
            display_order=display_order_product + 1,
            category_id=member_category.id,
            product_metadata={
                "allowed_price_levels": ["low_income_discount"],
                "special_product_id": "single_membership_year",
            },
        ),
    )
    get_or_create(ProductAction, product_id=prod1.id, value=365, action_type="add_membership_days")

    prod2 = get_or_create(
        Product,
        name="Makerspace access",
        defaults=dict(
            price=575,
            unit="mån",
            display_order=display_order_product + 2,
            category_id=member_category.id,
            product_metadata={
                "allowed_price_levels": ["low_income_discount"],
                "special_product_id": "single_labaccess_month",
            },
        ),
    )
    get_or_create(ProductAction, product_id=prod2.id, value=365, action_type="add_membership_days")
    get_or_create(ProductAction, product_id=prod2.id, value=30, action_type="add_labaccess_days")

    prod3 = get_or_create(
        Product,
        name="Makerspace access starter pack",
        defaults=dict(
            price=750,
            unit="st",
            display_order=display_order_product + 3,
            category_id=member_category.id,
            product_metadata={
                "allowed_price_levels": ["low_income_discount"],
                "special_product_id": "access_starter_pack",
            },
        ),
    )
    get_or_create(ProductAction, product_id=prod3.id, value=365, action_type="add_labaccess_days")

    get_or_create(
        Product,
        name="Trälist",
        defaults=dict(
            price=5,
            unit="dm",
            display_order=display_order_product + 4,
            category_id=consumption_category.id,
            product_metadata={},
        ),
    )
    get_or_create(
        Product,
        name="Lödtråd",
        defaults=dict(
            price=20,
            unit="dm",
            product_metadata={},
            category_id=tools_category.id,
            display_order=display_order_product + 5,
        ),
    )
    get_or_create(
        Product,
        name="Tång",
        defaults=dict(
            price=50,
            unit="st",
            product_metadata={},
            category_id=tools_category.id,
            display_order=display_order_product + 6,
        ),
    )
    get_or_create(
        Product,
        name="Färgat papper",
        defaults=dict(
            price=7,
            unit="st",
            product_metadata={},
            category_id=consumption_category.id,
            display_order=display_order_product + 7,
        ),
    )
    get_or_create(
        Product,
        name="Fjädrar",
        defaults=dict(
            price=1,
            unit="st",
            product_metadata={},
            category_id=others_category.id,
            display_order=display_order_product + 8,
        ),
    )
    db_session.commit()


def create_shop_transactions() -> None:
    banner(GREEN, "Creating Fake Shop Transactions And Content")

    tools_category = get_or_create(ProductCategory, name="Tools")

    products = db_session.query(Product).filter_by(category_id=tools_category.id).all()
    numdays_list = [1, 10, 35, 400]
    index = 1

    for product in products:
        for numdays in numdays_list:
            test_date = datetime.today() - timedelta(days=numdays)

            transaction = get_or_create(
                Transaction,
                id=index,
                defaults=dict(
                    member_id=1,
                    amount=product.price,
                    status="completed",
                    created_at=test_date,
                ),
            )
            transaction_content = get_or_create(
                TransactionContent,
                id=index,
                defaults=dict(
                    transaction_id=transaction.id,
                    product_id=product.id,
                    count=1,
                    amount=product.price,
                ),
            )
            index += 1

    # A transaction that is pending
    product = products[0]
    transaction = get_or_create(
        Transaction,
        id=index,
        defaults=dict(
            member_id=1,
            amount=product.price,
            status="pending",
            created_at=test_date,
        ),
    )
    transaction_content = get_or_create(
        TransactionContent,
        id=index,
        defaults=dict(
            transaction_id=transaction.id,
            product_id=product.id,
            count=1,
            amount=product.price,
        ),
    )
    index += 1

    # A failed transaction
    product = products[1]
    transaction = get_or_create(
        Transaction,
        id=index,
        defaults=dict(
            member_id=1,
            amount=product.price,
            status="failed",
            created_at=test_date,
        ),
    )
    transaction_content = get_or_create(
        TransactionContent,
        id=index,
        defaults=dict(
            transaction_id=transaction.id,
            product_id=product.id,
            count=1,
            amount=product.price,
        ),
    )
    index += 1

    # A transaction with a membership
    membership_prod = get_or_create(Product, name="Base membership")
    transaction = get_or_create(
        Transaction,
        id=index,
        defaults=dict(member_id=1, amount=membership_prod.price, status="completed", created_at=datetime.now()),
    )
    transaction_content = get_or_create(
        TransactionContent,
        id=index,
        defaults=dict(
            transaction_id=transaction.id,
            product_id=membership_prod.id,
            count=1,
            amount=membership_prod.price,
        ),
    )
    get_or_create(
        TransactionAction,
        id=index,
        defaults=dict(
            content_id=transaction_content.id,
            action_type="add_labaccess_days",
            value=10,
            status="completed",
            completed_at=datetime.now(),
        ),
    )
    index += 1

    # A transaction with member_id as null to represent a gift card.
    transaction = get_or_create(
        Transaction,
        id=index,
        defaults=dict(
            member_id=None,
            amount=100,
            status="completed",
            created_at=datetime.now(),
        ),
    )

    # TODO this should probabl be associated with some sort of gift card product later
    transaction_content = get_or_create(
        TransactionContent,
        id=index,
        defaults=dict(
            transaction_id=transaction.id,
            product_id=products[0].id,
            count=1,
            amount=100,
        ),
    )
    index += 1

    db_session.commit()


def create_shop_accounts_cost_centers() -> None:
    banner(BLUE, "Creating Fake Account and Cost Centers")

    accounts = []
    for account_id in range(1, 3):
        accounts.append(
            get_or_create(
                TransactionAccount,
                account=str(4000 + account_id),
                defaults=dict(
                    display_order=account_id,
                    description=f"Account {account_id}",
                ),
            )
        )

    cost_centers = []
    for cost_center_id in range(1, 3):
        cost_centers.append(
            get_or_create(
                TransactionCostcenter,
                cost_center=f"cost center number {cost_center_id}",
                defaults=dict(
                    display_order=cost_center_id,
                    description=f"CostCenter {cost_center_id}",
                ),
            )
        )

    tools_category = get_or_create(ProductCategory, name="Tools")
    products = db_session.query(Product).filter_by(category_id=tools_category.id).all()
    for product in products:
        for i, account in enumerate(accounts):
            for j, cost_center in enumerate(cost_centers):
                debits = 0 if i % 2 == 0 else 0.5
                credit_value = 0.3 if j % 2 == 0 else 0.7
                credits = 0 if i % 2 != 0 else credit_value
                get_or_create(
                    ProductAccountsCostCenters,
                    product_id=product.id,
                    account_id=account.id,
                    cost_center_id=cost_center.id,
                    defaults=dict(fraction=debits, type=AccountingEntryType.DEBIT.value),
                )
                get_or_create(
                    ProductAccountsCostCenters,
                    product_id=product.id,
                    account_id=account.id,
                    cost_center_id=cost_center.id,
                    defaults=dict(fraction=credits, type=AccountingEntryType.CREDIT.value),
                )

    db_session.commit()


def create_shop_gift_cards() -> None:
    banner(YELLOW, "Creating Fake 'Gift Cards' and 'Gift Card & Product Mappings'")

    # Get existing product Makerspace access starter pack
    product = get_or_create(
        Product,
        name="Makerspace access starter pack",
    )

    for i in range(2):
        status = "valid" if i % 2 == 0 else "used"
        gift_card = get_or_create(
            GiftCard,
            amount=product.price,
            validation_code=str(129895190 + i),
            email="test@fake.com",
            status=status,
        )

        get_or_create(
            ProductGiftCardMapping,
            gift_card_id=gift_card.id,
            product_id=product.id,
            product_quantity=1,
            amount=product.price,
        )

    db_session.commit()


def firstrun() -> None:
    create_db()
    admins = admin_group()
    create_admin(admins)

    while True:
        s = input("Do you want to add various fake data for development purposes? [Y/n]: ")
        if s in ["n", "no"]:
            create_dev_data = False
            break
        if s in {"", "y", "yes"}:
            create_dev_data = True
            break

    if create_dev_data:
        create_members()
        create_shop_products()
        create_shop_transactions()
        create_shop_accounts_cost_centers()
        create_shop_gift_cards()

    banner(
        GREEN,
        "Done, now run servers with 'make dev' then browse admin gui at "
        f"{config.get('HOST_FRONTEND')} and member gui at {config.get('HOST_PUBLIC')}, see also README.md.",
    )


if __name__ == "__main__":
    firstrun()
