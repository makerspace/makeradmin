
DB_NAME = 'mssql://(local)\\SQLEXPRESS/MultiAccess?trusted_connection=yes&driver=SQL+Server'


def create_default_engine():
    import sqlalchemy
    db = sqlalchemy.create_engine(DB_NAME)
    return db
