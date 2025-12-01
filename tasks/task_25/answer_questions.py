import sys
import os
sys.path.insert(0, str(os.getcwd()))
from pathlib import Path
from common.file_utils import read_json, save_json, read_file_content
from preprocess_files import clean_and_unify_text
from task_25_common.project_classes import SearchType
from task_25_common.prompt_generation import get_chunks
from tqdm import tqdm
from typing import List
from common.gemini_utils import GeminiCLIClient, extract_json_from_response
from common.centrala_aidevs_utils import AidevsMessageHandler
import asyncio


async def main():
    # 0. Initialize
    task_name = os.getenv("TASK_25_TASK_NAME")
    task_path = Path(__file__).parent
    aidevs_msg_handler = AidevsMessageHandler(task_name=task_name, base_dir=task_path)
    gemini_msg_handler = GeminiCLIClient(base_dir=task_path)
    prompts_dir = task_path / "prompts"
    program_files_dir = task_path / "program_files"
    questions_path = program_files_dir / "questions.json"
    questions_and_chunks_path = program_files_dir / "questions_and_chunks.json"
    questions_and_answers_path = program_files_dir / "questions_and_answers.json"


    # 1. Get chunks
    questions = [question for question in read_json(questions_path)]
    questions_and_chunks = {question: [] for question in questions}
    for question in tqdm(questions, desc="Getting chunks"):
        # question_cleaned_up = clean_and_unify_text(question)
        chunks = get_chunks(question, 20, 10, search_type=SearchType.HYBRID)
        # chunks = get_chunks(question, 10, 10, search_type=SearchType.VECTOR)
        questions_and_chunks[question] = chunks

    save_json(questions_and_chunks, questions_and_chunks_path)


    def concatenate_chunks(chunks: List[str]) -> str:
        chunks = [f"chunk {i+1}:\n" + chunk for i, chunk in enumerate(chunks)]
        chunks = "\n\n".join(chunks)
        return chunks

    
    def create_answer_for_centrala(question_number, answer):
        answer_table = ["empty"] * 24
        answer_table[question_number] = answer
        return answer_table

    
    questions = read_json(questions_path)
    questions_and_chunks = read_json(questions_and_chunks_path)


    # 2. Answer the questions
    questions_and_answers = {question: "" for question in questions}
    for q_number, question in enumerate(questions):
        return_code = 1
        chunks = concatenate_chunks(questions_and_chunks[question])
        answer = None
        feedback = None
        all_previous_answers = []
        all_previous_feedbacks = []
        counter = 0
        while(return_code != 0):
            # 3. Ask Gemini to answer the question
            counter += 1
            system_prompt = read_file_content(prompts_dir / "answer_the_question.txt")
            system_prompt += f"\n\n//=============== THIS IS THE {counter} try ===============//:\n\n"
            if answer and feedback:
                all_previous_answers.append(answer)
                all_previous_feedbacks.append(feedback)
                system_prompt += f"\n\n//=============== YOUR PREVIOUS ANSWERS ===============//:\n\n"
                for i, answer in enumerate(all_previous_answers): 
                    system_prompt += f"//------------- From {i+1} try -------------//:\n\n"
                    system_prompt += f"{answer}\n\n"
                system_prompt += f"\n\n//=============== FEEDBACK ===============//:\n\n"
                for i, feedback in enumerate(all_previous_feedbacks):
                    system_prompt += f"//------------- From {i+1} try -------------//:\n\n"
                    system_prompt += f"{feedback}\n\n"
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': 
                f"//=============== QUESTION ===============//:\n\n{question}\n\n"
                f"//=============== CHUNKS ===============//:\n\n{chunks}"}
            ]
            query_result = await gemini_msg_handler.call_gemini(messages=messages, output_format="json")
            answer = extract_json_from_response(query_result.get('response'))
            answer = answer["answer"]


            # 4. Check answers in Centrala
            answer_for_centrala = create_answer_for_centrala(q_number, answer)
            feedback = aidevs_msg_handler.ask_centrala_aidevs(answer_for_centrala)
            feedback = feedback.get("ok")
            if feedback:
                return_code = 0
                questions_and_answers[question] = answer
            else:
                if counter < 11:
                    feedback = "Zła odpowiedź"
                else:
                    questions_and_answers[question] = "TBD"
                    continue

    save_json(questions_and_answers, questions_and_answers_path)


    # 5. Send answer to Aidevs
    questions_and_answers = read_json(questions_and_answers_path)
    answer_for_centrala = [value for value in questions_and_answers.values()]
    aidevs_msg_handler.ask_centrala_aidevs(answer_for_centrala)


if __name__ == "__main__":
    asyncio.run(main())