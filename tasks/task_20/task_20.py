from pathlib import Path
from common.file_utils import read_file_content, download_file, pdf_to_text
from common.openai_utils import OpenaiClient
from common.centrala_aidevs_utils import AidevsMessageHandler
import os
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


    # 1. Download notebook and convert to plaintext
    notebook_pdf_path = download_file(notebook_url, downloads_dir)
    pdf_to_text(notebook_pdf_path, notebook_txt_path)

    
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


    # 7. Ask OpenAI to answer the questions
    prompt = read_file_content(prompts_dir / "answer_the_questions.txt")
    questions = read_file_content(questions_path)
    text_to_read = read_file_content(notebook_txt_path)
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': 
         f"//=============== QUESTIONS ===============//:\n\n{questions}\n\n"
         f"//=============== TEXT ===============//:\n\n{text_to_read}"}
    ]
    response = openai_msg_handler.call_openai(messages, response_format={"type": "json_object"})
    answers = response["answers"]


    # 8. Send answers to Aidevs
    aidevs_msg_handler.ask_centrala_aidevs(answers)


if __name__ == "__main__":
    main()