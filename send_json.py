import requests
import json

def send_json(url, filepath):
    """Send JSON file to a specified URL via POST request."""
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
        response = requests.post(url, json=data)
        response.raise_for_status()  # Raises an error for unsuccessful requests
        print("File sent successfully:", response.status_code)
        print(response.json())
        return response.json()  # Assuming the server returns a JSON response
    except requests.exceptions.RequestException as e:
        print("Error sending file:", e)
    except json.JSONDecodeError:
        print("Invalid JSON format in file:", filepath)
