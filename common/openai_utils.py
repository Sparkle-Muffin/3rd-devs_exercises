from typing import Dict, List, Optional
import base64
from openai import OpenAI
import json
from common.file_utils import save_json, save_txt_file
from dotenv import load_dotenv
import os
load_dotenv()  # Load environment variables from a .env file if present


class OpenaiClient:
    def __init__(self, base_dir):
        self.client = OpenAI()

        # Define query and response directories
        self.query_dir = base_dir / "openai_queries"
        self.response_dir = base_dir / "openai_responses"

        # Ensure directory exists
        self.query_dir.mkdir(parents=True, exist_ok=True)
        self.response_dir.mkdir(parents=True, exist_ok=True)

    def _encode_image(self, image_path: str) -> str:
        """Encode image file to base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _create_image_message(self, image_paths: List[str]) -> List[Dict]:
        """Create OpenAI message format for images."""
        return [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{self._encode_image(path)}"
                }
            }
            for path in image_paths
        ]

    def _get_next_file_number(self, directory):
        """Determine the next file number based on existing files."""
        files = list(directory.glob("*.txt")) + list(directory.glob("*.json"))
        return len(files) + 1

    def call_openai(
        self,
        messages: List[Dict[str, str]],
        images: Optional[List[str]] = None,
        model: str = "gpt-4o",
        response_format: Optional[Dict] = None,
        reasoning_effort: Optional[str] = None,
        temperature: Optional[float] = 1
    ) -> str:
        """Make an OpenAI API call with multiple messages and optional images.
        
            Args:
            client: OpenAI client instance
            messages: List of message dictionaries, each containing 'role' and 'prompt'
                 Example: [
                     {'role': 'system', 'content': 'You are a helpful assistant'},
                     {'role': 'user', 'content': 'Hello'}
                 ]
        images: Optional list of image paths
        model: The model to use
            response_format: Optional response format specification
            """
        formatted_messages = []
        for msg in messages:
            content = [{"type": "text", "text": msg['content']}]
            if msg['role'] == 'user' and images:
                content.extend(self._create_image_message(images))
            formatted_messages.append({"role": msg['role'], "content": content})
   
        response = self.client.chat.completions.create(
            model=model,
            response_format=response_format,
            messages=formatted_messages,
            temperature=temperature,
            reasoning_effort=reasoning_effort
        )

        response = response.choices[0].message.content
        print(response)
        file_number = self._get_next_file_number(self.query_dir)
        query_path = self.query_dir / f"{file_number}_openai_query.json"
        response_path = self.response_dir / f"{file_number}_openai_response.json"

        save_json(formatted_messages, query_path)

        if response_format:
            if response_format["type"] == "json_object":
                response = json.loads(response.replace("```json", "").replace("```", ""))
                save_json(response, response_path)
            else:
                save_txt_file(response, response_path)
        else:
            save_txt_file(response, response_path)

        return response
    
    
    def decode_image(self, encoded_image: str) -> str:
        """Decode base64 string to image file."""
        return base64.b64decode(encoded_image)