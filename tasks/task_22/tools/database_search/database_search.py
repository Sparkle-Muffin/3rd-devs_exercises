from os import getenv
import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, parent_dir)
from common.file_utils import send_json


def send_query_to_db(query: str) -> dict:
    # Prepare database query
    db_query = {
        "task": "database",
        "apikey": getenv("AI_DEVS_3_API_KEY"),
        "query": query
    }

    # Send database query
    db_response = send_json(getenv("TASK_22_DB_API"), db_query)
    return db_response