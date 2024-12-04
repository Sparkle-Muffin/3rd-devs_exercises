import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from tasks.common.send_json import send_json
from tasks.common.file_utils import save_txt_file, read_file_content, save_json, read_json, download_file, extract_file, download_website_source, process_audio_files, extract_text_from_translated_audio_files, download_files_from_website
from tasks.common.openai_utils import call_openai

from os import getenv
from dotenv import load_dotenv
import json
import subprocess
from openai import OpenAI
from typing import List, Dict, Any
from pathlib import Path
import requests
from PIL import Image
import pytesseract
from bs4 import BeautifulSoup


def rename_images_in_article(html_file_path: str) -> None:
    # Read the HTML file
    with open(html_file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
    
    # Find all img tags and rename their src attributes
    for index, img in enumerate(soup.find_all('img'), start=1):
        img['src'] = f'image_{index}.png'
    
    # Save the modified HTML
    with open(html_file_path, 'w', encoding='utf-8') as file:
        file.write(str(soup))
    
    print(f"Successfully renamed all images in {html_file_path}")


def replace_audio_references_with_translations(input_markdown_path: Path, audio_translations: Dict[str, str], output_markdown_path: Path) -> None:
    """
    Replaces audio file references in the markdown file with their translations.
    
    Args:
        input_markdown_path: Path to the markdown file
        audio_translations: Dictionary mapping audio filenames to their translations
        output_markdown_path: Path to the output markdown file
    """
    # Read the markdown file
    with open(input_markdown_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace each audio reference with its translation
    for audio_file, translation in audio_translations.items():
        # Replace both the audio filename and potential markdown audio links
        content = content.replace(audio_file, translation, 1)
        content = content.replace(f"[audio]({audio_file})", translation, 1)
    
    # Save the modified content
    with open(output_markdown_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Successfully replaced audio references in {input_markdown_path}")


def replace_tag_content(template_path: str, content_path: str, tag_name: str, output_path: str) -> None:
    """
    Replaces content between specified XML-style tags in a template file.
    
    Args:
        template_path: Path to the template file
        content_path: Path to the content file
        tag_name: Name of the tag to replace content between
        output_path: Path to the output file
    """
    # Read the template and content files
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    with open(content_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define the tags
    start_tag = f"<{tag_name}>"
    end_tag = f"</{tag_name}>"
    
    # Find tag positions
    start_pos = template.find(start_tag) + len(start_tag)
    end_pos = template.find(end_tag)
    
    if start_pos == -1 or end_pos == -1:
        raise ValueError(f"Tags {tag_name} not found in template")
    
    # Replace content between tags
    modified_template = (
        template[:start_pos] + 
        "\n" + content + "\n" +
        template[end_pos:]
    )
    
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(modified_template)


def main():
    # Initialize
    load_dotenv()
    # Initialize OpenAI client
    client = OpenAI()
    # Get the website URL
    website = getenv("TASK_10_ARTICLE_DOWNLOAD_URL")

    # Download the article  
    article_path = Path(__file__).parent / "article.html"
    download_website_source(website, article_path)
    # Rename the images in the article to img_1.png, img_2.png, etc.
    rename_images_in_article(article_path)

    # Download the images
    images_dir = Path(__file__).parent / "images"
    download_files_from_website(website, "img", images_dir, rename_files=True)

    # Download the audio files
    audio_files_dir = Path(__file__).parent / "audio"
    download_files_from_website(website, "audio", audio_files_dir)

    # Process audio files
    audio_output_dir = Path(__file__).parent / "translated_mp3_files"
    mp3_files = list(audio_files_dir.glob("*.mp3"))
    process_audio_files(mp3_files, audio_output_dir)

    # Convert image prompt to a string prompt
    original_prompt = pytesseract.image_to_string(Image.open(Path(__file__).parent / "original_prompt.jpeg"))
    save_txt_file(original_prompt, Path(__file__).parent / "original_prompt.txt")

    # Make a script using GPT (you have to create my_prompt.txt first)
    make_script_prompt = read_file_content(Path(__file__).parent / "my_prompt.txt")
    article = read_file_content(Path(__file__).parent / "article.html")
    
    messages = [
        {'role': 'system', 'content': make_script_prompt},
        {'role': 'user', 'content': article}
    ]
    response = call_openai(
        client,
        messages=messages
    )
    GPT_markdown_script_path = Path(__file__).parent / "GPT_markdown_script.md"
    save_txt_file(response, GPT_markdown_script_path)

    # Replace audio references with translations
    audio_texts = extract_text_from_translated_audio_files(audio_output_dir)
    modified_markdown_script_path = Path(__file__).parent / "modified_markdown_script.md"
    replace_audio_references_with_translations(GPT_markdown_script_path, audio_texts, modified_markdown_script_path)

    # Create a prompt template for questions
    questions_prompt_template_path = Path(__file__).parent / "questions_prompt_template.txt"
    # Download the questions
    questions_path = download_file(getenv("TASK_10_QUESTIONS_DOWNLOAD_URL"), Path(__file__).parent)
    questions_prompt_path = Path(__file__).parent / "questions_prompt.txt"
    # Add questions to the prompt template
    replace_tag_content(
        questions_prompt_template_path,
        questions_path,
        "questions",
        questions_prompt_path
    )
    
    # Read the questions and the modified markdown script
    questions_prompt = read_file_content(questions_prompt_path)
    modified_markdown_script = read_file_content(modified_markdown_script_path)
    
    # Call GPT
    messages = [
        {'role': 'system', 'content': questions_prompt},
        {'role': 'user', 'content': modified_markdown_script}
    ]
    response = call_openai(
        client,
        messages=messages,
        response_format={"type": "json_object"},
        images=list(images_dir.glob("*.png"))
    )
    GPT_answers_path = Path(__file__).parent / "GPT_answers.json"
    save_json(json.loads(response), GPT_answers_path)

    # Create and send submission
    submission = {
        "task": getenv("TASK_10_TASK_NAME"),
        "apikey": getenv("AI_DEVS_3_API_KEY"),
        "answer": read_json(GPT_answers_path)
    }
    submission_file_path = Path(__file__).parent / "submission_file.json"
    save_json(submission, submission_file_path)
    send_json(getenv("TASK_10_SUBMISSION_URL"), submission_file_path)


if __name__ == "__main__":
    main()