class SchemaUpdater:
    def __init__(self, documentation):
        self.documentation = documentation

    def update_or_remove(self, schema, schema_type):
        """
        Update or remove tables, procedures, functions, or triggers in the documentation.
        """

        if not self.documentation:
            self.documentation = {
                'tables': {},
                'views': {},
                'procedures': {},
                'functions': {},
                'triggers': {}
            }

        for key in ['tables', 'views', 'procedures', 'functions', 'triggers']:
            if schema_type == key:
                current_items = set(schema[key].keys())
                doc_items = set(self.documentation[key].keys())

                for item in doc_items - current_items:
                    del self.documentation[key][item]

                for item_name, item_data in schema[key].items():
                    if item_name not in self.documentation[key]:
                        self.documentation[key][item_name] = {'description': '', 'remarks': ''}
                        if key == 'tables' or key == 'views':
                            self.documentation[key][item_name]['columns'] = {}

                    if key == 'tables' or key == 'views':
                        for column_name, column_data in item_data['columns'].items():
                            if column_name not in self.documentation[key][item_name]['columns']:
                                self.documentation[key][item_name]['columns'][column_name] = {'description': '', 'remarks': ''}
