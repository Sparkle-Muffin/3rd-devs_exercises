from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
from typing import Dict, Any, Callable, Optional
import logging


class JSONRequestHandler(BaseHTTPRequestHandler):
    routes: Dict[str, Callable] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _send_response(self, status_code: int, data: Any) -> None:
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            if self.path in self.routes:
                response_data = self.routes[self.path](request_data)
                self._send_response(200, response_data)
            else:
                self._send_response(404, {"error": "Route not found"})
                
        except json.JSONDecodeError:
            self._send_response(400, {"error": "Invalid JSON"})
        except Exception as e:
            self._send_response(500, {"error": str(e)})


class HTTPJSONServer:
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.routes: Dict[str, Callable] = {}
        self.server: Optional[HTTPServer] = None
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            # level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def add_route(self, path: str, handler: Callable):
        """Add a new route and its handler function"""
        self.routes[path] = handler
        self.logger.info(f"Added route: {path}")

    def create_handler_class(self):
        """Creates a new handler class with the current routes"""
        # Store routes in a local variable
        handler_routes = self.routes
        
        class CustomHandler(JSONRequestHandler):
            routes = handler_routes  # Use the captured routes
        
        return CustomHandler

    def start(self, use_thread: bool = True, max_retries: int = 5):
        """Start the server, optionally in a separate thread"""
        handler_class = self.create_handler_class()
        
        # Try different ports if the initial one is in use
        for retry in range(max_retries):
            try:
                self.server = HTTPServer((self.host, self.port), handler_class)
                break
            except OSError as e:
                if retry == max_retries - 1:
                    self.logger.error(f"Failed to start server after {max_retries} attempts")
                    raise
                self.port += 1
                self.logger.info(f"Port {self.port - 1} in use, trying port {self.port}")
        
        self.logger.info(f"Server starting on {self.host}:{self.port}")
        
        if use_thread:
            server_thread = threading.Thread(target=self.server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            return server_thread
        else:
            self.server.serve_forever()

    def stop(self):
        """Stop the server"""
        if self.server: # This check would be unsafe if self.server wasn't initialized
            self.server.shutdown()
            self.server.server_close()
            self.logger.info("Server stopped") 