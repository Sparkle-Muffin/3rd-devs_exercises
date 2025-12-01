from task_25_common.embeddings import generate_embeddings_and_metadata
from task_25_common.qdrant_api import upload_to_qdrant
from task_25_common.bm25_encoding import generate_bm25_encodings
from task_25_common.constants import QDRANT_COLLECTION_NAME, VECTOR_SIZE, BM25_ENCODINGS_DB_PATH
from pathlib import Path


def main():
    # 0. Initialize
    task_path = Path(__file__).parent
    program_files_dir = task_path / "program_files"
    text_chunks_dir = program_files_dir / "text_chunks"

    # 1. Create embeddings using SentenceTransformer
    embeddings_and_metadata = generate_embeddings_and_metadata(
        input_dir=text_chunks_dir
    )

    # 2. Upload content to Qdrant
    upload_to_qdrant(
        collection_name=QDRANT_COLLECTION_NAME,
        embeddings_and_metadata=embeddings_and_metadata,
        vector_size=VECTOR_SIZE,
    )

    # 3. Create BM25 encodings
    generate_bm25_encodings(
        input_dir=text_chunks_dir, encodings_db_path=BM25_ENCODINGS_DB_PATH
    )


if __name__ == "__main__":
    main()