import os
import pytest

from export.documentation_exporter import DocumentationExporter


@pytest.fixture
def temp_doc_file(tmp_path):
    return tmp_path / "temp_doc.json"

def test_load_and_save_documentation(temp_doc_file):
    manager = DocumentationExporter(doc_file=str(temp_doc_file))

    doc = manager.get_documentation()
    assert isinstance(doc, dict)
    assert "tables" in doc

    manager.documentation['tables']['test'] = {"description": "test", "remarks": ""}
    manager.save_documentation()

    # Recharger pour vérifier la sauvegarde
    new_manager = DocumentationExporter(doc_file=str(temp_doc_file))
    new_doc = new_manager.get_documentation()
    assert "test" in new_doc['tables']

def test_update_or_remove(temp_doc_file):
    manager = DocumentationExporter(doc_file=str(temp_doc_file))

    fake_schema = {
        'tables': {
            'new_table': {
                'columns': {
                    'col1': {'type': 'INT', 'nullable': False, 'default': None, 'comment': '', 'is_virtual': False}
                },
                'primary_key': ['col1'],
                'indexes': [],
                'foreign_keys': [],
                'checks': [],
                'virtual_foreign_keys': []
            }
        },
        'procedures': {},
        'functions': {},
        'triggers': {}
    }

    manager.update_or_remove(fake_schema, 'tables')
    assert "new_table" in manager.documentation['tables']
