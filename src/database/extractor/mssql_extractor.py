from sqlalchemy import text, inspect
from adapter.schema_extractor_adapter import SchemaExtractorAdapter

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
                schema['tables'][table[0]] = self.__extract_table_details(conn, table[0])

                create_table_script = self.__generate_create_table_script(
                    table[0],
                    schema['tables'][table[0]]['columns'],
                    schema['tables'][table[0]]['primary_key'],
                    schema['tables'][table[0]]['foreign_keys'],
                    schema['tables'][table[0]]['checks']
                )

                if file_exporter:
                    file_exporter.save_sql('tables', table[0], create_table_script)


            # -------------------------------------------------------------
            # VIEWS
            # -------------------------------------------------------------

            views = conn.execute(text("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.VIEWS 
                WHERE TABLE_CATALOG = :db
            """), {"db": database}).fetchall()

            for view in views:
                name = view[0]
                schema['views'][name] = self.__extract_view_details(conn, name)

                if file_exporter:
                    ddl = self.__extract_ddl_details(conn, file_exporter, "VIEW", name)
                    schema["views"][name].update(ddl)


            # -------------------------------------------------------------
            # PROCEDURES
            # -------------------------------------------------------------

            procedures = conn.execute(text("""
                SELECT SPECIFIC_NAME 
                FROM INFORMATION_SCHEMA.ROUTINES 
                WHERE ROUTINE_TYPE = 'PROCEDURE' AND ROUTINE_CATALOG = :db
            """), {"db": database}).fetchall()

            for proc in procedures:
                name = proc[0]
                schema["procedures"][name] = self.__extract_ddl_details(conn, file_exporter, "PROCEDURE", name)


            # -------------------------------------------------------------
            # FUNCTIONS
            # -------------------------------------------------------------

            functions = conn.execute(text("""
                SELECT SPECIFIC_NAME 
                FROM INFORMATION_SCHEMA.ROUTINES 
                WHERE ROUTINE_TYPE = 'FUNCTION' AND ROUTINE_CATALOG = :db
            """), {"db": database}).fetchall()

            for func in functions:
                name = func[0]
                schema["functions"][name] = self.__extract_ddl_details(conn, file_exporter, "FUNCTION", name)


            # -------------------------------------------------------------
            # TRIGGERS
            # -------------------------------------------------------------

            triggers = conn.execute(text("""
                SELECT name, parent_id, type_desc 
                FROM sys.triggers 
                WHERE parent_id != 0
            """)).fetchall()

            for trigger in triggers:
                name = trigger[0]

                trigger_def = conn.execute(text(f"""
                    SELECT OBJECT_DEFINITION (OBJECT_ID(:name)) AS trigger_definition
                """), {"name": name}).scalar()

                schema['triggers'][name] = {
                    'table_id': trigger[1],
                    'type': trigger[2],
                }

                if file_exporter:
                    sql_path = file_exporter.save_sql('triggers', name, trigger_def)
                    schema['triggers'][name]['definition_file'] = sql_path
                else:
                    schema['triggers'][name]['definition'] = str(trigger_def)

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
            'virtual_foreign_keys': []  # Not really a concept in MSSQL, keep empty
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
        Extract the DDL of a view, procedure or function.
        """
        schema = {}

        ddl = conn.execute(text(f"""
            SELECT OBJECT_DEFINITION (OBJECT_ID(:name)) AS object_definition
        """), {"name": object_name}).scalar()

        if ddl:
            if file_exporter:
                sql_path = file_exporter.save_sql(f"{object_type.lower()}s", object_name, ddl.replace("\r", ""))
                schema = {'definition_file': sql_path}
            else:
                schema = {'definition': str(ddl)}

        return schema

    def __generate_create_table_script(self, table_name, columns, primary_key, foreign_keys, checks):
        """
        Generate the CREATE TABLE script for MSSQL.
        """
        script = f"CREATE TABLE [{table_name}] (\n"

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

        script += "\n);"

        return script

    def list_databases(self):
        """
        List all databases in the MSSQL server.
        :return: List of database names
        """
        with self.connection.engine.connect() as conn:
            databases = conn.execute(text("SELECT name FROM sys.databases")).fetchall()
            return [db[0] for db in databases]
