import sqlalchemy

class PEP240(object):
    '''
    https://www.python.org/dev/peps/pep-0249/#cursor-attributes
    '''
    def __init__(self, dict_entry):
        assert isinstance(dict_entry, tuple)
        assert len(dict_entry) == 7
        self.name          = dict_entry[0]
        self.type_code     = dict_entry[1]
        self.display_size  = dict_entry[2]
        self.internal_size = dict_entry[3]
        self.precision     = dict_entry[4]
        self.scale         = dict_entry[5]
        self.null_ok       = dict_entry[6]

def _get_column_names(cursor):
    table_description = cursor.description
    column_names = []
    for column_description in table_description:
        column_description = PEP240(column_description)
        column_names.append(column_description.name)
    return column_names

def get_column_names(db, table_name):
    '''
    Get a list of all columns in a table
    '''
    assert isinstance(db, sqlalchemy.engine.base.Engine)
    assert isinstance(table_name, str)
    with db.connect() as conn:
        res = conn.execute(sqlalchemy.text(f"SELECT * FROM {table_name}"))
        return _get_column_names(res.cursor)
    raise IOError("Could not connect to database")

def get_table_names(db):
    '''
    Get a list of all *base* tables in the database (user created tables)
    '''
    assert isinstance(db, sqlalchemy.engine.base.Engine)
    with db.connect() as conn:
        res = conn.execute(sqlalchemy.text("SELECT * FROM information_schema.tables WHERE TABLE_TYPE = 'BASE TABLE'"))
        rows = res.fetchall()
        table_names = []
        for row in rows:
            table_names.append(row.TABLE_NAME)
        return table_names
    raise IOError("Could not connect to database")

def get_all_table_names(db):
    '''
    Get a list of all tables in the database (also event-tables and other database-managed tables)
    '''
    assert isinstance(db, sqlalchemy.engine.base.Engine)
    with db.connect() as conn:
        res = conn.execute(sqlalchemy.text("SELECT * FROM Users")) # Dummy execution to get a cursor object
        t = res.cursor.tables()
        rows = t.fetchall()
        table_names = []
        for row in rows:
            table_names.append(row.table_name)
        return table_names
    raise IOError("Could not connect to database")