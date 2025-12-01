from task_25_common.constants import QDRANT_URL, QDRANT_PORT
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import subprocess
from pathlib import Path
from typing import List
from tqdm import tqdm
from task_25_common.project_classes import SearchResult, EmbeddingMetadata, QdrantConfig


def ensure_qdrant_running() -> None:
    """
    Ensure Qdrant container is running, creating it if needed.
    
    Checks if a Docker container named 'qdrant_container' exists and is running.
    If it exists but is stopped, starts it. If it doesn't exist, creates and runs
    a new container with persistent storage.
    """
    container_name = "qdrant_container"
    # Check if container exists and get its status
    command = f"docker ps -a --filter name={container_name}"
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        if len(result.stdout.strip().splitlines()) > 1:
            # Docker ps output contains multiple columns, we need to parse it carefully
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip the header line
                columns = line.split()
                if columns[-1] == container_name:
                    if 'Up' in line:
                        print("Qdrant container is already running")
                        return
                    # Container exists but is stopped - get container ID from first column
                    container_id = columns[0]
                    subprocess.run(f"docker start {container_id}", shell=True, check=True, text=True)
                    print("Successfully started existing Qdrant Docker container")
                    return
            # If we reach here, the container was not found
            print("Container not found in the list")
        else:
            # Container doesn't exist - create and run it
            qdrant_storage_dir = Path(__file__).parent.parent / "qdrant_storage"
            command = (
                f"docker run -d -p {QDRANT_PORT}:6333 "
                f"--name {container_name} "
                f"-v {qdrant_storage_dir}:/qdrant/storage "
                f"qdrant/qdrant"
            )
            subprocess.run(command, shell=True, check=True, text=True)
            print("Successfully created and started new Qdrant Docker container")
    except subprocess.CalledProcessError as e:
        print(f"Failed to manage Qdrant Docker container: {e}")


def upload_to_qdrant(collection_name: str, embeddings_and_metadata: List[EmbeddingMetadata], vector_size: int) -> None:
    """
    Upload embeddings and metadata to Qdrant vector database.
    
    Ensures Qdrant is running, creates a new collection with the specified vector size,
    and uploads all embeddings with their associated metadata as points.
    
    Args:
        collection_name: Name of the collection to create/upload to
        embeddings_and_metadata: List of EmbeddingMetadata objects containing id, vector, and text
        vector_size: Dimension of the embedding vectors
    """
    ensure_qdrant_running()

    # Create client
    qdrant_client = QdrantClient(url=QDRANT_URL)

    # Create collection 
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )

    # Upload files to Qdrant
    operation_info = qdrant_client.upsert(
        collection_name=collection_name,
        wait=True,
        points=[
            PointStruct(id=metadata.id, 
                       vector=metadata.vector, 
                       payload={"text": metadata.text})
            for metadata in tqdm(embeddings_and_metadata, desc="Uploading to Qdrant")
        ]
    )


def search_answer_in_qdrant(collection_name: str, query_embedding: List[float], db_chunks_number: int) -> List[SearchResult]:
    """
    Search for similar vectors in Qdrant collection using cosine similarity.
    
    Performs a vector similarity search in the specified collection and returns
    the top-k most similar documents with their scores and text content.
    
    Args:
        collection_name: Name of the collection to search in
        query_embedding: Query vector to search for
        db_chunks_number: Number of top results to return
        
    Returns:
        List of SearchResult objects containing document id, score, and text for each result
    """
    ensure_qdrant_running()

    # Create client
    qdrant_client = QdrantClient(url=QDRANT_URL)

    search_result = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_embedding,
        with_payload=True,
        limit=db_chunks_number
    )

    search_results = []
    for point in search_result.points:
        search_results.append(SearchResult(
            id=point.id,
            score=float(point.score),
            text=point.payload["text"]
        ))

    return search_results
