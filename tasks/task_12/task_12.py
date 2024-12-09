import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from tasks.common.send_json import send_json
from tasks.common.file_utils import save_txt_file, read_file_content, save_json, read_json, download_file, extract_file, download_website_source, process_audio_files, extract_text_from_translated_audio_files, download_files_from_website
from tasks.common.openai_utils import call_openai
from tasks.common.qdrant import ensure_qdrant_running
from qdrant_client.models import Filter, FieldCondition, MatchValue

from os import getenv
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from qdrant_client.models import PointStruct
import hashlib


# Function to generate text embeddings using 'text-embedding-ada-002'
def get_embedding(client, text, model="text-embedding-ada-002"):
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding


def main():
    # Initialize
    load_dotenv()
    openai_client = OpenAI()
    qdrant_client = QdrantClient(url="http://localhost:6333")

    # Download and extract files
    zip_path = download_file(getenv("TASK_12_DOWNLOAD_URL"), Path(__file__).parent)
    extract_dir = extract_file(zip_path)
    encrypted_zip_path = extract_dir / Path("weapons_tests.zip")
    weapons_tests_dir = extract_file(encrypted_zip_path, getenv("TASK_12_ZIP_PASSWORD"))
    weapons_tests_dir = weapons_tests_dir / Path("do-not-share")

    # Generate embeddings and payload (metadata)
    weapons_tests_files = []
    for file in weapons_tests_dir.iterdir():
        if file.is_file() and file.name.endswith(".txt"):
            file_name = file.name.replace(".txt", "")
            text = read_file_content(file)
            id = hashlib.md5(text.encode()).hexdigest()
            print(f"Generating embedding for {file_name}")
            vector = get_embedding(openai_client, text)
            weapons_tests_files.append({"file_name": file_name, 
                                        "text": text,
                                        "id": id,
                                        "vector": vector})

    # Ensure Qdrant is running
    ensure_qdrant_running()

    # Create collection 
    collection_name="weapons_tests"
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )

    # Upload files to Qdrant
    operation_info = qdrant_client.upsert(
        collection_name=collection_name,
        wait=True,
        points=[
            PointStruct(id=file["id"], 
                       vector=file["vector"], 
                       payload={"file_name": file["file_name"], 
                               "text": file["text"]})
            for file in weapons_tests_files
        ]
    )

    print(operation_info)

    # Search for the answer
    question="W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?"
    vector = get_embedding(openai_client, question)
    search_result = qdrant_client.query_points(
        collection_name=collection_name,
        query=vector,
        with_payload=True,
        limit=1
    ).points[0].payload["file_name"]

    print(search_result)

    # Create and send submission
    submission = {
        "task": getenv("TASK_12_TASK_NAME"),
        "apikey": getenv("AI_DEVS_3_API_KEY"),
        "answer": search_result.replace("_", "-")
    }
    submission_file_path = Path(__file__).parent / "submission_file.json"
    save_json(submission, submission_file_path)
    send_json(getenv("TASK_12_SUBMISSION_URL"), submission_file_path)


if __name__ == "__main__":
    main()