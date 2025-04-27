from database.connection import DatabaseConnection
from database.extractor.mssql_extractor import MSSQLSchemaExtractor
from database.extractor.mysql_extractor import MySQLSchemaExtractor

class DatabaseExtractorFactory:
    @staticmethod
    def create_extractor(db_type, connection):
        if db_type == 'mysql' or db_type == 'mariadb':
            return MySQLSchemaExtractor(connection)
        elif db_type == 'mssql':
            return MSSQLSchemaExtractor(connection)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

