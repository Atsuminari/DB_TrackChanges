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

To start using DB_TrackChanges, configure your database connection, for example:

```python

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
