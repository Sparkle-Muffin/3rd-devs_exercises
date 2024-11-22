import os
import requests
import json
from os import getenv
from dotenv import load_dotenv
import base64
from openai import OpenAI

load_dotenv()

openai_api_key = getenv("OPEN_AI_API_KEY")

client = OpenAI()


# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')


def encode_images(image_paths):
    images = []
    for image_path in image_paths:
        base64_image = encode_image(image_path)
        images.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                },
            },
        )
    return images


def call_openai_with_images(prompt: str, directory: str):
    image_paths = [
        os.path.join(directory, file)
        for file in os.listdir(directory)
        if file.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]

    images = encode_images(image_paths)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        *images
                    ],
                }
            ],
        )

    print(response.choices[0])

    answer_content = response.choices[0].message.content

    response_data = response.model_dump_json()

    os.makedirs("tasks/task_7", exist_ok=True)
    with open("tasks/task_7/GPT_response.json", "w", encoding="utf-8") as f:
        json.dump(response_data, f, indent=2, ensure_ascii=False)

    return answer_content


def main():
    # Get the prompt instructions from the prompt.txt file
    with open('tasks/task_7/prompt.txt', 'r') as file:
        prompt = file.read()

    # Ask OpenAI to answer the question
    answer = call_openai_with_images(prompt, "tasks/task_7/maps")
    print(answer)


if __name__ == "__main__":
    main()