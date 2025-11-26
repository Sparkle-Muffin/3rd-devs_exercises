import sys
import os
from pathlib import Path
from tqdm import tqdm
sys.path.insert(0, str(os.getcwd()))
from common.file_utils import save_txt_file
from common.opencv_utils import image_to_text


def main():
    # 0. Initialize
    task_path = Path(__file__).parent
    downloads_dir = task_path / "downloads"
    program_files_dir = task_path / "program_files"
    images_dir = downloads_dir / "zygfryd_notatnik"
    texts_dir = program_files_dir / "zygfryd_notatnik"
    texts_dir.mkdir(parents=True, exist_ok=True)

    # 1. Get images
    images = list(images_dir.glob("*.png"))

    # 2. Extract text from images and save to text files
    for image in tqdm(images, desc="Extracting text from images"):
        text = image_to_text(image)
        text_file = texts_dir / f"{image.stem}.txt"
        save_txt_file(text, text_file)


if __name__ == "__main__":
    main()