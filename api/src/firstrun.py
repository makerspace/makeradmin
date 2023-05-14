import argparse

from sqlalchemy import func

from init_db import init_db
from membership.models import Group, Permission, Member
from membership.permissions import register_permissions
from membership.views import member_entity
from service.api_definition import ALL_PERMISSIONS
from service.config import config
from service.db import db_session
from service.logging import logger
from shop.models import ProductCategory
from getpass import getpass

YELLOW = "\u001b[33m"
GREEN = "\u001b[32m"
RED = "\u001b[31m"
BLUE = "\u001b[34m"
RESET = "\u001b[0m"


def banner(color, message):
    line = "#" * (len(message) + (1 + 3) * 2)
    print(color)
    print(line)
    print('### ' + message + ' ###')
    print(line)
    print(RESET)


def get_or_create(model, defaults=None, **kwargs):
    entity = db_session.query(model).filter_by(**kwargs).first()
    if entity:
        return entity

    entity = model(**{**kwargs, **defaults})
    db_session.add(entity)
    db_session.flush()
    return entity


def create_db():
    banner(BLUE, "Making Sure Database Tables Exist")
    init_db()


def admin_group():
    banner(BLUE, "Adding Admin Permissions")

    logger.info(f"Adding permissions: {ALL_PERMISSIONS}")
    register_permissions(ALL_PERMISSIONS)

    logger.info("Creating admin group.")
    admins = get_or_create(Group, name='admins', defaults=dict(title='Admins'))
    for permission in db_session.query(Permission):
        admins.permissions.append(permission)

    db_session.commit()
    return admins


def create_admin(admins):
    banner(BLUE, "Admin User")

    s = input("Do you want to create a new admin user"
              " (you can later use the create_user.py script to create users)? [Y/n]: ")
    if s.lower() not in {"", "y", "yes"}:
        return

    while True:
        try:
            member = member_entity.create(dict(
                firstname=input("First name: "),
                lastname=input("Last name: "),
                email=input("Email: "),
                unhashed_password=getpass("Password: "),
            ))
            member_id = member['member_id']

            logger.info(f"Addmin new menber {member_id} to admin group.")
            admins.members.append(db_session.query(Member).get(member_id))
            db_session.commit()
            break
        except Exception as e:
            # This may fail when for example the password was too weak
            print(e)
            print("Something went wrong while creating the new user. Please try again.")



def create_members():
    banner(RED, "TDOO: Creating Fake Members")


def create_shop_products():
    banner(BLUE, "Creating Fake Shop Products")
    display_order = db_session.query(func.max(ProductCategory.display_order)).scalar() or 0
    get_or_create(ProductCategory, name='Medlemskap', defaults=dict(display_order=display_order + 1))
    get_or_create(ProductCategory, name='Förbrukning', defaults=dict(display_order=display_order + 2))
    get_or_create(ProductCategory, name='Verktyg', defaults=dict(display_order=display_order + 3))
    get_or_create(ProductCategory, name='Övrigt', defaults=dict(display_order=display_order + 4))
    db_session.commit()


def firstrun():
    create_db()
    admins = admin_group()
    create_admin(admins)
    create_members()
    create_shop_products()

    banner(GREEN, "Done, now run servers with 'make dev' then browse admin gui at "
                  f"{config.get('HOST_FRONTEND')} and member gui at {config.get('HOST_PUBLIC')}, see also README.md.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Initialize the database with some development data.')
    args = parser.parse_args()

    firstrun()
