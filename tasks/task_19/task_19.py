from pathlib import Path
from common.file_utils import read_file_content, save_json
import os
from common.openai_utils import OpenaiClient
from common.centrala_aidevs_utils import AidevsMessageHandler
from common.http_server import HTTPJSONServer
from common.ngrok_utils import NgrokTunnel

task_name = os.getenv("TASK_19_TASK_NAME")
task_path = Path(__file__).parent
aidevs_msg_handler = AidevsMessageHandler(task_name, task_path)
openai_msg_handler = OpenaiClient(task_path)

# 0. Initialize
prompts_dir = task_path / "prompts"
program_files_dir = task_path / "program_files"
map_image_path = program_files_dir / "mapa_s04e04.png"
map_description_path = program_files_dir / "map_description.json"
map_array_path = program_files_dir / "map_array.json"
host = "localhost"
port = 8000 # The port number can be changed if the default port is already in use
drone_navigation_route = "/navigate-drone"
drone_navigation_url = ""
message_counter = 0


def handle_drone_navigation(request_data: dict) -> dict:

    global message_counter, drone_navigation_url
    print("handle_drone_navigation was called with data:", request_data)  # Debug print


    # 6. After 3 messages, ask AIdevs about the flag
    if message_counter == 3:
        message_counter = 0
        aidevs_msg_handler.ask_centrala_aidevs(drone_navigation_url)
        return
    else:   
        message_counter += 1


    # 7. Use OpenAI to extract map coordinates
    prompt = read_file_content(prompts_dir / "extract_coordinates.txt")
    map_array = read_file_content(map_array_path)
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': f"{map_array} \n {request_data['instruction']}"}
    ]
    response = openai_msg_handler.call_openai(messages, response_format={"type": "json_object"})
    map_element = response["map_element"]


    # 8. Use OpenAI to describe an image
    prompt = read_file_content(prompts_dir / "describe_image.txt")
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': f"{map_element}"}
    ]
    response = openai_msg_handler.call_openai(messages, [map_image_path], response_format={"type": "json_object"})
    image_description = response["image_description"]


    # 9. Send image description to AIdevs
    image_description_json = {"description": image_description}
    return image_description_json


def main():

    global drone_navigation_url

    # 1. Run HTTP server
    # Initialize server
    server = HTTPJSONServer(host=host, port=port)
    # Add routes
    server.add_route(drone_navigation_route, handle_drone_navigation)
    # Start server
    server.start(use_thread=True)
    

    # 2. Start ngrok tunnel
    ngrok_tunnel = NgrokTunnel()
    public_url = ngrok_tunnel.start(server.port)
    print(f"Server is accessible at: {public_url}")


    # 3. Use OpenAI to count rows and columns
    prompt = read_file_content(prompts_dir / "count_rows_and_columns.txt")
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': "Map is attached."}
    ]
    response = openai_msg_handler.call_openai(messages, [map_image_path], response_format={"type": "json_object"}, temperature=0.0)
    map_array = response["map_array"]
    save_json(map_array, map_array_path)
    

    # 4. Send server URL to AIdevs
    drone_navigation_url = f"{public_url}{drone_navigation_route}"
    aidevs_msg_handler.ask_centrala_aidevs(drone_navigation_url)


    # 5. Keep the main thread running
    try:
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