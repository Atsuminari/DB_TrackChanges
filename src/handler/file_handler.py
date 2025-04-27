import json
import os

from utils.logger import Logger


class FileHandler:
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        """
        Load data from a JSON file. If file doesn't exist or is invalid, return an empty dict.
        """
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Reason why I dont delete it myself is because its a documentation file edited by the user
                # It would be bad if I deleted it without asking while the user as edited it and have no backup...
                Logger.Critical(f"Invalid JSON format in file: {self.file_path} - please correct it or delete it.")
                raise ValueError()
        else:
            return None

    def save(self, data):
        """
        Save data to a JSON file.
        """

        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)