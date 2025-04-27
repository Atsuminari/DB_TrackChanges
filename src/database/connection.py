import urllib

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

class DatabaseConnection:
    def __init__(self, db_type, host, port, user, password, database=None):
        self.db_type = db_type
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.engine = None

    def create_engine(self, database_name=None) -> Engine:
        database_name = database_name or self.database

        if self.db_type in ('mysql', 'mariadb'):
            url = f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{database_name if database_name else ''}"

        elif self.db_type == 'mssql':
            #https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver16
            databaseSetting = f"Database={database_name};" if database_name else ""
            params = urllib.parse.quote_plus(f'Driver={{ODBC Driver 18 for SQL Server}};Server={self.host},{self.port};{databaseSetting}UID={self.user};PWD={self.password};TrustServerCertificate=yes;')
            url = "mssql+pyodbc:///?odbc_connect=%s" % params

        else:
            raise ValueError(f"Unsupported db_type: {self.db_type}")

        self.engine = create_engine(url)
        return self.engine
