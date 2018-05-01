import sqlalchemy
from multi_access.dump import db_info
from multi_access.dump import db_helper
import pickle
import json
from datetime import date, datetime


def table(db, table_name):
    """ Get all rows of a table. """
    assert isinstance(db, sqlalchemy.engine.base.Engine)
    assert isinstance(table_name, str)
    with db.connect() as connection:
        sql_statement = sqlalchemy.text(f"SELECT * from {table_name}")
        res = connection.execute(sql_statement)
        rows = list(res.cursor)
        table_info = {
            "rows": rows,
            "columns": db_info.get_column_names(db, table_name)
        }
        return table_info


def tables(db):
    """ Get all rows of all tables in the database """
    assert isinstance(db, sqlalchemy.engine.base.Engine)
    table_names = db_info.get_table_names(db)
    return {table_name: table(db, table_name) for table_name in table_names}


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


def to_file(filename):
    assert isinstance(filename, str)
    extension = filename.split(".")[-1]
    table_dump = tables(db_helper.create_default_engine())
    if extension == "pkl":
        with open(filename, "wb") as f:
            pickle.dump(table_dump, file=f)
    elif extension == "json":
        with open(filename, "w", encoding="utf8") as f:
            json.dump(table_dump, fp=f, default=json_serial)
    else:
        raise ValueError(f"The file extension '.{extension}' is not valid. Use '.pkl' or '.json'")
    