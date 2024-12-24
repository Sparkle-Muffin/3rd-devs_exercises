import os
from pathlib import Path
from common.file_utils import download_file, extract_file, save_txt_file
import random
import json


def main():
    # 0. Initialize
    download_url = os.getenv("TASK_17_DOWNLOAD_URL")
    task_path = Path(__file__).parent
    download_files_path = task_path / "download_files"
    download_files_path.mkdir(parents=True, exist_ok=True)
    program_files_path = task_path / "program_files"


    # 1. Download and extract zip file
    zip_path = download_file(download_url, download_files_path)
    extract_dir = extract_file(zip_path)
    correct_file_path = extract_dir / "correct.txt"
    incorrect_file_path = extract_dir / "incorrect.txt"
    finetuning_jsonl_path = program_files_path / "finetuning.jsonl"
    finetuning_json_path = program_files_path / "finetuning_line_sketch.json"


    # 2. Convert correct and incorrect lines to JSONL format
    finetuning_jsonl = []
    finetuning_json = json.load(open(finetuning_json_path, "r"))

    with open(correct_file_path, "r") as correct_file:
        lines = correct_file.readlines()
        for line in lines:
            finetuning_json["messages"][1]["content"] = line.strip()
            finetuning_json["messages"][2]["content"] = "correct"
            finetuning_jsonl.append(json.dumps(finetuning_json))

    with open(incorrect_file_path, "r") as incorrect_file:
        lines = incorrect_file.readlines()
        for line in lines:
            finetuning_json["messages"][1]["content"] = line.strip()
            finetuning_json["messages"][2]["content"] = "incorrect"
            finetuning_jsonl.append(json.dumps(finetuning_json))


    # 3. Mix lines in JSONL and save it
    random.shuffle(finetuning_jsonl)
    finetuning_jsonl_str = "\n".join(finetuning_jsonl)
    save_txt_file(finetuning_jsonl_str, finetuning_jsonl_path)


if __name__ == "__main__":
    main()
