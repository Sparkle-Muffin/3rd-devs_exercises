import zipfile
import os
import re
from pathlib import Path
from typing import Callable, Any
import string


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
    text = re.sub(r"\.{2,}", ".", text)  # Replace multiple dots with single
    text = re.sub(r"!{2,}", "!", text)  # Replace multiple exclamation marks with single
    text = re.sub(r"\?{2,}", "?", text)  # Replace multiple question marks with single
    text = re.sub(r"\n+", "\n\n", text)  # Replace multiple newlines with two newlines

    text = text.lower()  # Lowercase all text

    text = text.strip()  # Remove leading/trailing whitespace

    return text


def split_into_chunks(text: str) -> str:
    """
    Split text into logical chunks based on header structure.

    Analyzes markdown headers to create context-aware chunks. Each chunk
    includes the relevant header context to maintain semantic meaning.

    Args:
        text: Text with markdown headers to be split

    Returns:
        Text with chunks separated by double newlines, each chunk containing
        relevant header context
    """
    chunks = []
    headers_stack = []

    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip empty lines

        # Check if line is a header
        header_match = re.match(r"^(#+)\s+(.*)", line)
        if header_match:
            level = len(header_match.group(1))  # number of '#'
            header_text = header_match.group(2).strip()

            # Cut headers stack to current level
            headers_stack = headers_stack[: level - 1]
            headers_stack.append(header_text)
        else:
            # This is content -> create chunk
            context = " ".join(headers_stack)
            chunk = f"{context} {line}"
            chunks.append(chunk)

    text = "\n\n".join(chunks)

    return text


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
    # List docs files
    docs_files = os.listdir(input_dir)

    for file in docs_files:
        print(f"Processing: {file}")

        # Skip directories
        file_path = input_dir / file
        if file_path.is_dir():
            continue

        try:
            # Read the file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Apply comprehensive cleaning
            cleaned_content = preprocess_func(content)

            # Save the cleaned content to db_cleaned_up_dir
            output_path = output_dir / file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(cleaned_content)

            print(f"  ✓ Saved cleaned file to: {output_path}")
            print(
                f"  ✓ Original size: {len(content)} chars, Cleaned size: {len(cleaned_content)} chars"
            )

        except Exception as e:
            print(f"  ✗ Error processing {file}: {e}")


def main():
    # 0. Initialize
    task_path = Path(__file__).parent
    program_files_dir = task_path / "program_files"
    docs_unprocessed_dir = program_files_dir / "unprocessed"
    docs_preprocessed_dir = program_files_dir / "docs_preprocessed"
    docs_preprocessed_dir.mkdir(exist_ok=True)
    docs_cleaned_up_dir = docs_preprocessed_dir / "docs_cleaned_up"
    docs_cleaned_up_dir.mkdir(exist_ok=True)


    # 1. Clean up and unify structure of docs files
    preprocess_files(docs_unprocessed_dir, docs_cleaned_up_dir, clean_and_unify_text)


if __name__ == "__main__":
    main()