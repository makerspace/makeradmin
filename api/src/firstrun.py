import argparse
import random
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
from shop.models import (
    AccountingEntryType,
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
    TransactionCostCenter,
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


def next_display_order(model) -> int:
    order = db_session.query(func.max(model.display_order)).scalar() or 0
    return order + 1


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

            def get_first_name():
                if config.get("FIRSTRUN_AUTO_ADMIN_FIRSTNAME", log_level=False):
                    return config.get("FIRSTRUN_AUTO_ADMIN_FIRSTNAME", log_level=False)
                else:
                    return input("First name: ")

            def get_last_name():
                if config.get("FIRSTRUN_AUTO_ADMIN_LASTNAME", log_level=False):
                    return config.get("FIRSTRUN_AUTO_ADMIN_LASTNAME", log_level=False)
                else:
                    return input("Last name: ")

            def get_email():
                if config.get("FIRSTRUN_AUTO_ADMIN_EMAIL", log_level=False):
                    return config.get("FIRSTRUN_AUTO_ADMIN_EMAIL", log_level=False)
                else:
                    return input("Email: ")

            def get_password():
                if config.get("FIRSTRUN_AUTO_ADMIN_PASSWORD", log_level=False):
                    return config.get("FIRSTRUN_AUTO_ADMIN_PASSWORD", log_level=False)
                else:
                    return getpass("Password: ")

            member = member_entity.create(
                dict(
                    firstname=get_first_name(),
                    lastname=get_last_name(),
                    email=get_email(),
                    unhashed_password=get_password(),
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


def create_required_stripe_products():
    banner(BLUE, "Creating required Stripe products")

    member_category = get_or_create(
        ProductCategory, name="Membership", defaults=dict(display_order=next_display_order(ProductCategory))
    )

    prod1 = get_or_create(
        Product,
        name="Base membership",
        defaults=dict(
            price=200,
            unit="år",
            display_order=next_display_order(Product),
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
            display_order=next_display_order(Product),
            category_id=member_category.id,
            product_metadata={
                "allowed_price_levels": ["low_income_discount"],
                "special_product_id": "single_labaccess_month",
            },
        ),
    )
    get_or_create(ProductAction, product_id=prod2.id, value=30, action_type="add_labaccess_days")

    prod3 = get_or_create(
        Product,
        name="Makerspace access starter pack",
        defaults=dict(
            price=750,
            unit="st",
            display_order=next_display_order(Product),
            category_id=member_category.id,
            product_metadata={
                "allowed_price_levels": ["low_income_discount"],
                "special_product_id": "access_starter_pack",
            },
        ),
    )
    get_or_create(ProductAction, product_id=prod3.id, value=365, action_type="add_labaccess_days")
    get_or_create(ProductAction, product_id=prod2.id, value=60, action_type="add_labaccess_days")

    prod = get_or_create(
        Product,
        name="Base membership subscription",
        defaults=dict(
            price=200,
            unit="år",
            display_order=next_display_order(Product),
            category_id=member_category.id,
            product_metadata={
                "allowed_price_levels": ["low_income_discount"],
                "special_product_id": "membership_subscription",
                "subscription_type": "membership",
            },
        ),
    )
    get_or_create(ProductAction, product_id=prod.id, value=365, action_type="add_membership_days")

    prod = get_or_create(
        Product,
        name="Makerspace access subscription",
        defaults=dict(
            price=350,
            unit="mån",
            display_order=next_display_order(Product),
            category_id=member_category.id,
            product_metadata={
                "allowed_price_levels": ["low_income_discount"],
                "special_product_id": "labaccess_subscription",
                "subscription_type": "labaccess",
            },
        ),
    )
    get_or_create(ProductAction, product_id=prod.id, value=30, action_type="add_labaccess_days")

    db_session.commit()


def create_members() -> None:
    banner(RED, "Creating Fake Members")

    price_levels = ["normal", "low_income_discount"]
    for num in range(1, 55):
        get_or_create(
            Member,
            email="first" + str(num) + ".last" + str(num) + "@gmail.com",
            defaults=dict(
                member_number=1000 + num,
                firstname="first" + str(num),
                lastname="last" + str(num),
                price_level=random.choice(price_levels),
                pending_activation=False,
            ),
        )

    db_session.commit()


def create_groups() -> None:
    banner(RED, "Creating Fake Groups")

    register_permissions(ALL_PERMISSIONS)
    for num in range(1, 26):
        current_group = get_or_create(Group, name="Group" + str(num), defaults=dict(title="Group" + str(num)))
        for permission in db_session.query(Permission):
            current_group.permissions.append(permission)

    db_session.commit()


def create_shop_products() -> None:
    banner(BLUE, "Creating Fake Shop Categories")

    categories = [
        "Membership",
        "Consumption",
        "Tools",
        "Other",
        "Trä",
        "Tyg",
        "Metall",
        "Garn",
        "Övrig textil",
        "Färg",
        "Lim",
        "Vinyl",
        "Laser",
        "Skivor",
        "Papper",
        "Kartong",
        "Små verktyg",
        "Stora verktyg",
        "Farliga verktyg",
        "Känsliga verktyg",
        "Fyllnadsmassor",
        "Påbörjade projekt",
        "Band",
        "Sprayer",
        "Dryck",
        "Fika",
    ]

    for name in categories:
        get_or_create(ProductCategory, name=name, defaults=dict(display_order=next_display_order(ProductCategory)))

    product_names_consumption = [
        "Trälist",
        "Färgat papper",
        "Kork",
        "Fjädrar",
        "Bräda",
        "Tygbit",
        "Frigolit",
        "Filt tygbit",
        "Fleece tygbit",
        "Tråd",
        "Pappersark",
        "Brodyrtråd",
        "Tejp",
        "Silkespapper",
        "Kartong",
        "Wellpapp",
        "Playwood",
        "Flörtkulor",
        "Ullgarn",
        "Akrylgarn",
        "Bomullsgarn",
        "Glittertråd",
        "Vinyl",
    ]
    consumption_category = get_or_create(ProductCategory, name="Consumption")

    for name in product_names_consumption:
        get_or_create(
            Product,
            name=name,
            defaults=dict(
                price=random.randint(5, 100),
                unit="dm",
                display_order=next_display_order(Product),
                category_id=consumption_category.id,
                product_metadata={},
            ),
        )

    product_names_tools = ["Lödtråd", "Tång", "Sågblad", "Hammare", "Nål"]
    tools_category = get_or_create(ProductCategory, name="Tools")

    for name in product_names_tools:
        get_or_create(
            Product,
            name=name,
            defaults=dict(
                price=random.randint(5, 100),
                unit="st",
                display_order=next_display_order(Product),
                category_id=tools_category.id,
                product_metadata={},
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

    # TODO this should be associated with some sort of gift card product later
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

    debits_account = get_or_create(
        TransactionAccount,
        account="1000",
        defaults=dict(
            display_order=1,
            description=f"Debits account",
        ),
    )

    accounts = []
    for account_id in range(2, 30):
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
    for cost_center_id in range(1, 30):
        cost_centers.append(
            get_or_create(
                TransactionCostCenter,
                cost_center=f"cost center number {cost_center_id}",
                defaults=dict(
                    display_order=cost_center_id,
                    description=f"CostCenter {cost_center_id}",
                ),
            )
        )

    products = db_session.query(Product).all()

    for product in products:
        debits = 100
        credits = 100
        get_or_create(
            ProductAccountsCostCenters,
            product_id=product.id,
            account_id=random.choice(accounts).id,
            cost_center_id=random.choice(cost_centers).id,
            type=AccountingEntryType.CREDIT.value,
            fraction=credits,
        )
        get_or_create(
            ProductAccountsCostCenters,
            product_id=product.id,
            account_id=debits_account.id,
            type=AccountingEntryType.DEBIT.value,
            fraction=debits,
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

    create_dev_data = False
    while True:
        s = input("Do you want to add various fake data for development purposes? [Y/n]: ")
        if s in ["n", "no"]:
            break
        if s in {"", "y", "yes"}:
            create_dev_data = True
            break

    create_stripe_data = True
    if not create_dev_data:
        while True:
            s = input(
                "Do you want to add products for stripe and memberships?"
                " (Some products are required for the member portal and regristration page to load) [Y/n]: "
            )
            if s in ["n", "no"]:
                create_stripe_data = False
                break
            if s in {"", "y", "yes"}:
                create_stripe_data = True
                break

    if create_stripe_data:
        create_required_stripe_products()

    if create_dev_data:
        create_members()
        create_groups()
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
