from typing import Dict, List, Optional
import base64
from openai import OpenAI
from pathlib import Path

def encode_image(image_path: str) -> str:
    """Encode image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def create_image_message(image_paths: List[str]) -> List[Dict]:
    """Create OpenAI message format for images."""
    return [
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{encode_image(path)}"
            }
        }
        for path in image_paths
    ]

def call_openai(
    client: OpenAI,
    messages: List[Dict[str, str]],
    images: Optional[List[str]] = None,
    model: str = "gpt-4o",
    response_format: Optional[Dict] = None,
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
            content.extend(create_image_message(images))
        formatted_messages.append({"role": msg['role'], "content": content})
    
    response = client.chat.completions.create(
        model=model,
        response_format=response_format,
        messages=formatted_messages
    )
    print(response.choices[0].message.content)
    return response.choices[0].message.content 