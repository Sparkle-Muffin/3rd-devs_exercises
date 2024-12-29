import requests
from bs4 import BeautifulSoup
import json
import logging
from pathlib import Path
import markdownify
from common.file_utils import read_file_content, save_txt_file
from common.openai_utils import OpenaiClient
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class WebsiteSearchAgent:
    def __init__(self, task_path):
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.openai_msg_handler = OpenaiClient(task_path)

    def fetch_page(self, url):
        """Fetch and parse a webpage."""       
        try:
            self.domain_url = url
            logging.info(f"Fetching page: {url}")
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        except requests.RequestException as e:
            logging.error(f"Error fetching page {url}: {e}")
            return None

    def extract_links_and_content(self, soup):
        """Extract links and main content from a webpage."""
        original_links = []
        full_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href != '/':
                original_links.append(href)
                if href.startswith('http'):
                    full_links.append(href)
                elif href.startswith('//'):
                    full_links.append('https:' + href)
                elif href.startswith('/'):
                    base_url = '/'.join(self.domain_url.split('/')[:3])  # Gets domain including protocol
                    full_links.append(base_url + href)
        # Add safety check for body
        body = soup.body if soup.body else soup
        content = markdownify.markdownify(str(body))
        
        # Replace original links with full links in content
        for original, full in zip(original_links, full_links):
            content = content.replace(original, full)

        return full_links, content

    def ask_llm(self, question, website_content, link_urls):
        """Query the LLM to extract the answer or next link."""
        prompt = read_file_content(self.prompts_dir / "answer_question.txt")
        question_and_website_content = f"question\n: {question}\n\nNEW PROMPT SECTION\nwebsite_content\n: {website_content}\n\nNEW PROMPT SECTION\nlink_urls\n: {link_urls}"
        messages = [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': question_and_website_content}
        ]
        response = self.openai_msg_handler.call_openai(messages, response_format={"type": "json_object"})
        return response
    
    def navigate_and_find_answers(self, website_url: str, questions: json):
        """Navigate the site and find answers for the given questions."""
        try:
            # Initialize questions and answers
            questions_and_answers = {question_id: {"question": question, "answer": ""} 
                                    for question_id, question in questions.items()}
            # Process each question
            for question_id, question_and_answer in questions_and_answers.items():
                question_text = question_and_answer["question"]
                logging.info(f"Processing question {question_id}: {question_text}")
                current_url = website_url
                website_properties = {"website_url": "", "link_urls": [], "content": ""}
                website_chain = []
                visited_pages = set()

                while True:
                    soup = self.fetch_page(current_url)
                    if not soup:
                        question_and_answer["answer"] = "Error during website parsing."
                        break                
                    link_urls, content = self.extract_links_and_content(soup)
                    website_properties["website_url"] = current_url
                    website_properties["link_urls"] = link_urls
                    website_properties["content"] = content
                    website_chain.append(website_properties)

                    # Filter out links that have already been visited
                    visited_pages.add(current_url)
                    valid_link_urls = [link for link in link_urls if link not in visited_pages]

                    # Ask the LLM for the answer or next link
                    llm_response = self.ask_llm(question_text, content, valid_link_urls)

                    # Answer found on the current page
                    if llm_response["status"] == "ANSWERED":
                        question_and_answer["answer"] = llm_response["answer"]
                        break
                    # Next link to visit
                    elif llm_response["status"] == "LINK":
                        current_url = llm_response["link"]
                    # No answer found, go back to the previous page
                    else:
                        website_chain.pop()
                        # If there is a previous page, go back to it
                        if website_chain != []:
                            current_url = website_chain[-1]["website_url"]
                        # No previous page, no answer found
                        else:
                            question_and_answer["answer"] = "No answer found."
                            break


            return questions_and_answers
        
        except Exception as e:
            logging.error(f"Execution failed: {e}")