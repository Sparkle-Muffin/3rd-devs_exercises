import requests
import asyncio
import aiohttp
import time
from dotenv import load_dotenv
from os import getenv
from pathlib import Path
import json
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)
from common.file_utils import read_json, send_json, save_json

load_dotenv()

# task_path = Path(__file__).parent
# program_files_dir = task_path / "program_files"
# program_files_dir.mkdir(parents=True, exist_ok=True)

urls_and_contents = [
    {"url": getenv("TASK_23_API_URL"), "content": {"sign": ""}, "fetch": ""},
    {"url": getenv("TASK_23_QUESTIOS_0_URL"), "fetch": ""},
    {"url": getenv("TASK_23_QUESTIOS_1_URL"), "fetch": ""}
]


def get_hash():
    response = requests.post(getenv("TASK_23_API_URL"), json={"password": "NONOMNISMORIAR"})
    urls_and_contents[0]["content"]["sign"] = response.json()["message"]


async def fetch(session, url_and_content):
    """Fetch one URL, and store the content."""
    try:
        if "content" in url_and_content:
            content = url_and_content["content"]
        else:
            content = None
        # async with session.post(url_and_content["url"], json=content) as response:
        async with session.get(url_and_content["url"], json=content) as response:
            data = await response.json()  # response is JSON
            url_and_content["fetch"] = data

    except Exception as e:
        print(f"Error fetching {url_and_content['url']}: {e}")


async def concurrent_requests():
    """Request URLs every INTERVAL seconds for DURATION seconds."""

    async with aiohttp.ClientSession() as session:
        # Run all fetches concurrently
        await asyncio.gather(*(fetch(session, url_and_content) for url_and_content in urls_and_contents))

    print(json.dumps(urls_and_contents, indent=2))


def prepare_answer():
    questions_0 = urls_and_contents[1]["fetch"]["data"]
    questions_1 = urls_and_contents[2]["fetch"]["data"]

    answers_0 = []
    answers_1 = []

    file_0 = read_json(Path(__file__).parent / "program_files" / "questions_and_answers_0.json")
    file_1 = read_json(Path(__file__).parent / "program_files" / "questions_and_answers_1.json")

    for question in file_0.items():
        if question[1]["question"] in questions_0:
            answers_0.append(question[1]["answer"])

    for question in file_1.items():
        if question[1]["question"] in questions_1:
            answers_1.append(question[1]["answer"])

    answer = {
        "apikey": getenv("AI_DEVS_3_API_KEY"),
        "timestamp": urls_and_contents[0]["fetch"]["message"]["timestamp"],
        "signature": urls_and_contents[0]["fetch"]["message"]["signature"],
        "answer": answers_0 + answers_1
    }

    save_json(answer, Path(__file__).parent / "program_files" / "answer.json")

    return answer


def send_answer(answer):
    centrala_response = send_json(getenv("TASK_23_API_URL"), answer)
    save_json(centrala_response, Path(__file__).parent / "program_files" / "centrala_response.json")


if __name__ == "__main__":
    get_hash()
    asyncio.run(concurrent_requests())
    answer = prepare_answer()
    send_answer(answer)