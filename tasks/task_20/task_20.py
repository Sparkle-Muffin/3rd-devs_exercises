import sys
from pathlib import Path
import os
sys.path.insert(0, str(os.getcwd()))

from common.file_utils import read_file_content, download_file, pdf_to_text
from common.openai_utils import OpenaiClient
from common.centrala_aidevs_utils import AidevsMessageHandler
from dotenv import load_dotenv
from pdf2image import convert_from_path
from common.opencv_utils import split_text_blocks

task_name = os.getenv("TASK_20_TASK_NAME")
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
    notebook_url = os.getenv("TASK_20_NOTEBOOK_URL")
    questions_url = os.getenv("TASK_20_QUESTIONS_URL")
    notebook_txt_path = program_files_dir / "notebook.txt"
    notebook_photo_path = program_files_dir / "notebook_last_page.png"
    text_blocks_dir = program_files_dir / "text_blocks"
    text_blocks_dir.mkdir(parents=True, exist_ok=True)
    text_blocks_prefix = text_blocks_dir / "text_block"
    notebook_with_dates_path = program_files_dir / "notebook_with_dates.txt"
    notebook_with_sigla_path = program_files_dir / "notebook_with_sigla.txt"


    # 1. Download notebook and convert to plaintext
    notebook_pdf_path = download_file(notebook_url, downloads_dir)
    pdf_to_text(notebook_pdf_path, notebook_txt_path, number_the_pages=True)

    
    # 2. Convert last page to image
    images = convert_from_path(notebook_pdf_path)
    last_page = images[-1]  # Get the last page
    last_page.save(str(notebook_photo_path), format='PNG')
    

    # 3. Split text blocks from image
    split_text_blocks(notebook_photo_path, text_blocks_prefix, contour_min_width=200, contour_min_height=200)
    text_blocks_paths = list(text_blocks_dir.glob("*.png"))

    
    # 4. Read text from each text block
    read_text = "\n\n"
    prompt = read_file_content(prompts_dir / "read_text_from_image.txt")
    for text_block_path in text_blocks_paths:
        messages = [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': "Image is attached."}
        ]
        response = openai_msg_handler.call_openai(messages, [text_block_path], response_format={"type": "json_object"}, temperature=0.0)
        text_blocks = response["text"]
        read_text += text_blocks + "\n\n"


    # 5. Append the read text to the notebook text file
    with open(notebook_txt_path, 'a', encoding='utf-8') as f:
        f.write(read_text)


    # 6. Download questions
    questions_path = download_file(questions_url, downloads_dir)


    # 7. Ask OpenAI to add date information to the text
    prompt = read_file_content(prompts_dir / "add_dates_to_the_text.txt")
    text_to_read = read_file_content(notebook_txt_path)
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': 
         f"//=============== TEXT ===============//:\n\n{text_to_read}"}
    ]
    response = openai_msg_handler.call_openai(messages)
    with open(notebook_with_dates_path, 'w', encoding='utf-8') as f:
        f.write(response)


    # 8. Ask OpenAI to expand biblical sigla
    prompt = read_file_content(prompts_dir / "expand_biblical_sigla.txt")
    text_to_read = read_file_content(notebook_with_dates_path)
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': 
         f"\n\n{text_to_read}"}
    ]
    response = openai_msg_handler.call_openai(messages)
    with open(notebook_with_sigla_path, 'w', encoding='utf-8') as f:
        f.write(response)


    # 9. Ask OpenAI to prepare lists of answers
    prompt = read_file_content(prompts_dir / "prepare_lists_of_answers.txt")
    questions = read_file_content(questions_path)
    text_to_read = read_file_content(notebook_with_sigla_path)
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': 
         f"//=============== QUESTIONS ===============//:\n\n{questions}\n\n"
         f"//=============== TEXT ===============//:\n\n{text_to_read}"}
    ]
    response = openai_msg_handler.call_openai(messages, response_format={"type": "json_object"})
    possible_answers = response["answers"]


    return_code = 1
    answers = None
    feedback = None
    all_previous_answers = []
    all_previous_feedbacks = []
    counter = 0
    while(return_code != 0):
        # 10. Ask OpenAI to answer the questions
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
        response = openai_msg_handler.call_openai(messages=messages, response_format={"type": "json_object"})
        answers = response["answers"]


        # 11. Send answers to Aidevs
        feedback = aidevs_msg_handler.ask_centrala_aidevs(answers)
        return_code = feedback.get("code")
        print(f"Return code: {return_code}")


if __name__ == "__main__":
    main()