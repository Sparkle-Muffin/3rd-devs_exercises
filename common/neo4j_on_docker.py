import subprocess
from pathlib import Path
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from typing import Dict
from os import getenv
import time
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable


def ensure_neo4j_running(volume_path: Path, import_dir: Path, container_name: str):
    """Ensure Neo4j container is running, creating it if needed."""
    # Check if container exists and get its status
    command = f"docker ps -a --filter name={container_name}"
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        if len(result.stdout.strip().splitlines()) > 1:
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:
                columns = line.split()
                if columns[-1] == container_name:
                    if 'Up' in line:
                        print("Neo4j container is already running")
                        return
                    container_id = columns[0]
                    subprocess.run(f"docker start {container_id}", shell=True, check=True, text=True)
                    print("Successfully started existing Neo4j Docker container")
                    return
            print("Container not found in the list")
        else:
            # Create directories if they don't exist
            volume_path.mkdir(parents=True, exist_ok=True)
            import_dir.mkdir(parents=True, exist_ok=True)
            # Set proper permissions (777 for testing, you might want to restrict this in production)
            try:
                subprocess.run(f"sudo chmod -R 777 {volume_path}", shell=True, check=True)
                subprocess.run(f"sudo chmod -R 777 {import_dir}", shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to set permissions: {e}")
                return
            
            command = (
                f"docker run -d -p 7474:7474 -p 7687:7687 "
                f"--env NEO4J_AUTH=neo4j/{getenv('NEO4J_PASSWORD')} "
                f"--name {container_name} "
                f"--env NEO4J_dbms_security_allow__csv__import__from__file__urls=true "
                f"-v {volume_path}:/data "
                f"-v {import_dir}:/var/lib/neo4j/import "
                f"neo4j:latest"
            )
            subprocess.run(command, shell=True, check=True, text=True)
            print("Successfully created and started new Neo4j Docker container")
    except subprocess.CalledProcessError as e:
        print(f"Failed to manage Neo4j Docker container: {e}")


def execute_neo4j_query(query: str, neo4j_container_name: str) -> Dict:
    """Execute a query on Neo4j database.
    
    Args:
        query: Neo4j query to execute
        neo4j_container_name: Name of the Neo4j container
        
    Returns:
        Dictionary containing query results or error message
    """
    # Neo4j default credentials
    uri = "neo4j://localhost:7687"
    username = "neo4j"
    password = getenv("NEO4J_PASSWORD")
    
    try:
        # Create a driver instance
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Verify connectivity
        driver.verify_connectivity()
        
        # Execute query in a session
        with driver.session() as session:
            result = session.run(query)
            
            # For path queries, collect all nodes in the path
            if "path" in query.lower():
                paths = []
                for record in result:
                    path = record["path"]
                    path_nodes = [node["username"] for node in path.nodes]
                    paths.append(", ".join(path_nodes))
                
                return {
                    "status": "success",
                    "paths": paths
                }
            
            # For other queries, return the summary as before
            summary = result.consume()
            return {
                "status": "success",
                "nodes_created": summary.counters.nodes_created,
                "relationships_created": summary.counters.relationships_created
            }
        
    except ServiceUnavailable:
        return {
            "status": "error",
            "message": f"Could not connect to Neo4j container '{neo4j_container_name}'. Make sure it's running."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    

def wait_for_neo4j(container_name: str, max_retries: int = 30, delay: int = 2) -> None:
    """Wait for Neo4j database to become available and ready to serve queries."""
    uri = "neo4j://localhost:7687"
    # Use the password from environment variables
    driver = GraphDatabase.driver(uri, auth=("neo4j", getenv("NEO4J_PASSWORD")))
    
    for attempt in range(max_retries):
        try:
            with driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
                print("Neo4j database is ready!")
                driver.close()
                return
        except ServiceUnavailable:
            print(f"Waiting for Neo4j to become available... (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
    
    driver.close()
    raise RuntimeError("Neo4j database failed to become available")