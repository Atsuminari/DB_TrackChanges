import argparse
import os
import json

import pyodbc
from constants.constants import SUPPORTED_SGBD, SYSTEM_TABLE_SGBD, DEFAULT_PORT
from core import Core


class input_listener:
    def __init__(self):
        self.args = self.parse_arguments()

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Export DB schema to JSON for git versionning.")
        parser.add_argument('--db_type', '-t', '--type', type=str, required=True, help=f"Database type (supported SGBD: {', '.join(SUPPORTED_SGBD)})")
        parser.add_argument('--host', '-i', type=str, required=True, default="127.0.0.1", help="Database host")
        parser.add_argument('--port', type=int, required=False, help="Database port")
        parser.add_argument('--user', '-u', type=str, required=False, help="Database user")
        parser.add_argument('--password', '-p', type=str, required=False, help="Database password")
        parser.add_argument('--output', '-o', type=str, required=False, default="./", help="Output directory")
        parser.add_argument('--restriction_list', '-r', type=str, required=False, help="Path to JSON file containing a list of restricted databases or tables to exclude.")
        parser.add_argument('--exclude_system_databases', '-e', type=bool, required=False, default=True, help="Exclude system databases like 'sys' or 'master' (default: True)")
        parser.add_argument('--databases', '-d', type=str, nargs='*', required=False, help="List of databases to export. (default: all databases)")

        args = parser.parse_args()
        return args

    def load_restriction_list(self):
        restriction_list = []
        if self.args.restriction_list and os.path.exists(self.args.restriction_list):
            try:
                with open(self.args.restriction_list, 'r', encoding='utf-8') as f:
                    restriction_list = json.load(f)

                    if not isinstance(restriction_list, list):
                        raise ValueError("The restriction list must be a JSON array.")

            except FileNotFoundError:
                raise FileNotFoundError(f"Restriction list file not found: {self.args.restriction_list}")

            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON format in {self.args.restriction_list}")

            except ValueError as e:
                raise ValueError(f"Error in restriction list: {e}")

        return restriction_list

    def run(self):
        db_type = self.args.db_type
        host = self.args.host
        port = self.args.port
        user = self.args.user
        password = self.args.password
        output = self.args.output
        databases = self.args.databases
        restriction_list = self.load_restriction_list()
        exclude_system_databases = self.args.exclude_system_databases

        #Check if ODBC Driver 18 for SQL Server
        if db_type == 'mssql':
            driver = pyodbc.drivers()
            if "ODBC Driver 18 for SQL Server" not in driver:
                raise ValueError("No ODBC SQL Server driver found. Please install 'ODBC Driver 18 for SQL Server'.")

        if db_type == 'mssql':
            if "ODBC Driver 18 for SQL Server" not in driver:
                raise ValueError("No ODBC SQL Server driver found. Please install 'ODBC Driver 18 for SQL Server'.")



    # Fallback logic for Windows Auth if user/pass not provided
        if not user and not password:
            if db_type == 'mssql':
                use_windows_auth = True
            else:
                raise ValueError("Missing credentials: user and password are required for non-MSSQL databases.")
        else:
            use_windows_auth = False

        if db_type not in SUPPORTED_SGBD:
            raise ValueError(f"Unsupported database type: {db_type}. Supported types are: {', '.join(SUPPORTED_SGBD)}")

        if not port:
            port = DEFAULT_PORT.get(db_type)

        if not port:
            raise ValueError(f"Port not specified and no default port available for {db_type}.")

        system_tables = SYSTEM_TABLE_SGBD[db_type]

        if not os.path.exists(output):
            os.makedirs(output)

        if restriction_list and not isinstance(restriction_list, list):
            raise ValueError("The restriction list must be a JSON array.")

        if restriction_list and not all(isinstance(item, str) for item in restriction_list):
            raise ValueError("All items in the restriction list must be strings.")

        if restriction_list and db_type in SUPPORTED_SGBD:
            if any(item in system_tables for item in restriction_list):
                raise ValueError(f"The restriction list contains system tables: {', '.join(system_tables)}. Please remove them.")

        extractor = Core(
            db_type=db_type,
            host=host,
            port=int(port),
            user=user,
            password=password,
            databases=databases,
            output=output,
            system_tables=system_tables,
            restriction_list=restriction_list,
            exclude_system_databases=exclude_system_databases,
            use_windows_auth=use_windows_auth
        )

        extractor.run()
