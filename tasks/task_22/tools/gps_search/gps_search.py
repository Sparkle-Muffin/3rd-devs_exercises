from os import getenv
import sys
import os

# Add the parent directory to Python path so we can import the common module
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, parent_dir)

from common.file_utils import send_json


def send_query_to_gps_search(userID: int) -> dict:
    # Prepare database query
    db_query = {
        "apikey": getenv("AI_DEVS_3_API_KEY"),
        "userID": userID
    }

    # Send database query
    db_response = send_json(getenv("TASK_22_GPS_API"), db_query)
    return db_response