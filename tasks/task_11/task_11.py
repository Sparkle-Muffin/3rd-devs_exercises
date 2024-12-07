import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from tasks.common.send_json import send_json
from tasks.common.file_utils import save_txt_file, read_file_content, save_json, read_json, download_file, extract_file, download_website_source, process_audio_files, extract_text_from_translated_audio_files, download_files_from_website
from tasks.common.openai_utils import call_openai

from os import getenv
from dotenv import load_dotenv
import json
from openai import OpenAI
from pathlib import Path
from typing import List, Dict, Any


def merge_reports_and_facts(report_files_list: List[str], fact_files_list: List[str], output_path: str) -> Dict:
    report_files = []
    for file in report_files_list:
        report_name = file.stem
        report_content = read_file_content(file)
        if report_content != "":
            report_files.append({report_name: report_content})

    fact_files = []
    for file in fact_files_list:
        fact_name = file.stem
        fact_content = read_file_content(file)
        if fact_content != "":
            fact_files.append({fact_name: fact_content})

    # Save both report_files and fact_files in a single JSON object
    combined_data = {
        "report_files": report_files,
        "fact_files": fact_files
    }
    save_json(combined_data, output_path)


def main():
    # Initialize
    load_dotenv()
    client = OpenAI()

    # Download and extract files
    zip_path = download_file(getenv("TASK_11_DOWNLOAD_URL"), Path(__file__).parent)
    extract_path = extract_file(zip_path)
    report_files_list = list(Path(extract_path).glob("*.txt"))
    fact_files_list = list((Path(extract_path) / "facts").glob("*.txt"))

    # Merge reports and facts
    reports_and_facts_file_path = Path(__file__).parent / "reports_and_facts_file.json"
    merge_reports_and_facts(report_files_list, fact_files_list, reports_and_facts_file_path)
    
    prompt_rewritting = read_file_content(Path(__file__).parent / "prompt_rewritting.txt")
    reports_and_facts_file = json.dumps(read_json(reports_and_facts_file_path))

    # Call GPT
    messages = [
        {'role': 'system', 'content': prompt_rewritting},
        {'role': 'user', 'content': reports_and_facts_file}
    ]
    response = call_openai(client, messages)

    GPT_rewritting_path = Path(__file__).parent / "GPT_rewritting.json"
    save_json(json.loads(response), GPT_rewritting_path)


    prompt_keywords = read_file_content(Path(__file__).parent / "prompt_keywords.txt")
    rewritting_file = json.dumps(read_json(GPT_rewritting_path))

    # Call GPT
    messages = [
        {'role': 'system', 'content': prompt_keywords},
        {'role': 'user', 'content': rewritting_file}
    ]
    response = call_openai(client, messages)

    GPT_keywords_path = Path(__file__).parent / "GPT_keywords.json"
    save_json(json.loads(response), GPT_keywords_path)

    # Create and send submission
    submission = {
        "task": getenv("TASK_11_TASK_NAME"),
        "apikey": getenv("AI_DEVS_3_API_KEY"),
        "answer": read_json(GPT_keywords_path)
    }
    submission_file_path = Path(__file__).parent / "submission_file.json"
    save_json(submission, submission_file_path)
    send_json(getenv("TASK_11_SUBMISSION_URL"), submission_file_path)


if __name__ == "__main__":
    main()