#!python
from contextlib import closing

import membership.models
import quiz.models
from IPython import start_ipython
from service.config import get_mysql_config
from service.db import create_mysql_engine
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker


def init_db():
    engine = create_mysql_engine(**get_mysql_config())
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_factory


if __name__ == "__main__":
    session_factory = init_db()

    with closing(session_factory()) as session:
        connection = session.connection()
        execute = connection.execute

        namespace = {
            "session": session,
            "connection": connection,
            "execute": execute,
            "membership": membership.models,
            "quiz": quiz.models,
            "select": select,
        }

        print(f"Welcome!")
        print(f"")
        print(f"Things available:")
        for k in sorted(namespace.keys()):
            print(f"   {k}")
        print(f"")
        print(
            f"Now do something, for example: execute(select(membership.Group.name, membership.Group.num_members)).all()"
        )
        print(f"")

        start_ipython(argv=[], user_ns=namespace)
