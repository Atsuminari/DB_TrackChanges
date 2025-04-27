import os

class FileExporter:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def change_base_dir(self, new_base_dir):
        self.base_dir = new_base_dir
        os.makedirs(new_base_dir, exist_ok=True)

    def save_sql(self, subdir, name, content):
        safe_name = name.replace('`', '').replace('/', '_')
        folder_path = os.path.join(self.base_dir, subdir)
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f"{safe_name}.sql")

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return os.path.relpath(file_path, self.base_dir)
