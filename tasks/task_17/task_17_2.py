import os
from pathlib import Path
from common.file_utils import read_file_content
from common.openai_utils import OpenaiClient
from common.centrala_aidevs_utils import AidevsMessageHandler

task_name = os.getenv("TASK_17_TASK_NAME")
task_path = Path(__file__).parent
aidevs_msg_handler = AidevsMessageHandler(task_name, task_path)
openai_msg_handler = OpenaiClient(task_path)


def main():
    # 0. Initialize
    verify_file_path = task_path / "download_files/lab_data" / "verify.txt"
    prompts_dir = task_path / "prompts"

    
    prompt = read_file_content(prompts_dir / "validate_data.txt")
    verify_data = read_file_content(verify_file_path)
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': verify_data}
    ]
    response = openai_msg_handler.call_openai(messages, response_format={"type": "json_object"}, model="ft:gpt-4o-mini-2024-07-18:personal:ai-devs-s04e02:AhlSIBld")
    response = response["answer"]
    aidevs_msg_handler.ask_centrala_aidevs(response)


if __name__ == "__main__":
    main()
