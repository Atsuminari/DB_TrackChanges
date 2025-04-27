from handler.file_handler import FileHandler
from utils.schema_updater import SchemaUpdater


class DocumentationExporter:
    def __init__(self, doc_file):
        self.file_handler = FileHandler(doc_file)
        self.documentation = self.file_handler.load()
        self.schema_updater = SchemaUpdater(self.documentation)

    def save_documentation(self):
        """
        Save the documentation to the JSON file.
        """
        self.file_handler.save(self.documentation)

    def update_or_remove(self, schema, schema_type):
        """
        Update or remove tables, procedures, functions, or triggers in the documentation.
        """
        self.schema_updater.update_or_remove(schema, schema_type)
        self.documentation = self.schema_updater.documentation

    def get_documentation(self):
        """
        Return the current documentation.
        """
        return self.documentation
