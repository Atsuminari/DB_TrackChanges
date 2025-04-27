import pytest
from unittest.mock import MagicMock, patch
from src.database.extractor.database_extractor import DatabaseExtractor



@pytest.fixture
def database_extractor():
    return DatabaseExtractor(
        db_type="mariadb",
        host="localhost",
        port=3306,
        user="user",
        password="password"
    )

@patch('src.database.connection.DatabaseConnection.create_engine')
@patch('src.database.factory.DatabaseExtractorFactory.create_extractor')
def test_list_databases(mock_create_extractor, mock_create_engine, database_extractor):
    # Arrange
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine

    mock_extractor = MagicMock()
    mock_extractor.list_databases.return_value = ['test_db1', 'test_db2']
    mock_create_extractor.return_value = mock_extractor

    # Act
    databases = database_extractor.list_databases()

    # Assert
    mock_create_engine.assert_called_once()
    mock_create_extractor.assert_called_once_with('mariadb', database_extractor.connection)
    assert databases == ['test_db1', 'test_db2']