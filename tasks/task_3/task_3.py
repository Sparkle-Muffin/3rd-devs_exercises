import requests
from os import getenv
from dotenv import load_dotenv
import json
import os
import sys

# Add the parent directory to the system path (otherwise the send_json.py can't be imported)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from tasks.common.send_json import send_json

load_dotenv()

openai_api_key = getenv("OPEN_AI_API_KEY")
ai_devs_3_api_key = getenv("AI_DEVS_3_API_KEY")
task_name = getenv("TASK_3_TASK_NAME")
submission_url = getenv("TASK_3_SUBMISSION_URL")

# New list to store question-answer pairs
test_qa_pairs = []

# Add at the top of the file with other global variables
response_counter = 0


def fix_math():
    # Read the original file
    with open("tasks/task_3/calibration_original.json", "r") as file:
        data = json.load(file)
    
    # Iterate through test data
    for item in data["test-data"]:
        # Skip entries that don't have both "question" and "answer"
        if not ("question" in item and "answer" in item):
            continue
            
        # Extract numbers from the question (format: "a + b")
        try:
            a, b = map(int, item["question"].split(" + "))
            correct_answer = a + b
            
            # Update the answer if it's incorrect
            if item["answer"] != correct_answer:
                item["answer"] = correct_answer
        except (ValueError, AttributeError):
            continue
    
    # Save the corrected data to a new file with a different name
    with open("tasks/task_3/calibration_math_fixed.json", "w") as file:
        json.dump(data, file, indent=4)


def collect_test_questions():
    # Read the original file
    with open("tasks/task_3/calibration_math_fixed.json", "r") as file:
        data = json.load(file)
    
    # Iterate through test data
    for item in data["test-data"]:
        # Check if item has a "test" field
        if "test" in item and isinstance(item["test"], dict):
            # Check if "q" field exists in the test dictionary
            if "q" in item["test"]: 
                # Add to structured list
                test_qa_pairs.append({
                    "question": item["test"]["q"],
                    "answer": ""  # Empty for now
                })


def call_openai(prompt: str):
    global response_counter
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

    # Increment counter for unique filenames
    response_counter += 1
    
    # Create directory if it doesn't exist
    os.makedirs("tasks/task_3", exist_ok=True)

    # Save response to a numbered JSON file
    filename = f"tasks/task_3/GPT_response_{response_counter}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(response_data, f, indent=2, ensure_ascii=False)

    return answer_content


def answer_questions():
    # Read the fixed math file
    with open("tasks/task_3/calibration_math_fixed.json", "r") as file:
        data = json.load(file)
    
    # Iterate through test data
    for item in data["test-data"]:
        # Check if item has a test field and it's a dictionary
        if "test" in item and isinstance(item["test"], dict):
            # Get the question from the test
            test_question = item["test"].get("q")
            
            # Find matching question in test_qa_pairs
            for qa_pair in test_qa_pairs:
                if qa_pair["question"] == test_question:
                    # Update the answer in the JSON
                    item["test"]["a"] = str(qa_pair["answer"])
                    break
    
    # Save the updated data to a new file
    with open("tasks/task_3/calibration_final_version.json", "w") as file:
        json.dump(data, file, indent=4)


def update_api_key():
    # Read the final version file
    with open("tasks/task_3/calibration_final_version.json", "r") as file:
        data = json.load(file)
    
    # Replace the placeholder with actual API key
    data["apikey"] = ai_devs_3_api_key
    
    # Save the updated data back to the file
    with open("tasks/task_3/calibration_final_version.json", "w") as file:
        json.dump(data, file, indent=4)


def create_submission_file():
    # Read the content of calibration_final_version.json
    with open("tasks/task_3/calibration_final_version.json", "r") as file:
        calibration_data = json.load(file)
    
    # Create the submission structure
    submission_data = {
        "task": task_name,
        "apikey": ai_devs_3_api_key,
        "answer": calibration_data
    }
    
    # Save the submission data to a new file
    with open("tasks/task_3/submission_file.json", "w") as file:
        json.dump(submission_data, file, indent=4)


def main():
    # Fix math operations in the original file
    fix_math()

    # Collect test questions
    collect_test_questions()

    # Print the structured Q&A pairs
    print("\nStructured Q&A pairs:")
    for qa in test_qa_pairs:
        print(f"Q: {qa['question']}")
        print(f"A: {qa['answer'] or 'Not answered yet'}\n")

    # Get the prompt from the prompt.txt file
    with open('tasks/task_3/prompt.txt', 'r') as file:
        prompt = file.read()
    # Call OpenAI for each question
    for qa in test_qa_pairs:
        qa["answer"] = call_openai(prompt + "/n" + qa["question"])

    # Answer the questions
    answer_questions()

    # Update the API key in the final version file
    update_api_key()
    
    # Create the submission file
    create_submission_file()

    # Path to the submission JSON file
    json_file_path = "tasks/task_3/submission_file.json"
    # Send the final version file to the submission URL
    send_json(submission_url, json_file_path)


if __name__ == "__main__":
    main()