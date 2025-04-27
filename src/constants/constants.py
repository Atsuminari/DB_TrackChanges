
SUPPORTED_SGBD = ["mssql", "mariadb", "mysql"]

SYSTEM_TABLE_SGBD = {
    "mysql": ["sys", "mysql", "performance_schema", "information_schema"],
    "mariadb": ["sys", "mysql", "performance_schema", "information_schema"],
    "mssql": ["master", "tempdb", "model", "msdb"]
}