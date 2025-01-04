from pathlib import Path
from common.file_utils import download_file, read_file_content, save_json
import os
from dotenv import load_dotenv
from common.openai_utils import OpenaiClient
from common.http_server import HTTPJSONServer
from common.ngrok_utils import NgrokTunnel

task_name = os.getenv("TASK_19_TASK_NAME")
task_path = Path(__file__).parent
openai_msg_handler = OpenaiClient(task_path)


def handle_map_request(request_data: dict) -> dict:
    # Example handler function
    return {"status": "success", "message": "Map data processed"}

def main():
    # 0. Initialize
    prompts_dir = task_path / "prompts"
    program_files_dir = task_path / "program_files"
    image_path = program_files_dir / "mapa_s04e04.png"
    map_description_path = program_files_dir / "map_description.json"

    # Initialize server
    server = HTTPJSONServer(host="localhost", port=8000)
    
    # Add routes
    server.add_route("/process-map", handle_map_request)
    
    # Start server
    server.start(use_thread=True)
    
    # Start ngrok tunnel
    ngrok_tunnel = NgrokTunnel()
    public_url = ngrok_tunnel.start(8000)
    
    print(f"Server is accessible at: {public_url}")
    
    try:
        # Keep the main thread running
        while True:
            input("Press Enter to stop the server...")
            break
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup
        server.stop()
        ngrok_tunnel.stop()


if __name__ == "__main__":
    main()