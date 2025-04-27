from src.database.connection import DatabaseConnection
from src.database.factory import DatabaseExtractorFactory

class DatabaseExtractor:
    def __init__(self, db_type, host, port, user, password, databases=None):
        self.db_type = db_type
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.databases = databases
        self.virtual_foreign_keys = {}
        self.connection = DatabaseConnection(db_type, host, port, user, password)

    def list_databases(self):
        if self.databases:
            return self.databases

        self.connection.create_engine()
        extractor = DatabaseExtractorFactory.create_extractor(self.db_type, self.connection)

        return extractor.list_databases()

    def extract_schema(self, database=None, file_exporter=None) -> dict:
        self.connection.create_engine(database or None)
        extractor = DatabaseExtractorFactory.create_extractor(self.db_type, self.connection)

        return extractor.extract_schema(file_exporter, database)
