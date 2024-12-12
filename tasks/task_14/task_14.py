import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from tasks.common.send_json import send_json
from tasks.common.file_utils import save_txt_file, read_file_content, save_json, download_file, read_json
from tasks.common.openai_utils import call_openai

from os import getenv
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
import json


query_number = 0
def ask_database(db_name, query):
        # Current query number
        global query_number

        # Create database query
        db_query = {
            "apikey": getenv("AI_DEVS_3_API_KEY"),
            "query": query
        }

        # Save database query
        os.makedirs(Path(__file__).parent / "queries", exist_ok=True)
        db_query_path = Path(__file__).parent / f"queries/{db_name}_db_query_{query_number}.json"
        save_json(db_query, db_query_path)

        # Send database query)
        db_response = send_json(getenv(f"TASK_14_DATABASE_{db_name}_API"), db_query_path)

        # Save database response
        os.makedirs(Path(__file__).parent / "responses", exist_ok=True)
        db_response_path = Path(__file__).parent / f"responses/{db_name}_db_response_{query_number}.json"
        save_json(db_response, db_response_path)

        message = db_response["message"]

        # Increment query number
        query_number += 1

        # Return message
        print(message)
        return message


def check_proper_name(message: str):
    if not message.isupper() or message.find("/") != -1 or message.find(".") != -1 or message.find("*") != -1:
        return False
    return True


def main():
    # Initialize
    load_dotenv()
    openai_client = OpenAI()

    note_path = download_file(getenv("TASK_14_NOTE_URL"), Path(__file__).parent)
    note_content = read_file_content(note_path)

    prompt = read_file_content(Path(__file__).parent / "prompt.txt")

    # Call GPT
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': note_content}
    ]
    response = call_openai(openai_client, messages)

    GPT_response_path = Path(__file__).parent / "GPT_response.json"
    save_json(json.loads(response), GPT_response_path)


    note_content = read_json(GPT_response_path)
    people_names = note_content["names"]
    places_names = note_content["cities"]
    passed_people_names = []
    passed_places_names = []
    garbage = []

    # Get people names
    for name in people_names:
        if name not in passed_people_names:
            passed_people_names.append(name)
            db_response = ask_database("PEOPLE", name)

            if check_proper_name(db_response):
                new_places_names = db_response.split(" ")
                for name in new_places_names:
                    if name not in places_names:
                        places_names.append(name)
            else:
                garbage.append(db_response)
            
            # Get places names
            for name in places_names:
                if name not in passed_places_names:
                    passed_places_names.append(name)
                    db_response = ask_database("PLACES", name)

                    if check_proper_name(db_response):
                        new_people_names = db_response.split(" ")
                        for name in new_people_names:
                            if name not in people_names:
                                people_names.append(name)
                    else:
                        garbage.append(db_response)

    # Save people, places and garbage
    people_places_and_garbage = {
        "people": people_names,
        "places": places_names,
        "garbage": garbage
    }
    people_places_and_garbage_path = Path(__file__).parent / "people_places_and_garbage.json"
    save_json(people_places_and_garbage, people_places_and_garbage_path)

    # Check every place
    for place in people_places_and_garbage["places"]:
        # Create and send submission
        submission = {
            "task": getenv("TASK_14_TASK_NAME"),
            "apikey": getenv("AI_DEVS_3_API_KEY"),
            "answer": place
        }
        submission_file_path = Path(__file__).parent / "submission_file.json"
        save_json(submission, submission_file_path)
        send_json(getenv("TASK_14_SUBMISSION_URL"), submission_file_path)


if __name__ == "__main__":
    main()
