from common.constants import QDRANT_COLLECTION_NAME, BM25_ENCODINGS_DB_PATH
from common.embeddings import generate_query_embedding
from common.qdrant_api import search_answer_in_qdrant
from common.bm25_encoding import get_top_k_bm25_encoding_results
from common.reciprocal_rank_fusion import hybrid_search
from typing import Tuple
from common.models import PromptData, SearchType


def create_prompt(system_prompt: str, user_prompt: str, db_chunks_number: int, model_context_chunks_number: int, search_type: SearchType = SearchType.HYBRID) -> Tuple[str, str]:
    """
    Create a complete prompt by combining system prompt with retrieved context.
    
    Generates embeddings for the user query, retrieves relevant documents using both
    vector search (Qdrant) and text search (BM25), combines results using hybrid search,
    and appends the context to the system prompt.
    
    Args:
        system_prompt: Base system prompt for the model
        user_prompt: User's question or query
        db_chunks_number: Number of chunks to retrieve from the database
        model_context_chunks_number: Maximum number of chunks to include in the final context
        
    Returns:
        Tuple of (enhanced_system_prompt, user_prompt) where the system prompt
        contains the retrieved context
    """
    # Validate input parameters using Pydantic model
    prompt_data = PromptData(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        db_chunks_number=db_chunks_number,
        model_context_chunks_number=model_context_chunks_number
    )
    
    if search_type == SearchType.VECTOR or search_type == SearchType.HYBRID:
        query_embedding = generate_query_embedding(prompt_data.user_prompt)
        qdrant_results = search_answer_in_qdrant(
            collection_name=QDRANT_COLLECTION_NAME, 
            query_embedding=query_embedding, 
            db_chunks_number=prompt_data.db_chunks_number
        )

    if search_type == SearchType.BM25 or search_type == SearchType.HYBRID:  
        bm25_results = get_top_k_bm25_encoding_results(
            prompt_data.user_prompt, 
            BM25_ENCODINGS_DB_PATH, 
            db_chunks_number=prompt_data.db_chunks_number
        )

    if search_type == SearchType.HYBRID:
        hybrid_search_answers = hybrid_search(
            qdrant_results=qdrant_results, 
            bm25_results=bm25_results, 
            max_results=prompt_data.model_context_chunks_number
        )

    if search_type == SearchType.VECTOR:
        qdrant_results_text = [result.text for result in qdrant_results]
        context = "\n\n".join(qdrant_results_text)
    elif search_type == SearchType.BM25:
        bm25_results_text = [result.text for result in bm25_results]
        context = "\n\n".join(bm25_results_text)
    elif search_type == SearchType.HYBRID:
        context = "\n\n".join(hybrid_search_answers)

    enhanced_system_prompt = prompt_data.system_prompt + "\n\n" + context
    
    return enhanced_system_prompt
