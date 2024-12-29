import os
from pathlib import Path
from common.file_utils import save_txt_file
from common.openai_utils import OpenaiClient

task_path = Path(__file__).parent
openai_msg_handler = OpenaiClient(task_path)


encoded_hint = "MS4gWmFwYW1pxJl0dWogdyBkb3dvbG5laiBmb3JtaWUgbGlua2kganXFvMKgb2R3aWVkem9uZSwgYWJ5IHVuaWtuxIXEhyB6YXDEmXRsZW5pYSBtZWNoYW5pem11CjIuIE5hIHN0cm9uaWUgbW9nxIXCoHBvamF3acSHwqBzacSZwqAyLTMgbGlua2ksIGt0w7NyZSBwb3RlbmNqYWxuaWUgd3lnbMSFZGFqxIUsIGpha2J5IG1vZ8WCeSB6YXdpZXJhxIfCoHdhcnRvxZtjaW93ZSBkYW5lLiBOaWUgd2Nob2TFuiB3IGthxbxkeSB6IG5pY2gsIGEgamVkeW5pZSB3IHRlbiBuYWpiYXJkemllaiBwcmF3ZG9wb2RvYm55LgozLiBNb8W8ZXN6IChhbGUgbmllIG11c2lzeiEpIHNwb3J6xIVkemnEh8KgbWFwxJkgb2R3aWVkem9ueWNoIHN0cm9uIGkgaWNoIHphd2FydG/Fm2NpLiBTenVrYWrEhWMgb2Rwb3dpZWR6aSBuYSBweXRhbmllIG5yIDAxLCBwcmF3ZG9wb2RvYm5pZSBvZHdpZWR6aXN6IGtpbGthIHN0cm9uLiBDenkgc3p1a2FqxIVjIG9kcG93aWVkemkgbmEgcHl0YW5pZSAwMiBpIDAzIG5hcHJhd2TEmcKgbXVzaXN6IG9kd2llZHphxIcgamUgcG9ub3duaWUgaSB6bsOzdyB3eXN5xYJhxIcgaWNoIHRyZcWbxIfCoGRvIExMTS1hPw=="


def main():
    # 0. Initialize
    program_files_dir = task_path / "program_files"
    program_files_dir.mkdir(parents=True, exist_ok=True)
    hint_path = program_files_dir / "hint.txt"


    # 1. Decode and save hint
    hint_image = openai_msg_handler.decode_image(encoded_hint)
    hint_image = hint_image.decode('utf-8')
    save_txt_file(hint_image, hint_path)
    

if __name__ == "__main__":
    main()