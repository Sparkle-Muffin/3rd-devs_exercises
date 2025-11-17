import json
from pathlib import Path


class Logging:
    def __init__(self, directory):
        self.directory = Path(directory)

    def _get_next_file_number(self, directory):
        """Determine the next file number based on existing files."""
        files = list(directory.glob("*.txt")) + list(directory.glob("*.json"))
        return len(files) + 1

    def log(self, message, format="json"):
        file_number = self._get_next_file_number(self.directory)
        file_path = self.directory / f"log_{file_number}.{format}"
        with open(file_path, "a") as f:
            if format == "json":
                f.write(json.dumps(message) + "\n")
            elif format == "txt":
                f.write(message + "\n")