import zipfile
import os
import re
from pathlib import Path
from typing import Callable, Any
import string
import math


MAX_CHUNK_LENGTH = 350


def count_text_elements(text: str) -> int:
    if not text:
        return 0
    
    # Count words (sequences of letters, including contractions and hyphenated words)
    # This pattern matches words that contain at least one letter
    word_pattern = r'\b[a-zA-Z]+(?:[\'-][a-zA-Z]+)*\b'
    words = re.findall(word_pattern, text)
    word_count = len(words)
    
    # Count numbers (integers and decimals, including negative numbers)
    # This pattern matches integers and decimal numbers
    number_pattern = r'-?\d+\.?\d*'
    numbers = re.findall(number_pattern, text)
    number_count = len(numbers)
    
    # Count punctuation marks
    # Get all punctuation characters from string module and count them in text
    punctuation_chars = set(string.punctuation)
    punctuation_count = sum(1 for char in text if char in punctuation_chars)
    
    return word_count + number_count + punctuation_count


def clean_and_unify_text(text: str) -> str:
    """
    Comprehensive text cleaning for optimal RAG embeddings.

    Preserves logical structure and section divisions while cleaning formatting.
    Removes URLs, markdown syntax, excessive punctuation, and normalizes text.

    Args:
        text: Raw text to be cleaned

    Returns:
        Cleaned and normalized text suitable for embedding generation
    """
    # Remove URLs and file references (enhanced pattern)
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+|ftp://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+|file:///.[^\s<>"{}|\\^`\[\]]+'
    text = re.sub(url_pattern, "", text)

    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # Remove markdown links
    text = re.sub(r"\*", "", text)  # Remove markdown bold
    text = re.sub(r"\|", "", text)  # Remove markdown tables

    # Remove excessive punctuation
    # text = re.sub(r"\.{2,}", ".", text)  # Replace multiple dots with single
    text = re.sub(r"!{2,}", "!", text)  # Replace multiple exclamation marks with single
    text = re.sub(r"\?{2,}", "?", text)  # Replace multiple question marks with single
    text = re.sub(r"\n{2,}", "\n\n", text)  # Replace multiple newlines with two newlines

    # text = text.lower()  # Lowercase all text

    text = text.strip()  # Remove leading/trailing whitespace

    return text


def split_into_chunks(text: str) -> str:
    """
    Split text into logical chunks based on header structure and length limits.

    Args:
        text: Text with markdown headers to be split

    Returns:
        Text with chunks separated by double newlines, each chunk containing
        relevant header context
    """

    def split_text_with_limit(text_to_split: str, context: str = "") -> list[str]:
        if not text_to_split.strip():
            return []

        normalized_text = text_to_split.strip()
        if not normalized_text:
            return []

        # Count context length if provided
        context_len = count_text_elements(context) if context else 0
        available_len = MAX_CHUNK_LENGTH - context_len - (1 if context else 0)  # -1 for space
        
        if count_text_elements(normalized_text) <= available_len:
            if context:
                return [f"{context} {normalized_text}".strip()]
            return [normalized_text]

        sentences = re.split(r"(?<=[.!?])\s+", normalized_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            if context:
                return [f"{context} {normalized_text}".strip()]
            return [normalized_text]

        # Calculate total length and estimate number of chunks needed
        sentence_lengths = [count_text_elements(s) for s in sentences]
        total_len = sum(sentence_lengths)
        num_chunks = max(1, math.ceil(total_len / available_len))
        target_chunk_len = max(1, total_len // num_chunks)

        chunks_list: list[str] = []
        current_sentences: list[str] = []
        current_len = 0
        length_consumed = 0

        for sentence, sentence_len in zip(sentences, sentence_lengths):
            # If adding this sentence would exceed limit, finalize current chunk
            if current_sentences and current_len + sentence_len > available_len:
                chunk_text = " ".join(current_sentences).strip()
                if context:
                    chunks_list.append(f"{context} {chunk_text}".strip())
                else:
                    chunks_list.append(chunk_text)
                current_sentences = [sentence]
                current_len = sentence_len
                length_consumed += sentence_len
                # Recalculate target for remaining chunks
                remaining_len = total_len - length_consumed
                remaining_chunks = num_chunks - len(chunks_list)
                if remaining_chunks > 0:
                    target_chunk_len = max(1, remaining_len // remaining_chunks)
                continue

            current_sentences.append(sentence)
            current_len += sentence_len
            length_consumed += sentence_len

            # If we've reached target length and there's more to process, finalize chunk
            remaining_len = total_len - length_consumed
            remaining_chunks = num_chunks - len(chunks_list)
            if (
                current_len >= target_chunk_len
                and remaining_len > 0
                and remaining_chunks > 1
            ):
                chunk_text = " ".join(current_sentences).strip()
                if context:
                    chunks_list.append(f"{context} {chunk_text}".strip())
                else:
                    chunks_list.append(chunk_text)
                current_sentences = []
                current_len = 0
                if remaining_chunks > 1:
                    target_chunk_len = max(1, remaining_len // remaining_chunks)

        if current_sentences:
            chunk_text = " ".join(current_sentences).strip()
            if context:
                chunks_list.append(f"{context} {chunk_text}".strip())
            else:
                chunks_list.append(chunk_text)

        return chunks_list

    if not text or not text.strip():
        return ""

    header_regex = re.compile(r"^(#+)\s+(.*)", re.MULTILINE)
    if not header_regex.search(text):
        normalized = re.sub(r"\n+", "\n", text.strip())
        limited_chunks = split_text_with_limit(normalized)
        return "\n\n".join(f"@ {chunk}" for chunk in limited_chunks)

    chunks: list[str] = []
    headers_stack: list[str] = []
    current_content: list[str] = []

    def flush_current_content() -> None:
        nonlocal current_content
        if not current_content:
            return

        paragraph_text = "\n".join(current_content).strip()
        paragraph_text = re.sub(r"\n+", "\n", paragraph_text)
        current_content = []
        if not paragraph_text:
            return

        context = " ".join(headers_stack).strip()
        chunks.extend(split_text_with_limit(paragraph_text, context))

    for raw_line in text.splitlines():
        stripped_line = raw_line.strip()
        header_match = re.match(r"^(#+)\s+(.*)", stripped_line)

        if header_match:
            flush_current_content()
            level = len(header_match.group(1))
            header_text = header_match.group(2).strip()
            headers_stack = headers_stack[: level - 1]
            headers_stack.append(header_text)
            continue

        if stripped_line:
            current_content.append(stripped_line)
        else:
            if current_content and current_content[-1] != "":
                current_content.append("")

    flush_current_content()

    return "\n\n".join(f"@ {chunk}" for chunk in chunks)


def preprocess_files(
    input_dir: Path, output_dir: Path, preprocess_func: Callable[[str], str]
) -> None:
    """
    Process multiple files using a specified preprocessing function.

    Reads all files from the input directory, applies the preprocessing function
    to each file's content, and saves the processed results to the output directory.
    Skips directories and handles errors gracefully.

    Args:
        input_dir: Directory containing files to process
        output_dir: Directory where processed files should be saved
        preprocess_func: Function to apply to each file's content
    """
    # Walk recursively to cover nested content
    for file_path in input_dir.rglob("*"):
        if file_path.is_dir():
            continue

        relative_path = file_path.relative_to(input_dir)
        print(f"Processing: {relative_path}")

        try:
            # Read the file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Apply comprehensive cleaning
            cleaned_content = preprocess_func(content)

            # Save the cleaned content to mirror the relative structure
            output_path = output_dir / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(cleaned_content)

            print(f"  ✓ Saved cleaned file to: {output_path}")
            print(
                f"  ✓ Original size: {len(content)} chars, Cleaned size: {len(cleaned_content)} chars"
            )

        except Exception as e:
            print(f"  ✗ Error processing {relative_path}: {e}")


def create_chunk_files(input_dir: Path, output_dir: Path) -> None:
    """
    Create individual text chunk files for embedding and BM25 encoding.

    Args:
        input_dir: Directory containing files to split into chunks
        output_dir: Directory where chunk files should be saved
    """
    # Global counter for chunk numbering
    chunk_counter = 0
    
    # Walk recursively to cover nested content
    for file_path in input_dir.rglob("*"):
        if file_path.is_dir():
            continue
        
        relative_path = file_path.relative_to(input_dir)
        print(f"Processing: {relative_path}")
        
        try:
            # Read the file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Split content into chunks (chunks are separated by "\n\n" and start with "@ ")
            chunks = [chunk.strip() for chunk in content.split("\n\n") if chunk.strip().startswith("@ ")]
            
            if not chunks:
                print(f"  ⚠ No chunks found in {relative_path}")
                continue
            
            # Create a separate file for each chunk
            for chunk in chunks:
                # Remove "@ " from the beginning of the chunk
                if chunk.startswith("@ "):
                    chunk = chunk[2:]
                
                chunk_filename = f"{chunk_counter}.txt"
                chunk_path = output_dir / chunk_filename
                
                with open(chunk_path, "w", encoding="utf-8") as f:
                    f.write(chunk)
                
                print(f"  ✓ Created chunk {chunk_counter}: {chunk_path}")
                chunk_counter += 1
            
            print(f"  ✓ Created {len(chunks)} chunk(s) from {relative_path}")
            
        except Exception as e:
            print(f"  ✗ Error processing {relative_path}: {e}")
    
    print(f"\n✓ Total chunks created: {chunk_counter}")



def main():
    # 0. Initialize
    task_path = Path(__file__).parent
    program_files_dir = task_path / "program_files"
    docs_unprocessed_dir = program_files_dir / "unprocessed"
    docs_preprocessed_dir = program_files_dir / "docs_preprocessed"
    docs_preprocessed_dir.mkdir(exist_ok=True)
    docs_cleaned_up_dir = docs_preprocessed_dir / "docs_cleaned_up"
    docs_cleaned_up_dir.mkdir(exist_ok=True)
    docs_divided_into_chunks_dir = docs_preprocessed_dir / "docs_divided_into_chunks"
    docs_divided_into_chunks_dir.mkdir(exist_ok=True)
    text_chunks_dir = program_files_dir / "text_chunks"
    text_chunks_dir.mkdir(exist_ok=True)

    # 1. Clean up and unify structure of docs files
    preprocess_files(docs_unprocessed_dir, docs_cleaned_up_dir, clean_and_unify_text)

    # 2. Split docs into chunks
    preprocess_files(docs_cleaned_up_dir, docs_divided_into_chunks_dir, split_into_chunks)

    # 3. Create chunk files
    create_chunk_files(docs_divided_into_chunks_dir, text_chunks_dir)


if __name__ == "__main__":
    main()