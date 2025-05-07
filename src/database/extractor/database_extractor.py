from database.connection import DatabaseConnection
from database.factory import DatabaseExtractorFactory

class DatabaseExtractor:
    def __init__(self, db_type, host, port, user=None, password=None, databases=None, use_windows_auth=False):
        self.connection = DatabaseConnection(
            db_type, host, port, user, password, None, use_windows_auth
        )
        self.database = None
        self.db_type = db_type
        self.databases = databases

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
