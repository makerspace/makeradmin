import sqlalchemy
from src import db_info
import pickle

def table(db, table_name):
    '''
    Get all rows of a table
    '''
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
    table_names = db_info.get_table_names(db)
    table_dumps = {}
    for table_name in table_names:
        table_dump = table(db, table_name)
        table_dumps[table_name] = table_dump
    return table_dumps

def dump_tables(filename, out_format="pickle"):
    if out_format not in ("pickle", "json"): raise ValueError()
    import src.db_helper as db_helper
    pickle.dump(tables(db_helper.create_default_engine()), filename)