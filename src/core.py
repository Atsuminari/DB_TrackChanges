import os

from database.extractor.database_extractor import DatabaseExtractor
from export.documentation_exporter import DocumentationExporter
from export.file_exporter import FileExporter
from handler.file_handler import FileHandler
from utils.logger import Logger
from utils.schema_updater import SchemaUpdater


class Core:
    def __init__(self, db_type, host, port, user, password, output, databases=None, system_tables=None, restriction_list=None, exclude_system_databases=True):
        self.db_type = db_type
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.outputDir = output
        self.databases = databases
        self.restriction_list = restriction_list if restriction_list else []

        if exclude_system_databases and system_tables:
            self.restriction_list.extend(system_tables)

    def run(self):
        file_exporter = FileExporter(self.outputDir)

        extractor = DatabaseExtractor(
            db_type=self.db_type,
            host=self.host,
            port=int(self.port),
            user=self.user,
            password=self.password,
            databases=self.databases
        )

        Logger.Info("Connecting to database server and extracting list of databases...")

        databases = extractor.list_databases()

        if not databases:
            raise ValueError("No databases found or unable to connect to the database server.")

        # Each database
        for db_name in databases:
            Logger.ProgressBar(databases.index(db_name), len(databases))

            if db_name in self.restriction_list:
                # Skip databases in the restriction list
                continue

            db_output_dir = os.path.join(self.outputDir, db_name)
            os.makedirs(db_output_dir, exist_ok=True)

            file_exporter.change_base_dir(db_output_dir)
            extractor.database = db_name

            schema = extractor.extract_schema(file_exporter=file_exporter, database=db_name)

            if not schema:
                continue

            self.__generate_documentation(schema, db_name, db_output_dir)
            self.__save(schema, db_name, db_output_dir)


    def __generate_documentation(self, schema, db_name, db_output_dir):
        try:
            doc_manager = DocumentationExporter(os.path.join(db_output_dir, f"Documentation.json"))

        except ValueError:
            # Invalid JSON file, let the user fix it, we continue with the extraction
            return

        doc_manager.update_or_remove(schema, 'tables')
        doc_manager.update_or_remove(schema, 'views')
        doc_manager.update_or_remove(schema, 'procedures')
        doc_manager.update_or_remove(schema, 'functions')
        doc_manager.update_or_remove(schema, 'triggers')
        doc_manager.save_documentation()

    def __save(self, schema, db_name, db_output_dir):
        serializer = FileHandler(os.path.join(db_output_dir, f"{db_name}_schema.json"))
        serializer.save(schema)
