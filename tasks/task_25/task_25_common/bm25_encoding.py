import os
from pathlib import Path
from typing import List
from tqdm import tqdm
from task_25_common.project_classes import SearchResult, BM25Config


def generate_bm25_encodings(input_dir: Path, encodings_db_path: str) -> None:
    """
    Generate BM25 encodings for text documents and save them to disk.
    
    Creates a BM25 model from text files in the input directory, tokenizes the corpus,
    and saves the model along with the corpus for later retrieval.
    
    Args:
        input_dir: Directory containing text files to encode
        encodings_db_path: Path where to save the BM25 model and corpus
    """
    import bm25s

    # Create your corpus here
    corpus = []
    for file in tqdm(os.listdir(input_dir), desc="Generating BM25 encodings"):
        with open(input_dir / file, 'r', encoding='utf-8') as f:
            text = f.read()
            corpus.append(text)

    # Tokenize the corpus and only keep the ids (faster and saves memory)
    corpus_tokens = bm25s.tokenize(corpus, stopwords="en")

    # Create the BM25 model and index the corpus
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)

    # You can save the arrays to a directory...
    retriever.save(encodings_db_path)

    # You can save the corpus along with the model
    retriever.save(encodings_db_path, corpus=corpus)


def get_top_k_bm25_encoding_results(query: str, encodings_db_path: str, db_chunks_number: int) -> List[SearchResult]:
    """
    Retrieve top-k results from BM25 model for a given query.
    
    Loads a pre-trained BM25 model, tokenizes the query, and returns the most
    relevant documents ranked by BM25 scores.
    
    Args:
        query: Search query string
        encodings_db_path: Path to the saved BM25 model and corpus
        db_chunks_number: Number of top results to return
        
    Returns:
        List of SearchResult objects containing document id, score, and text for each result
    """
    import bm25s

    retriever = bm25s.BM25.load(encodings_db_path, load_corpus=True)

    query = query.lower()
    query_tokens = bm25s.tokenize(query, return_ids=False)

    results, scores = retriever.retrieve(query_tokens, k=db_chunks_number)

    search_results = []
    for i in range(results.shape[1]):
        doc, score = results[0, i], scores[0, i]
        search_results.append(SearchResult(
            id=doc["id"],
            score=float(score),
            text=doc["text"]
        ))

    return search_results
