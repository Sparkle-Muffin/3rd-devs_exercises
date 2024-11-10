import requests
from os import getenv
from dotenv import load_dotenv
import json
import os

load_dotenv()

openai_api_key = getenv("OPEN_AI_API_KEY")
robot_website = getenv("TASK_2_ROBOT_SITE_URL")

msgID = 0

def call_openai(prompt: str):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}",
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()

    # Extract the actual answer content
    answer_content = response_data["choices"][0]["message"]["content"]

    # Create directory if it doesn't exist
    os.makedirs("tasks/task_2", exist_ok=True)

    # Save response to a JSON file
    with open("tasks/task_2/GPT_response.json", "w", encoding="utf-8") as f:
        json.dump(response_data, f, indent=2, ensure_ascii=False)

    return answer_content


def send_data(url, data):
    """
    Sends data to a specified URL using POST method.

    Args:
        url (str): The URL to submit the form to
        data: Data to be sent

    Returns:
        str: Server response content
    """
    try:
        # Add headers for JSON content
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Try sending as JSON data
        response = requests.post(url, json=data, headers=headers)
        
        response.raise_for_status()
        return response.text

    except requests.RequestException as e:
        print(f"An error occurred while submitting the form: {e}")
        return None


def main():
    # Get the initial message from the JSON file
    with open("tasks/task_2/initial_message.json", "r") as file:
        initial_message = json.load(file)
    question = send_data(robot_website, initial_message)
    
    # Parse the JSON string into a Python dictionary
    question_data = json.loads(question)
    
    # Extract the fields
    msgID = question_data["msgID"]
    text = question_data["text"] 
    print(f"Message ID: {msgID}")
    print(f"Text: {text}")

    # Get the prompt from the prompt.txt file
    with open('tasks/task_2/prompt.txt', 'r') as file:
        prompt = file.read()
    prompt += prompt + "/n" + text

    # Ask OpenAI to answer the question
    answer = call_openai(prompt)
    print(answer)

    # Create a JSON object with the answer
    json_answer = {
        "msgID": msgID,
        "text": answer
    }

    # Send the answer to the robot website  
    robot_answer = send_data(robot_website, json_answer)
    print(robot_answer)


if __name__ == "__main__":
    main()
