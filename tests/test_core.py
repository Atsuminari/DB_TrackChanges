import os
import pytest
from unittest.mock import patch, MagicMock

from core import Core

@pytest.fixture
def core_instance(tmp_path):
    return Core(
        db_type="mssql",
        host="localhost",
        port=1433,
        user="sa",
        password="Strong!Passw0rd",
        output=str(tmp_path),
        databases=None,
        system_tables=["master", "tempdb"],
        exclude_system_databases=True
    )

@patch("core.FileExporter")
@patch("core.DatabaseExtractor")
@patch("core.Logger")
@patch("core.DocumentationExporter")
@patch("core.FileHandler")
def test_run_success(mock_filehandler, mock_docexporter, mock_logger, mock_dbextractor, mock_fileexporter, core_instance):
    # Mock database extractor behavior
    mock_extractor_instance = MagicMock()
    mock_extractor_instance.list_databases.return_value = ["testdb"]
    mock_extractor_instance.extract_schema.return_value = {"tables": {"table1": {}}}
    mock_dbextractor.return_value = mock_extractor_instance

    # Mock file exporter behavior
    mock_file_exporter_instance = MagicMock()
    mock_fileexporter.return_value = mock_file_exporter_instance

    # Mock documentation exporter
    mock_doc_exporter_instance = MagicMock()
    mock_docexporter.return_value = mock_doc_exporter_instance

    # Mock file handler
    mock_file_handler_instance = MagicMock()
    mock_filehandler.return_value = mock_file_handler_instance

    # Execute
    core_instance.run()

    # Assertions
    mock_dbextractor.assert_called_once()
    mock_extractor_instance.list_databases.assert_called_once()
    mock_extractor_instance.extract_schema.assert_called_once_with(
        file_exporter=mock_file_exporter_instance,
        database="testdb"
    )
    mock_docexporter.assert_called_once()
    mock_filehandler.assert_called_once()

@patch("core.FileExporter")
@patch("core.DatabaseExtractor")
@patch("core.Logger")
def test_run_no_databases(mock_logger, mock_dbextractor, mock_fileexporter, core_instance):
    # Mock database extractor behavior to return no databases
    mock_extractor_instance = MagicMock()
    mock_extractor_instance.list_databases.return_value = []
    mock_dbextractor.return_value = mock_extractor_instance

    with pytest.raises(ValueError, match="No databases found or unable to connect"):
        core_instance.run()

@patch("core.FileExporter")
@patch("core.DatabaseExtractor")
@patch("core.Logger")
def test_run_with_restricted_database(mock_logger, mock_dbextractor, mock_fileexporter, core_instance):
    # Mock database extractor returning a restricted database
    mock_extractor_instance = MagicMock()
    mock_extractor_instance.list_databases.return_value = ["master", "userdb"]
    mock_extractor_instance.extract_schema.return_value = {"tables": {"table1": {}}}
    mock_dbextractor.return_value = mock_extractor_instance

    mock_file_exporter_instance = MagicMock()
    mock_fileexporter.return_value = mock_file_exporter_instance

    # Patch the methods __generate_documentation and __save to track calls
    with patch.object(core_instance, "_Core__generate_documentation") as mock_doc, \
            patch.object(core_instance, "_Core__save") as mock_save:

        core_instance.run()

        # master should be skipped, only userdb processed
        mock_doc.assert_called_once_with(
            {"tables": {"table1": {}}}, "userdb", os.path.join(core_instance.outputDir, "userdb")
        )
        mock_save.assert_called_once_with(
            {"tables": {"table1": {}}}, "userdb", os.path.join(core_instance.outputDir, "userdb")
        )

@patch("core.DocumentationExporter")
def test_generate_documentation_invalid_json(mock_docexporter, core_instance, tmp_path):
    # Force DocumentationExporter to raise ValueError
    mock_docexporter.side_effect = ValueError("Invalid JSON")

    schema = {"tables": {"table1": {}}}
    db_name = "testdb"
    db_output_dir = tmp_path / db_name

    # Should not raise, just pass
    core_instance._Core__generate_documentation(schema, db_name, db_output_dir)

@patch("core.FileHandler")
def test_save_schema_success(mock_filehandler, core_instance, tmp_path):
    mock_file_handler_instance = MagicMock()
    mock_filehandler.return_value = mock_file_handler_instance

    schema = {"tables": {"table1": {}}}
    db_name = "testdb"
    db_output_dir = tmp_path / db_name

    core_instance._Core__save(schema, db_name, db_output_dir)

    mock_filehandler.assert_called_once_with(os.path.join(db_output_dir, f"{db_name}_schema.json"))
    mock_file_handler_instance.save.assert_called_once_with(schema)
