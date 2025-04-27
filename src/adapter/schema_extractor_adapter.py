from abc import ABC, abstractmethod

class SchemaExtractorAdapter(ABC):
    def __init__(self, connection):
        self.connection = connection


    @abstractmethod
    def extract_schema(self, file_exporter=None) -> dict:
        pass

    @abstractmethod
    def list_databases(self) -> list | None:
        pass
