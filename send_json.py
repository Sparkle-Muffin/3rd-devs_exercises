import requests
import json

def send_json(url, filepath):
    """Send JSON file to a specified URL via POST request."""
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
        response = requests.post(url, json=data)
        print("Response status code:", response.status_code)
        
        # Get and format the response
        try:
            response_data = response.json()
            print("\nServer Response:")
            print(json.dumps(response_data, indent=2))  # Pretty print full JSON response
        except json.JSONDecodeError:
            print("\nServer Response (raw):")
            print(response.text)  # Print raw response if not JSON
            
    except json.JSONDecodeError:
        print("Invalid JSON format in file:", filepath)
    except requests.exceptions.RequestException as e:
        print("Error sending file:", e)
