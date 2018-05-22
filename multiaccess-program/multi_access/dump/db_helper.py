
DB_NAME = 'mssql://(local)\\SQLEXPRESS/MultiAccess?trusted_connection=yes&driver=SQL+Server'


def create_default_engine(db_name=None):
    db_name = db_name or DB_NAME
    import sqlalchemy
    db = sqlalchemy.create_engine(db_name)
    return db
