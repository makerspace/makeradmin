import sqlalchemy
from src import db_info
from src import db_helper
import pickle, json

def table(db, table_name):
    '''
    Get all rows of a table
    '''
    assert isinstance(db, sqlalchemy.engine.base.Engine)
    assert isinstance(table_name, str)
    with db.connect() as connection:
        sql_statement = sqlalchemy.text(f"SELECT * from {table_name}")
        res = connection.execute(sql_statement)
        rows = [d for d in res.fetchall()]
        table_info = {
            "result": res,
            "rows": rows,
            "columns": db_info.get_column_names(db, table_name)
        }
        return table_info

def tables(db):
    '''
    Get all rows of all tables in the database
    '''
    assert isinstance(db, sqlalchemy.engine.base.Engine)
    table_names = db_info.get_table_names(db)
    table_dumps = {}
    for table_name in table_names:
        table_dump = table(db, table_name)
        table_dumps[table_name] = table_dump
    return table_dumps

def dump_tables(filename, out_format="pickle"):
    assert isinstance(filename, str)
    assert isinstance(out_format, str)
    out_format = out_format.lower()
    if out_format not in ("pickle", "json"): raise ValueError()
    table_dump = tables(db_helper.create_default_engine())
    if out_format is "pickle":
        pickle.dump(table_dump, filename)
    elif out_format is "json":
        with open(filename, "w") as f:
            json.dump(table_dump, fp=f)