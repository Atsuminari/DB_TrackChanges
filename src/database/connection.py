import urllib

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
# noinspection PyUnresolvedReferences
import pyodbc

class DatabaseConnection:
    def __init__(self, db_type, host, port, user=None, password=None, database=None, use_windows_auth=False):
        self.db_type = db_type
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.use_windows_auth = use_windows_auth
        self.engine = None


    def create_engine(self, database_name=None) -> Engine:
        database_name = database_name or self.database

        if self.db_type in ('mysql', 'mariadb'):
            url = f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{database_name or ''}"

        elif self.db_type == 'mssql':
            databaseSetting = f"Database={database_name};" if database_name else ""
            base_conn_str = f"Driver=ODBC Driver 18 for SQL Server;Server={self.host},{self.port};{databaseSetting}"
            auth_part = ""

            if not self.use_windows_auth:
                auth_part = f"UID={self.user};PWD={self.password};"
            else:
                auth_part = f"Trusted_Connection=yes;"

            params = urllib.parse.quote_plus(
                base_conn_str + auth_part + "TrustServerCertificate=yes;"
            )

            url = "mssql+pyodbc:///?odbc_connect=%s" % params

        else:
            raise ValueError(f"Unsupported db_type: {self.db_type}")

        self.engine = create_engine(url)
        return self.engine
