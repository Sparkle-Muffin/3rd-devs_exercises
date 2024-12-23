import os
from dotenv import load_dotenv  # Optional for managing environment variables
from common.file_utils import save_json, send_json
load_dotenv()  # Load environment variables from a .env file if present


class AidevsMessageHandler:
    def __init__(self, task_name, base_dir):
        self.task_name = task_name
        self.api_key = os.getenv("AI_DEVS_3_API_KEY")
        self.server_url = os.getenv("AI_DEVS_3_SERVER_URL")
        
        # Define query and response directories
        self.query_dir = base_dir / "centrala_queries"
        self.response_dir = base_dir / "centrala_responses"
        
        # Ensure directories exist
        self.query_dir.mkdir(parents=True, exist_ok=True)
        self.response_dir.mkdir(parents=True, exist_ok=True)

    def _get_next_file_number(self, directory):
        """Determine the next file number based on existing files."""
        files = list(directory.glob("*.json"))
        return len(files) + 1

    def ask_centrala_aidevs(self, message):
        """Send a message to the centrala aidevs server and save query/response files."""
        query = {
            "task": self.task_name,
            "apikey": self.api_key,
            "answer": message
        }
        
        # Determine file paths
        file_number = self._get_next_file_number(self.query_dir)
        query_path = self.query_dir / f"{file_number}_centrala_query.json"
        response_path = self.response_dir / f"{file_number}_centrala_response.json"
        
        # Save the query
        save_json(query, query_path)
        
        # Simulate sending query and receiving response
        response = send_json(self.server_url, query)
        
        # Save the response
        save_json(response, response_path)
        
        print(response)
        return response
