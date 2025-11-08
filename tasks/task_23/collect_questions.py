import asyncio
import aiohttp
import time
from dotenv import load_dotenv
from os import getenv
from pathlib import Path
import json

load_dotenv()

task_path = Path(__file__).parent
program_files_dir = task_path / "program_files"
program_files_dir.mkdir(parents=True, exist_ok=True)

URLS = [
    getenv("TASK_23_QUESTIOS_0_URL"),
    getenv("TASK_23_QUESTIOS_1_URL")
]

INTERVAL = 5          # seconds
DURATION = 10 * 60    # 10 minutes in seconds


async def fetch(session, url, questions):
    """Fetch one URL, extract new unique questions, and store them."""
    try:
        async with session.get(url) as response:
            data = await response.json()  # response is JSON
            new_questions = data.get("data", [])

            # Add only new questions (avoid duplicates)
            for q in new_questions:
                if q not in questions:
                    questions.append(q)
                    print(f"[{time.strftime('%H:%M:%S')}] \n {q}")

    except Exception as e:
        print(f"Error fetching {url}: {e}")


async def periodic_requests():
    """Request URLs every INTERVAL seconds for DURATION seconds."""
    questions = {url: [] for url in URLS}  # store questions per URL

    async with aiohttp.ClientSession() as session:
        start = time.time()
        while time.time() - start < DURATION:
            # Run all fetches concurrently
            await asyncio.gather(*(fetch(session, url, questions[url]) for url in URLS))
            await asyncio.sleep(INTERVAL)

    return questions


def save_questions(questions_by_url):
    """Save questions per URL to JSON files."""
    for i, (url, questions) in enumerate(questions_by_url.items()):
        # Convert questions list to required JSON structure
        output_data = {
            f"question_{j+1}": {"question": q, "answer": ""}
            for j, q in enumerate(questions)
        }

        file_name = "questions_" + str(i) + ".json"
        file_path = program_files_dir / file_name

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)

        print(f"Saved {len(questions)} questions to {file_path}")


if __name__ == "__main__":
    all_questions = asyncio.run(periodic_requests())
    save_questions(all_questions)