import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from tasks.common.send_json import send_json
from tasks.common.file_utils import save_json, read_json, copy_files_to_directory

from os import getenv
from dotenv import load_dotenv
from pathlib import Path
from tasks.common.neo4j_on_docker import ensure_neo4j_running, execute_neo4j_query, wait_for_neo4j
import csv
from typing import List, Dict


def json_to_csv(json_path: Path, output_path: Path) -> None:
    """Convert a JSON file to CSV format with proper database formatting.
    
    Args:
        json_path: Path to the input JSON file
        output_path: Path where the CSV file will be saved
    """
    # Read JSON data
    data = read_json(json_path)
    
    if not data or not isinstance(data, dict) or 'reply' not in data:
        raise ValueError("Invalid JSON data format")
    
    data = data['reply']
    
    # Get headers from the first item
    headers = list(data[0].keys())
    
    # Write to CSV with proper quoting
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        # Write headers without quotes
        writer.writerow(headers)
        # Write data with proper quoting
        for row in data:
            writer.writerow([
                row[key] for key in headers
            ])


def main():
    # Initialize
    load_dotenv()

    # Prepare database query
    query_users = "SELECT * FROM users"
    db_query_users = {
        "task": "database",
        "apikey": getenv("AI_DEVS_3_API_KEY"),
        "query": query_users
    }

    # Save database query
    db_query_users_path = Path(__file__).parent / "db_query_users.json"
    save_json(db_query_users, db_query_users_path)

    # Send database query
    db_response_users = send_json(getenv("TASK_15_DATABASE_API"), db_query_users_path)

    # Save database response
    db_response_users_path = Path(__file__).parent / "db_response_users.json"
    save_json(db_response_users, db_response_users_path)
    
    # Convert users JSON to CSV
    users_file_name = "users.csv"
    users_csv_path = Path(__file__).parent / users_file_name
    json_to_csv(db_response_users_path, users_csv_path)


    # Prepare database query
    query_connections = "SELECT * FROM connections"
    db_query_connections = {
        "task": "database",
        "apikey": getenv("AI_DEVS_3_API_KEY"),
        "query": query_connections
    }

    # Save database query
    db_query_connections_path = Path(__file__).parent / "db_query_connections.json"
    save_json(db_query_connections, db_query_connections_path)

    # Send database query
    db_response_connections = send_json(getenv("TASK_15_DATABASE_API"), db_query_connections_path)

    # Save database response
    db_response_connections_path = Path(__file__).parent / "db_response_connections.json"
    save_json(db_response_connections, db_response_connections_path)
    
    # Convert connections JSON to CSV
    connections_file_name = "connections.csv"
    connections_csv_path = Path(__file__).parent / connections_file_name
    json_to_csv(db_response_connections_path, connections_csv_path)

    # Prepare Neo4j database
    neo4j_container_name = "task_15_neo4j"
    neo4j_volume_path = Path.home() / "neo4j_databases" / neo4j_container_name / "neo4j/data"
    neo4j_import_dir = Path.home() / "neo4j_databases" / neo4j_container_name / "neo4j_import"

    # Copy CSV files to Neo4j import directory
    files_to_copy = [users_csv_path, connections_csv_path]
    copy_files_to_directory(files_to_copy, neo4j_import_dir)

    # Run Neo4j database
    ensure_neo4j_running(neo4j_volume_path, neo4j_import_dir, neo4j_container_name)
    
    # Wait for Neo4j to become available
    wait_for_neo4j(neo4j_container_name)

    # Load users table to Neo4j database
    neo4j_query = f"LOAD CSV WITH HEADERS FROM 'file:///{users_file_name}' AS row \
                    CREATE (:User {{ \
                        id: toInteger(row.id), \
                        username: row.username, \
                        access_level: row.access_level, \
                        is_active: toBoolean(toInteger(row.is_active)), \
                        lastlog: date(row.lastlog) \
                    }})"
    # Execute the query
    result = execute_neo4j_query(neo4j_query, neo4j_container_name)
    print(f"Neo4j query result: {result}")

    # Load connections table to Neo4j database and create relationships
    neo4j_query = f"LOAD CSV WITH HEADERS FROM 'file:///{connections_file_name}' AS row \
                    MATCH (u1:User {{id: toInteger(row.user1_id)}}), \
                          (u2:User {{id: toInteger(row.user2_id)}}) \
                    CREATE (u1)-[:KNOWS]->(u2)"
    # Execute the query
    result = execute_neo4j_query(neo4j_query, neo4j_container_name)
    print(f"Neo4j query result: {result}")

    # Load connections table to Neo4j database and create relationships
    neo4j_query = "MATCH path = shortestPath((u1:User {username: 'Rafał'})-[*]->(u2:User {username: 'Barbara'})) \
                    RETURN path"
    # Execute the query
    result = execute_neo4j_query(neo4j_query, neo4j_container_name)
    print(f"Neo4j query result: {result}")

    # Create and send submission
    submission = {
        "task": getenv("TASK_15_TASK_NAME"),
        "apikey": getenv("AI_DEVS_3_API_KEY"),
        "answer": result["paths"][0]
    }
    submission_file_path = Path(__file__).parent / "submission_file.json"
    save_json(submission, submission_file_path)
    send_json(getenv("TASK_15_SUBMISSION_URL"), submission_file_path)


if __name__ == "__main__":
    main()