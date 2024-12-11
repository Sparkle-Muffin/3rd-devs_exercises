import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from tasks.common.send_json import send_json
from tasks.common.file_utils import save_txt_file, read_file_content, save_json
from tasks.common.openai_utils import call_openai

from os import getenv
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path


def main():
    # Initialize
    load_dotenv()
    openai_client = OpenAI()

    # Read prompt and question
    prompt = read_file_content(Path(__file__).parent / "prompt.txt")
    question = "Zwróć mi numery ID czynnych datacenter, które zarządzane są przez menadżerów, którzy aktualnie przebywają na urlopie (są nieaktywni)."

    # Call GPT
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': question}
    ]
    response = call_openai(openai_client, messages)

    GPT_response_path = Path(__file__).parent / "GPT_response.txt"
    save_txt_file(response, GPT_response_path)

    # Prepare database query
    db_query = {
        "task": "database",
        "apikey": getenv("AI_DEVS_3_API_KEY"),
        "query": response.replace("```sql", "").replace("```", "")
    }

    # Save database query
    db_query_path = Path(__file__).parent / "db_query.json"
    save_json(db_query, db_query_path)

    # Send database query
    db_response = send_json(getenv("TASK_13_DATABASE_API"), db_query_path)

    # Save database response
    db_response_path = Path(__file__).parent / "db_response.json"
    save_json(db_response, db_response_path)

    # Extract datacenters IDs
    datacenters_IDs = [item["dc_id"] for item in db_response["reply"]]

    # Create and send submission
    submission = {
        "task": getenv("TASK_13_TASK_NAME"),
        "apikey": getenv("AI_DEVS_3_API_KEY"),
        "answer": datacenters_IDs
    }
    submission_file_path = Path(__file__).parent / "submission_file.json"
    save_json(submission, submission_file_path)
    send_json(getenv("TASK_13_SUBMISSION_URL"), submission_file_path)


if __name__ == "__main__":
    main()
