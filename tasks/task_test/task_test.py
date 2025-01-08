from pathlib import Path
from common.opencv_utils import split_text_blocks

task_path = Path(__file__).parent


def main():
    program_files_dir = task_path / "program_files"
    input_file = program_files_dir / "input_file.png"
    output_prefix = program_files_dir / "output_file"


    fragment_count = split_text_blocks(input_file, output_prefix, contour_min_width=200, contour_min_height=200)

    print(f"Generated {fragment_count} fragments with prefix '{output_prefix}'")

if __name__ == "__main__":
    main()