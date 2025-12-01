import asyncio
import time
import json
from typing import Dict, List, Optional, Any
from common.file_utils import save_json, save_txt_file

GEMINI_TIMEOUT_MS = 1_000_000  # 10 minutes

def ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")


async def run_gemini_process(args):
    # print(f"[{ts()}][gemini] Spawning: gemini {' '.join(args)}")
    print(f"[{ts()}][gemini] Spawning: gemini")

    # Start process
    process = await asyncio.create_subprocess_exec(
        "gemini",
        *args,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    out_buf = []
    err_buf = []

    async def read_stream(stream, buffer):
        """Read stream line-by-line and log previews."""
        while True:
            chunk = await stream.readline()
            if not chunk:
                break
            text = chunk.decode("utf-8", errors="replace")
            buffer.append(text)

    # Create reading tasks
    read_stdout = asyncio.create_task(read_stream(process.stdout, out_buf))
    read_stderr = asyncio.create_task(read_stream(process.stderr, err_buf))

    try:
        # Wait for process OR timeout
        await asyncio.wait_for(
            asyncio.gather(read_stdout, read_stderr, process.wait()),
            timeout=GEMINI_TIMEOUT_MS / 1000,
        )

        code = process.returncode

        print(f"[{ts()}][gemini] Process completed with code: {code}")
        stdout_str = "".join(out_buf).strip()
        print(f"[{ts()}][gemini] Output length: {len(stdout_str)} characters")
        print(f"[{ts()}][gemini] Error: {str(err_buf)}")

        return {
            "stdout": stdout_str,
            "stderr": str(err_buf),
            "code": code,
        }

    except asyncio.TimeoutError:
        print(f"[{ts()}][gemini] ⏰ Timeout after {GEMINI_TIMEOUT_MS}ms")
        process.kill()
        await process.wait()

        return {
            "stdout": "".join(out_buf).strip(),
            "stderr": str(err_buf) + " [timeout]",
            "code": 124,  # like JS example
        }

    except Exception as e:
        print(f"[{ts()}][gemini] ❌ Spawn error: {e}")
        return {
            "stdout": "".join(out_buf).strip(),
            "stderr": str(e),
            "code": -1,
        }


def extract_json_from_response(response: str) -> Dict[str, Any]:
    """Extract JSON object from response string that may contain text before/after JSON."""
    if not response:
        raise ValueError("Empty response")
    
    # First, try to parse the entire response as JSON
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # If that fails, try to find and extract JSON object from the string
    # Look for the first occurrence of { and find the matching }
    start_idx = response.find('{')
    if start_idx == -1:
        raise ValueError(f"No JSON object found in response: {response[:100]}...")
    
    # Find the matching closing brace by counting braces
    brace_count = 0
    end_idx = start_idx
    for i in range(start_idx, len(response)):
        if response[i] == '{':
            brace_count += 1
        elif response[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break
    
    if brace_count != 0:
        raise ValueError(f"Unbalanced braces in JSON response: {response[:100]}...")
    
    json_str = response[start_idx:end_idx]
    return json.loads(json_str)


class GeminiCLIClient:
    def __init__(self, base_dir):
        # Define query and response directories
        self.query_dir = base_dir / "gemini_queries"
        self.response_dir = base_dir / "gemini_responses"
        # Ensure directory exists
        self.query_dir.mkdir(parents=True, exist_ok=True)
        self.response_dir.mkdir(parents=True, exist_ok=True)

    def _get_next_file_number(self, directory):
        """Determine the next file number based on existing files."""
        files = list(directory.glob("*.txt")) + list(directory.glob("*.json"))
        return len(files) + 1

    async def call_gemini(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        yolo: Optional[bool] = False,
        output_format: Optional[str] = None
    ) -> str:

        args = []
        if yolo:
            args.append("--yolo")
        if model:
            args.append(f"--model")
            args.append(model)
        if output_format:
            args.append(f"--output-format")
            args.append(output_format)
        args.append("--prompt")

        messages_str = "\n".join([str(message) for message in messages])
        args.append(messages_str)

        process_result = await run_gemini_process(args)
        response = process_result.get("stdout", "")
        print(response)

        file_number = self._get_next_file_number(self.query_dir)
        query_path = self.query_dir / f"{file_number}_gemini_query.json"
        response_path = self.response_dir / f"{file_number}_gemini_response.json"

        save_json(messages, query_path)

        if output_format:
            if output_format == "json":
                response = json.loads(response.replace("```json", "").replace("```", ""))
                save_json(response, response_path)
            else:
                save_txt_file(response, response_path)
        else:
            save_txt_file(response, response_path)

        return response