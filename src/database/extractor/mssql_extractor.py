import re

from sqlalchemy import text, inspect
from src.adapter.schema_extractor_adapter import SchemaExtractorAdapter
from sqlalchemy.exc import DBAPIError


class MSSQLSchemaExtractor(SchemaExtractorAdapter):

    def extract_schema(self, file_exporter=None, database=None) -> dict:
        """
        Extract the schema of the database including tables, views, procedures, functions, and triggers.
        :param file_exporter: File exporter to save the SQL files
        :param database: Name of the current database
        :return: JSON schema with the database structure
        """
        schema = {'tables': {}, 'views': {}, 'procedures': {}, 'functions': {}, 'triggers': {}}

        with self.connection.engine.connect() as conn:
            # -------------------------------------------------------------
            # TABLES
            # -------------------------------------------------------------

            tables = conn.execute(text("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_CATALOG = :db
            """), {"db": database}).fetchall()

            for table in tables:
                try:
                    schema['tables'][table[0]] = self.__extract_table_details(conn, table[0])

                    create_table_script = self.__generate_create_table_script(
                        conn,
                        table[0],
                        schema['tables'][table[0]]['columns'],
                        schema['tables'][table[0]]['primary_key'],
                        schema['tables'][table[0]]['foreign_keys'],
                        schema['tables'][table[0]]['checks']
                    )

                    if file_exporter:
                        file_exporter.save_sql('tables', table[0], create_table_script)
                except DBAPIError:
                    schema['tables'][table[0]] = {'error': 'Insufficient privileges to access table'}
                except:
                    continue


            # -------------------------------------------------------------
            # VIEWS
            # -------------------------------------------------------------

            try:
                views = conn.execute(text("""
                    SELECT TABLE_NAME 
                    FROM INFORMATION_SCHEMA.VIEWS 
                    WHERE TABLE_CATALOG = :db
                """), {"db": database}).fetchall()

                for view in views:
                    name = view[0]
                    try:
                        schema['views'][name] = self.__extract_view_details(conn, name)

                        if file_exporter:
                            ddl = self.__extract_ddl_details(conn, file_exporter, "VIEW", name)
                            schema["views"][name].update(ddl)
                    except DBAPIError:
                        schema['views'][name] = {'error': 'Insufficient privileges to access view'}
                    except:
                        continue

            except DBAPIError:
                schema['views'] = {'error': 'Insufficient privileges to access views'}


            # -------------------------------------------------------------
            # PROCEDURES
            # -------------------------------------------------------------

            try:
                procedures = conn.execute(text("""
                    SELECT SPECIFIC_NAME 
                    FROM INFORMATION_SCHEMA.ROUTINES 
                    WHERE ROUTINE_TYPE = 'PROCEDURE' AND ROUTINE_CATALOG = :db
                """), {"db": database}).fetchall()

                for proc in procedures:
                    name = proc[0]
                    try:
                        schema["procedures"][name] = self.__extract_ddl_details(conn, file_exporter, "PROCEDURE", name)
                    except DBAPIError:
                        schema["procedures"][name] = {'error': 'Insufficient privileges'}
                    except:
                        continue

            except DBAPIError:
                schema["procedures"] = {'error': 'Insufficient privileges to list procedures'}

            # -------------------------------------------------------------
            # FUNCTIONS
            # -------------------------------------------------------------

            try:
                functions = conn.execute(text("""
                    SELECT SPECIFIC_NAME 
                    FROM INFORMATION_SCHEMA.ROUTINES 
                    WHERE ROUTINE_TYPE = 'FUNCTION' AND ROUTINE_CATALOG = :db
                """), {"db": database}).fetchall()

                for func in functions:
                    name = func[0]
                    try:
                        schema["functions"][name] = self.__extract_ddl_details(conn, file_exporter, "FUNCTION", name)
                    except DBAPIError:
                        schema["functions"][name] = {'error': 'Insufficient privileges'}
                    except:
                        continue

            except DBAPIError:
                schema["functions"] = {'error': 'Insufficient privileges to list functions'}

            # -------------------------------------------------------------
            # TRIGGERS
            # -------------------------------------------------------------

            try:
                triggers = conn.execute(text("""
                    SELECT name, parent_id, type_desc 
                    FROM sys.triggers 
                    WHERE parent_id != 0
                """)).fetchall()

                for trigger in triggers:
                    name = trigger[0]
                    try:
                        schema["triggers"][name] = self.__extract_ddl_details(conn, file_exporter, "TRIGGER", name)
                    except DBAPIError:
                        schema["triggers"][name] = {'error': 'Insufficient privileges'}
                    except:
                        continue

            except DBAPIError:
                schema["triggers"] = {'error': 'Insufficient privileges to list triggers'}

        return schema

    def __extract_table_details(self, conn, table_name):
        """
        Extract the details of a table including columns, primary keys, indexes, foreign keys, and checks.
        """
        inspector = inspect(conn)

        columns = inspector.get_columns(table_name)
        pk_constraint = inspector.get_pk_constraint(table_name)
        indexes = inspector.get_indexes(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)

        checks = []

        # MSSQL-specific query to fetch CHECK constraints
        check_constraints_query = text("""
            SELECT cc.name AS constraint_name, cc.definition
            FROM sys.check_constraints cc
            INNER JOIN sys.objects o ON cc.parent_object_id = o.object_id
            WHERE o.name = :table_name
        """)
        result = conn.execute(check_constraints_query, {"table_name": table_name}).mappings()

        for row in result:
            checks.append({
                'name': row['constraint_name'],
                'sqltext': row['definition']
            })

        schema = {
            'comment': '',
            'columns': {},
            'primary_key': pk_constraint.get('constrained_columns', []),
            'indexes': [],
            'foreign_keys': [],
            'checks': [],
        }

        for column in columns:
            default_value = column.get('default', None)

            schema['columns'][column['name']] = {
                'type': str(column['type']),
                'nullable': column['nullable'],
                'default': "NULL" if default_value and default_value == "(NULL)" else default_value,
                'comment': column.get('comment', ''),
                'is_virtual': False  # MSSQL does not have virtual columns
            }

        for index in indexes:
            schema['indexes'].append({
                'name': index['name'],
                'columns': index['column_names']
            })

        for fk in foreign_keys:
            schema['foreign_keys'].append({
                'name': fk.get('name'),
                'columns': fk['constrained_columns'],
                'referred_table': fk['referred_table'],
                'referred_columns': fk['referred_columns']
            })

        for check in checks:
            schema['checks'].append({
                'name': check.get('name'),
                'sqltext': check.get('sqltext')
            })

        return schema

    def __extract_view_details(self, conn, view_name):
        """
        Extract the details of a view including columns.
        """
        inspector = inspect(conn)
        columns = inspector.get_columns(view_name)

        schema = {
            'comment': '',
            'columns': {},
        }

        for column in columns:
            schema['columns'][column['name']] = {
                'type': str(column['type'])
            }

        return schema

    def __extract_ddl_details(self, conn, file_exporter, object_type, object_name):
        """
        Extract the DDL of a view, procedure, function or trigger.
        """
        schema = {}

        ddl = conn.execute(text(f"""
            SELECT OBJECT_DEFINITION (OBJECT_ID(:name)) AS object_definition
        """), {"name": object_name}).scalar()

        if ddl:
            ddl = ddl.replace("\r", "")
            pattern = r"""((?:/\*.*?\*/|--[^\n]*|[^C/\\-]+|[C/\\-](?!REATE|[*-]))*?)\bCREATE\b"""
            ddl = re.sub(pattern, r"\1CREATE OR ALTER", ddl, count=1, flags=re.IGNORECASE | re.DOTALL | re.VERBOSE)

            if file_exporter:
                sql_path = file_exporter.save_sql(f"{object_type.lower()}s", object_name, ddl)
                schema = {'definition_file': sql_path}
            else:
                schema = {'definition': str(ddl)}

        return schema


    def __generate_create_table_script(self, conn, table_name, columns, primary_key, foreign_keys, checks):
        """
        Generate the CREATE TABLE script for MSSQL.
        """
        script = f"CREATE OR ALTER TABLE [{table_name}] (\n"

        # Column definitions
        column_definitions = []
        for column_name, column_data in columns.items():
            col_def = f"    [{column_name}] {column_data['type']}"

            if not column_data['nullable']:
                col_def += " NOT NULL"

            if column_data['default']:
                col_def += f" DEFAULT {column_data['default']}"

            column_definitions.append(col_def)

        script += ",\n".join(column_definitions)

        if primary_key:
            script += f",\n    PRIMARY KEY ({', '.join(primary_key)})"

        for fk in foreign_keys:
            script += f",\n    CONSTRAINT [{fk['name']}] FOREIGN KEY ({', '.join(fk['columns'])}) REFERENCES [{fk['referred_table']}] ({', '.join(fk['referred_columns'])})"

        for check in checks:
            script += f",\n    CONSTRAINT [{check['name']}] CHECK ({check['sqltext']})"

        script += "\n);\n"

        # Ajouter les CREATE INDEX
        for index in self.__get_table_indexes_mssql(conn, table_name):
            cols = ', '.join(index['columns'])
            script += f"\nCREATE INDEX [{index['name']}] ON [{table_name}] ({cols});"

        return script

    def __get_table_indexes_mssql(self, conn, table_name):
        """
        Custom method to retrieve indexes for a table in MSSQL.
        """
        indexes_query = text("""
            SELECT 
                i.name AS index_name,
                c.name AS column_name,
                i.is_unique
            FROM 
                sys.indexes i
            INNER JOIN 
                sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            INNER JOIN 
                sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            INNER JOIN 
                sys.tables t ON i.object_id = t.object_id
            WHERE 
                t.name = :table_name
                AND i.is_primary_key = 0 -- exclude primary key
                AND i.type_desc <> 'HEAP'
            ORDER BY 
                i.name, ic.key_ordinal
        """)

        result = conn.execute(indexes_query, {"table_name": table_name}).fetchall()

        indexes = {}
        for row in result:
            index_name = row[0]
            column_name = row[1]
            is_unique = row[2]

            if index_name not in indexes:
                indexes[index_name] = {
                    "name": index_name,
                    "columns": [],
                    "is_unique": is_unique
                }

            indexes[index_name]["columns"].append(column_name)

        return list(indexes.values())


    def list_databases(self):
        """
        List only the databases the current user has access to.
        :return: List of accessible database names
        """
        with self.connection.engine.connect() as conn:
            databases = conn.execute(text("""
                SELECT name 
                FROM sys.databases 
                WHERE HAS_DBACCESS(name) = 1
            """)).fetchall()
            return [db[0] for db in databases]

        with self.connection.engine.connect() as conn:
            databases = conn.execute(text("SELECT name FROM sys.databases")).fetchall()
            return [db[0] for db in databases]
