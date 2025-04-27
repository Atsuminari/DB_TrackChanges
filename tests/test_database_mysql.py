import pytest
from unittest.mock import MagicMock, patch
from src.database.extractor.mysql_extractor import MySQLSchemaExtractor

@pytest.fixture
def fake_connection():
    conn = MagicMock()
    conn.engine.connect.return_value.__enter__.return_value = conn
    return conn

from unittest.mock import MagicMock, patch

def test_extract_schema(fake_connection):
    # Arrange
    extractor = MySQLSchemaExtractor(fake_connection)

    # Mock execute calls
    mock_execute = MagicMock()
    mock_execute.fetchall.side_effect = [
        [('table1',)],  # Pour tables
        [('view1',)]    # Pour views
    ]

    fake_connection.engine.connect.return_value.__enter__.return_value.execute.return_value = mock_execute

    # Mock inspector
    with patch('src.database.extractor.mysql_extractor.inspect') as mock_inspect:
        mock_inspector = MagicMock()
        mock_inspector.get_columns.return_value = [{'name': 'id', 'type': 'INT', 'nullable': False}]
        mock_inspector.get_pk_constraint.return_value = {'constrained_columns': ['id']}
        mock_inspector.get_indexes.return_value = []
        mock_inspector.get_foreign_keys.return_value = []
        mock_inspector.get_check_constraints.return_value = []
        mock_inspect.return_value = mock_inspector

        # Act
        schema = extractor.extract_schema(database='testdb')

        # Assert
        assert 'tables' in schema
