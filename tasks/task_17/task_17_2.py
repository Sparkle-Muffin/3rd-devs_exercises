import os
import json
from pathlib import Path
from common.file_utils import read_file_content, save_txt_file
from common.openai_utils import OpenaiClient
from common.centrala_aidevs_utils import AidevsMessageHandler

task_name = os.getenv("TASK_17_TASK_NAME")
task_path = Path(__file__).parent
aidevs_msg_handler = AidevsMessageHandler(task_name, task_path)
openai_msg_handler = OpenaiClient(task_path)


def main():
    # 0. Initialize
    verify_file_path = task_path / "download_files/lab_data" / "verify.txt"
    verify_jsonl_path = task_path / "program_files" / "verify.jsonl"
    verify_json_path = task_path / "program_files" / "verify_line_sketch.json"
    prompts_dir = task_path / "prompts"

    
    verify_jsonl = []
    verify_json = json.load(open(verify_json_path, "r"))

    with open(verify_file_path, "r") as file:
        lines = file.readlines()
        for line in lines:
            identifier = line.split("=")[0]
            data = line.split("=")[1]
            verify_json["id"] = identifier
            verify_json["data"] = data.replace("\n", "")
            verify_jsonl.append(json.dumps(verify_json))
    
    verify_jsonl_str = "\n".join(verify_jsonl)
    save_txt_file(verify_jsonl_str, verify_jsonl_path)


    prompt = read_file_content(prompts_dir / "validate_data.txt")
    verify_data = read_file_content(verify_jsonl_path)
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': verify_data}
    ]
    response = openai_msg_handler.call_openai(messages,model="ft:gpt-4o-mini-2024-07-18:personal:ai-devs-s04e02:AhlSIBld")
    response = response["answer"]
    aidevs_msg_handler.ask_centrala_aidevs(response)


if __name__ == "__main__":
    main()
