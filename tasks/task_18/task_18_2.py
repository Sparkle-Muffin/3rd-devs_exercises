from pathlib import Path
from common.file_utils import download_file, read_json, save_json
from common.openai_utils import OpenaiClient
from common.centrala_aidevs_utils import AidevsMessageHandler
from common.website_search.website_search import WebsiteSearchAgent
import os
from dotenv import load_dotenv

task_name = os.getenv("TASK_18_TASK_NAME")
task_path = Path(__file__).parent
aidevs_msg_handler = AidevsMessageHandler(task_name, task_path)
openai_msg_handler = OpenaiClient(task_path)
website_search_agent = WebsiteSearchAgent(task_path)

def main():
    # 0. Initialize
    load_dotenv()
    program_files_dir = task_path / "program_files"
    questions_url = os.getenv("TASK_18_QUESTIONS_URL")
    website_url = os.getenv("TASK_18_WEBSITE_URL")
    questions_path = ""
    questions_and_answers_path = program_files_dir / "questions_and_answers.json"


    # 1. Download questions
    questions_path = download_file(questions_url, program_files_dir)
    questions = read_json(questions_path)


    # 2. Find answers
    questions_and_answers = website_search_agent.navigate_and_find_answers(website_url, questions)
    save_json(questions_and_answers, questions_and_answers_path)


    # 3. Send submission to Centrala AI_devs
    submission = {}
    for question_id, question_and_answer in questions_and_answers.items():
        answer = question_and_answer["answer"]
        submission.update({question_id: answer})
    aidevs_msg_handler.ask_centrala_aidevs(submission)


if __name__ == "__main__":
    main()