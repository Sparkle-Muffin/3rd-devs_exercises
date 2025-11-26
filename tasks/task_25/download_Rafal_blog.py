import sys
import os
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, str(os.getcwd()))
from common.websires_utils import download_website_as_markdown
from common.file_utils import save_txt_file


def main():
    # 0. Initialize
    load_dotenv()
    task_path = Path(__file__).parent
    program_files_dir = task_path / "program_files"
    blog_url = os.getenv("TASK_25_SOURCE_5_URL")
    blog_markdown_path = program_files_dir / "blog.md"


    # 1. Download the blog
    blog_markdown = download_website_as_markdown(blog_url)
    save_txt_file(blog_markdown, blog_markdown_path)


if __name__ == "__main__":
    main()