import sys
from pathlib import Path
import os
import re

sys.path.insert(0, str(os.getcwd()))

from common.file_utils import download_file, read_json, read_file_content, save_json, extract_file, send_json
from common.openai_utils import OpenaiClient
from common.centrala_aidevs_utils import AidevsMessageHandler
from dotenv import load_dotenv

task_name = os.getenv("TASK_21_TASK_NAME")
task_path = Path(__file__).parent
aidevs_msg_handler = AidevsMessageHandler(task_name, task_path)
openai_msg_handler = OpenaiClient(task_path)


def main():
    # 0. Initialize
    load_dotenv()
    prompts_dir = task_path / "prompts"
    program_files_dir = task_path / "program_files"
    program_files_dir.mkdir(parents=True, exist_ok=True)
    downloads_dir = task_path / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)


    # # 1. Download conversations and questions
    conversations_raw_path = download_file(os.getenv("TASK_21_CONVERSATIONS_URL"), downloads_dir)
    questions_path = download_file(os.getenv("TASK_21_QUESTIONS_URL"), downloads_dir)
    conversations_ordered_path = program_files_dir / "conversations_ordered.json"
    conversations_with_names_path = program_files_dir / "conversations_with_names.json"
    pliki_z_fabryki_zip_path = downloads_dir / "pliki_z_fabryki.zip"
    pliki_z_fabryki_path = extract_file(pliki_z_fabryki_zip_path)
    facts_path = pliki_z_fabryki_path / "facts"
    urls_and_passwords_path = program_files_dir / "urls_and_passwords.json"
    chosen_url_and_password_path = program_files_dir / "chosen_url_and_password.json"


    # 2. Ask GPT 5 to put sentences in the correct order
    prompt = read_file_content(prompts_dir / "put_sentences_in_order.txt")
    conversations_raw = read_file_content(conversations_raw_path)
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': conversations_raw}
    ]
    response = openai_msg_handler.call_openai(messages, 
                                                response_format={"type": "json_object"}, 
                                                model="gpt-5", 
                                                reasoning_effort="high",
                                                temperature=1)
    save_json(response, conversations_ordered_path)


    # 3. Ask GPT 5 to find the names
    prompt = read_file_content(prompts_dir / "find_the_names.txt")
    conversations_ordered = read_file_content(conversations_ordered_path)
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': conversations_ordered}
    ]
    response = openai_msg_handler.call_openai(messages, 
                                                response_format={"type": "json_object"}, 
                                                model="gpt-5", 
                                                reasoning_effort="high",
                                                temperature=1)
    save_json(response, conversations_with_names_path)


    # 4. Extract all URLs from the conversations
    conversations_with_names = read_file_content(conversations_with_names_path)
    urls = re.findall(r'(https?://[^\s]+|www\.[^\s]+)', conversations_with_names)
        
    urls_and_passwords_list = []
    for url in urls:
        urls_and_passwords_list.append({"url": url})


    # 5. Ask GPT 5 nano to find the password in the conversations
    prompt = read_file_content(prompts_dir / "find_the_password.txt")
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': conversations_with_names}
    ]
    response = openai_msg_handler.call_openai(messages, 
                                                response_format={"type": "json_object"}, 
                                                model="gpt-5-nano", 
                                                temperature=1)
    
    for url_and_password in urls_and_passwords_list:
        url_and_password["password"] = response["password"]
    

    # 6. Download endpoints contents
    for url_and_password in urls_and_passwords_list:
        url = url_and_password["url"]
        password = url_and_password["password"]
        content = send_json(url, {"password": password})
        url_and_password["content"] = content

    # Create the final JSON structure
    urls_and_passwords = {
        "urls_and_passwords": urls_and_passwords_list
    }
    save_json(urls_and_passwords, urls_and_passwords_path)


    # 7. Ask GPT 5 nano to choose the right endpoint
    prompt = read_file_content(prompts_dir / "choose_the_right_endpoint.txt")
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': str(urls_and_passwords)}
    ]
    response = openai_msg_handler.call_openai(messages, 
                                                response_format={"type": "json_object"}, 
                                                model="gpt-5-nano", 
                                                temperature=1)

    save_json(response, chosen_url_and_password_path)


    # 8. Ask GPT 5 to prepare lists of answers
    prompt = read_file_content(prompts_dir / "prepare_lists_of_answers.txt")
    questions = read_file_content(questions_path)
    conversations_with_names = read_file_content(conversations_with_names_path)
    facts = ""
    for fact in facts_path.glob("*.txt"):
        facts += read_file_content(fact) + "\n\n"
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': 
         f"//=============== QUESTIONS ===============//:\n\n{questions}\n\n"
         f"//=============== TELEPHONE CONVERSATIONS ===============//:\n\n{conversations_with_names}\n\n"
         f"//=============== FACTS ===============//:\n\n{facts}"}
    ]
    response = openai_msg_handler.call_openai(messages, 
                                            response_format={"type": "json_object"}, 
                                            model="gpt-5", 
                                            reasoning_effort="high",
                                            temperature=1)
    possible_answers = response["answers"]


    return_code = 1
    answers = None
    feedback = None
    all_previous_answers = []
    all_previous_feedbacks = []
    counter = 0
    while(return_code != 0):
        # 9. Ask GPT 5 to answer the questions
        counter += 1
        prompt = read_file_content(prompts_dir / "answer_the_questions.txt")
        system_prompt = prompt
        system_prompt += f"\n\n//=============== THIS IS THE {counter} PROMPT ===============//:\n\n"
        if answers and feedback:
            all_previous_answers.append(answers)
            all_previous_feedbacks.append(feedback)
            system_prompt += f"\n\n//=============== YOUR PREVIOUS ANSWERS ===============//:\n\n"
            for i, answer in enumerate(all_previous_answers): 
                system_prompt += f"//------------- From {i+1} prompt -------------//:\n\n"
                system_prompt += f"{answer}\n\n"
            system_prompt += f"\n\n//=============== FEEDBACK ===============//:\n\n"
            for i, feedback in enumerate(all_previous_feedbacks):
                system_prompt += f"//------------- From {i+1} prompt -------------//:\n\n"
                system_prompt += f"{feedback}\n\n"
        questions = read_file_content(questions_path)
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': 
             f"//=============== QUESTIONS ===============//:\n\n{questions}\n\n"
             f"//=============== POSSIBLE ANSWERS ===============//:\n\n{possible_answers}"}
        ]
        response = openai_msg_handler.call_openai(messages, 
                                        response_format={"type": "json_object"}, 
                                        model="gpt-5", 
                                        reasoning_effort="high",
                                        temperature=1)
        answers = response["answers"]


        # 10. Get the password from the chosen endpoint
        endpoint = read_json(chosen_url_and_password_path)
        url = endpoint["url"]
        password = endpoint["password"]
        content = send_json(url, {"password": password})
        code = content["message"]

        answers["05"] = code


        # 11. Send answers to Aidevs
        feedback = aidevs_msg_handler.ask_centrala_aidevs(answers)
        return_code = feedback.get("code")
        print(f"Return code: {return_code}")    


if __name__ == "__main__":
    main()