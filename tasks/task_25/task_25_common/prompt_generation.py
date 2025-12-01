from task_25_common.constants import QDRANT_COLLECTION_NAME, BM25_ENCODINGS_DB_PATH
from task_25_common.embeddings import generate_query_embedding
from task_25_common.qdrant_api import search_answer_in_qdrant
from task_25_common.bm25_encoding import get_top_k_bm25_encoding_results
from task_25_common.reciprocal_rank_fusion import hybrid_search
from typing import Tuple, List
from task_25_common.project_classes import PromptData, SearchType


def get_chunks(question: str, db_chunks_number: int, model_context_chunks_number: int, search_type: SearchType = SearchType.HYBRID) -> List[str]:
    
    if search_type == SearchType.VECTOR or search_type == SearchType.HYBRID:
        query_embedding = generate_query_embedding(question)
        qdrant_results = search_answer_in_qdrant(
            collection_name=QDRANT_COLLECTION_NAME, 
            query_embedding=query_embedding, 
            db_chunks_number=db_chunks_number
        )

    if search_type == SearchType.BM25 or search_type == SearchType.HYBRID:  
        bm25_results = get_top_k_bm25_encoding_results(
            question, 
            BM25_ENCODINGS_DB_PATH, 
            db_chunks_number=db_chunks_number
        )

    if search_type == SearchType.HYBRID:
        hybrid_search_answers = hybrid_search(
            qdrant_results=qdrant_results, 
            bm25_results=bm25_results, 
            max_results=model_context_chunks_number
        )

    if search_type == SearchType.VECTOR:
        qdrant_results_text = [result.text for result in qdrant_results]
        return qdrant_results_text
    elif search_type == SearchType.BM25:
        bm25_results_text = [result.text for result in bm25_results]
        return bm25_results_text
    elif search_type == SearchType.HYBRID:
        return hybrid_search_answers
