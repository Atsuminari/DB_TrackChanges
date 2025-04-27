from sqlalchemy import text, inspect
from adapter.schema_extractor_adapter import SchemaExtractorAdapter


class MySQLSchemaExtractor(SchemaExtractorAdapter):
    def extract_schema(self, file_exporter=None, database=None) -> dict:
        """
        Extract the schema of the database including tables, procedures, functions, and triggers.
        :param file_exporter: File exporter to save the SQL files
        :param database: Name of the current database
        :return: JSON schema with the database structure
        """
        schema = {'tables': {}, 'views': {}, 'procedures': {}, 'functions': {}, 'triggers': {}}

        with self.connection.engine.connect() as conn:
            # -------------------------------------------------------------
            # TABLES
            # -------------------------------------------------------------

            tables = conn.execute(text("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")).fetchall()

            for table in tables:
                schema['tables'][table[0]] = self.__extract_table_details(conn, table[0], database)

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

            views = conn.execute(text("SHOW FULL TABLES WHERE Table_type = 'VIEW'")).fetchall()
            for view in views:
                name = view[0]
                schema["views"] = self.__extract_ddl_details(conn, file_exporter, "View", name)
                schema['views'][view[0]] = self.__extract_view_details(conn, view[0])


            # -------------------------------------------------------------
            # PROCEDURES
            # -------------------------------------------------------------

            procedures = conn.execute(text("SHOW PROCEDURE STATUS WHERE Db = :db"), {"db": database}).mappings()

            for proc in procedures:
                name = proc['Name']
                schema["procedures"] = self.__extract_ddl_details(conn, file_exporter, "Procedure", name)


            # -------------------------------------------------------------
            # FUNCTIONS
            # -------------------------------------------------------------

            functions = conn.execute(text("SHOW FUNCTION STATUS WHERE Db = :db"), {"db": database}).mappings()

            for func in functions:
                name = func['Name']
                schema["functions"] = self.__extract_ddl_details(conn, file_exporter, "Function", name)


            # -------------------------------------------------------------
            # TRIGGERS
            # -------------------------------------------------------------

            triggers = conn.execute(text("SHOW TRIGGERS")).mappings()
            for trigger in triggers:
                name = trigger['Trigger']
                sql_content = trigger['Statement']

                schema['triggers'][name] = {
                    'table': trigger['Table'],
                    'timing': trigger['Timing'],
                    'event': trigger['Event']
                }

                if file_exporter:
                    sql_path = file_exporter.save_sql('triggers', name, sql_content)
                    schema['triggers'][name]['definition_file'] = sql_path
                else:
                    schema['triggers'][name]['definition'] = str(sql_content)

        return schema

    def __extract_table_details(self, conn, table_name, database=None):
        """
        Extract the details of a table including columns, primary keys, indexes, foreign keys, and checks.
        :param conn: Connection to the database
        :param table_name: Name of the table
        :return: JSON schema with the table details
        """
        inspector = inspect(conn)

        columns = inspector.get_columns(table_name)
        pk_constraint = inspector.get_pk_constraint(table_name)
        indexes = inspector.get_indexes(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        checks = inspector.get_check_constraints(table_name)

        schema = {
            'comment': '',
            'columns': {},
            'primary_key': pk_constraint.get('constrained_columns', []),
            'indexes': [],
            'foreign_keys': [],
            'checks': [],
            'virtual_foreign_keys': []
        }

        column_info_query = text(f"""
                            SELECT COLUMN_NAME, EXTRA
                            FROM INFORMATION_SCHEMA.COLUMNS
                            WHERE TABLE_SCHEMA = :db AND TABLE_NAME = :table
                        """);

        result = conn.execute(column_info_query, {"db": database, "table": table_name}).mappings()
        virtual_columns = {row['COLUMN_NAME'] for row in result if 'VIRTUAL' in row['EXTRA'].upper()}

        for column in columns:
            schema['columns'][column['name']] = {
                'type': str(column['type']),
                'nullable': column['nullable'],
                'default': column.get('default', None),
                'comment': column.get('comment', ''),
                'is_virtual': column['name'] in virtual_columns
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

    def __extract_view_details(self, conn, table_name):
        """
        Extract the details of a view including columns, primary keys, indexes, foreign keys, and checks.
        :param conn: Connection to the database
        :param table_name: Name of the table
        :return: JSON schema with the table details
        """
        inspector = inspect(conn)
        columns = inspector.get_columns(table_name)

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
        Extract the DDL details of a given object (procedure or function).
        :param conn: Connection to the database
        :param file_exporter: File exporter to save the SQL file
        :param object_type: Type of the object (Procedure or Function)
        :param object_name: Name of the object
        :return: JSON schema with the DDL details
        """
        schema = {}

        create_proc = conn.execute(text(f"SHOW CREATE {object_type.upper()} `{object_name}`")).mappings().first()
        if create_proc:
            sql_content = create_proc[f'Create {object_type}']
            if file_exporter:
                sql_path = file_exporter.save_sql(f"{object_type.lower()}s", object_name, sql_content.replace('\r', ''))
                schema[object_name] = {'definition_file': sql_path}
            else:
                schema[object_name] = {'definition': str(sql_content)}

        return schema

    def __generate_create_table_script(self, table_name, columns, primary_key, foreign_keys, checks):
        """
        Generate the CREATE TABLE script for a given table.
        """
        script = f"CREATE TABLE `{table_name}` (\n"

        # Column definitions
        column_definitions = []
        for column_name, column_data in columns.items():
            col_def = f"    `{column_name}` {column_data['type']}"

            if not column_data['nullable']:
                col_def += " NOT NULL"

            if column_data['default']:
                col_def += f" DEFAULT {column_data['default']}"

            if column_data['is_virtual']:
                col_def += " GENERATED ALWAYS AS (expression) VIRTUAL"

            if column_data['comment']:
                col_def += f" COMMENT '{column_data['comment']}'"

            column_definitions.append(col_def)

        script += ",\n".join(column_definitions)

        if primary_key:
            script += f",\n    PRIMARY KEY ({', '.join(primary_key)})"

        for fk in foreign_keys:
            script += f",\n    CONSTRAINT `{fk['name']}` FOREIGN KEY ({', '.join(fk['columns'])}) REFERENCES `{fk['referred_table']}` ({', '.join(fk['referred_columns'])})"

        for check in checks:
            script += f",\n    CONSTRAINT `{check['name']}` CHECK ({check['sqltext']})"

        script += "\n);"

        return script

    def list_databases(self):
        """
        List all databases in the MySQL server.
        :return: List of database names
        """

        with self.connection.engine.connect() as conn:
            databases = conn.execute(text("SHOW DATABASES")).fetchall()
            return [db[0] for db in databases]