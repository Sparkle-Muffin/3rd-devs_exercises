import requests
from bs4 import BeautifulSoup
from os import getenv
from dotenv import load_dotenv
import json
import os

load_dotenv()

openai_api_key = getenv("OPEN_AI_API_KEY")
robot_website = getenv("TASK_1_ROBOT_SITE_URL")
username = getenv("TASK_1_USERNAME")
password = getenv("TASK_1_PASSWORD")


def get_paragraph_content(url, element_id):
    """
    Fetches the content of a paragraph with the specified id from a webpage.

    Args:
        url (str): The URL of the webpage.
        element_id (str): The id of the HTML element to find.

    Returns:
        str: The content of the paragraph, or None if not found.
    """
    try:
        # Step 1: Request the page content
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for failed requests

        # Step 2: Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Step 3: Find the paragraph with the specified id and extract its content
        paragraph = soup.find("p", id=element_id)

        if paragraph:
            question = paragraph.get_text(strip=True)
            return question  # Returns the text content without extra spaces

        # If the paragraph is not found, return None
        return None

    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None


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
    os.makedirs("tasks/task_1", exist_ok=True)

    # Save response to a JSON file
    with open("tasks/task_1/GPT_response.json", "w", encoding="utf-8") as f:
        json.dump(response_data, f, indent=2, ensure_ascii=False)

    return answer_content


def submit_form_data(url, username, password, answer):
    """
    Submits form data to a specified URL using POST method.

    Args:
        url (str): The URL to submit the form to
        username: First input value
        password: Second input value
        answer: Third input value

    Returns:
        str: Server response content
    """
    try:
        # Create a dictionary with the form data
        form_data = {"username": username, "password": password, "answer": answer}

        # Send POST request with form data
        response = requests.post(url, data=form_data)
        response.raise_for_status()  # Raise an error for failed requests

        return response.text  # Return the server's response

    except requests.RequestException as e:
        print(f"An error occurred while submitting the form: {e}")
        return None


def main():
    # Go to the robot website and retrieve the question content
    element_id = "human-question"
    question_content = get_paragraph_content(robot_website, element_id)

    if question_content:
        print("Paragraph content:", question_content)
    else:
        print("Paragraph not found or there was an error retrieving it.")

    # Create a prompt for OpenAI
    prompt_answer_question = f"Answer to this question in Polish: {question_content}. Answer it with just a year of the event. No comments, formatting or anything."

    # Ask OpenAI to answer the question
    answer = call_openai(prompt_answer_question)
    print(answer)

    # Submit the answer to the robot website
    secret_url = submit_form_data(robot_website, username, password, answer)
    print(secret_url)


if __name__ == "__main__":
    main()
