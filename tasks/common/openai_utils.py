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
    prompt: str,
    images: Optional[List[str]] = None,
    model: str = "gpt-4o",
    response_format: Optional[Dict] = None
) -> str:
    """Make an OpenAI API call with optional images."""
    message_content = [{"type": "text", "text": prompt}]
    
    if images:
        message_content.extend(create_image_message(images))
    
    response = client.chat.completions.create(
        model=model,
        response_format=response_format,
        messages=[{"role": "user", "content": message_content}]
    )
    
    return response.choices[0].message.content 