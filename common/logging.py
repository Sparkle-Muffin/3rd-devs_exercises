import json
from pathlib import Path
from typing import Any

try:
    from pydantic import BaseModel
except ImportError:  # pragma: no cover
    BaseModel = None  # type: ignore


class Logging:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _serialize_message(self, message: Any):
        if BaseModel and isinstance(message, BaseModel):
            return message.model_dump()
        if hasattr(message, "model_dump"):
            try:
                return message.model_dump()
            except TypeError:
                pass
        if hasattr(message, "dict"):
            try:
                return message.dict()
            except TypeError:
                pass
        if isinstance(message, dict):
            return {key: self._serialize_message(value) for key, value in message.items()}
        if isinstance(message, (list, tuple, set)):
            return [self._serialize_message(value) for value in message]
        if isinstance(message, (str, int, float, bool)) or message is None:
            return message
        return str(message)

    def _get_next_file_number(self, directory):
        """Determine the next file number based on existing files."""
        files = list(directory.glob("*.txt")) + list(directory.glob("*.json"))
        return len(files) + 1

    def log(self, message, format="json"):
        serialized_message = self._serialize_message(message)
        file_number = self._get_next_file_number(self.directory)
        file_path = self.directory / f"log_{file_number}.{format}"
        with open(file_path, "a") as f:
            if format == "json":
                f.write(json.dumps(serialized_message, ensure_ascii=False) + "\n")
            elif format == "txt":
                f.write(str(serialized_message) + "\n")