# DB_TrackChanges

DB_TrackChanges is an open-source tool that helps you automatically document your database schema and track changes in a Git repository. It is designed to be simple to use, and it helps developers keep track of changes to their database schema over time.

## Features
- Automatically extract database schema. (Currently support MySQL, MariaDB, SQL Server)
- Generate SQL scripts for creating tables, views, procedures, and other database objects.
- Save schema in a JSON format that’s easy to version with Git.
- Generate comprehensive documentation of the database structure.

## Installation

### Prerequisites
- Python 3.6 or higher
- Required libraries: `sqlalchemy`, `pyodbc`, `pymysql`, etc. (see `requirements.txt` for the full list)

### Clone the project

```bash
git clone https://github.com/Atsuminari/DB_TrackChanges.git
cd DB_TrackChanges

pip install -r requirements.txt
```

## Usage

This program is CLI-based and can be run from the command line.

```cmd
> DB_TrackChanges_1.1.0.exe --help 

Export DB schema to JSON.

options:
  -h, --help            show this help message and exit
  --db_type DB_TYPE     Database type (supported SGBD: mssql, mariadb, mysql)
  --host HOST           Database host
  --port PORT           Database port
  --user USER           Database user
  --password PASSWORD   Database password
  --output OUTPUT       Output directory
  --restriction_list RESTRICTION_LIST
                        Path to JSON file containing a list of restricted databases or tables to exclude.
  --exclude_system_databases EXCLUDE_SYSTEM_DATABASES
                        Exclude system databases like 'sys' or 'master' (default: True)
  --databases [DATABASES ...]
                        List of databases to export. (default: all databases)
```

### Example

```bash
DB_TrackChanges_1.1.0.exe --db_type mssql --host 127.0.0.1 --port 1433 --user sa --password "Strong!Passw0rd" --output ./export
```

This script will extract the schema from your database and save it in the specified output directory.

## Contributing

We encourage contributions! To get started:

    Fork the repository

    Create a new branch (git checkout -b feature/my-new-feature)

    Make your changes and commit them (git commit -am 'Added a feature')

    Push your branch (git push origin feature/my-new-feature)

    Open a Pull Request

Please review the Code of Conduct before contributing.

## License
This project is licensed under the MIT License - see the LICENSE file for more details.
