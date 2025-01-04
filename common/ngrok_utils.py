from pyngrok import ngrok
import logging
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv

class NgrokTunnel:
    def __init__(self):
        self.tunnel = None
        self.logger = logging.getLogger(__name__)
        load_dotenv()  # Load environment variables from .env

    def _configure_auth_token(self) -> None:
        """Configure ngrok auth token if not already set"""
        ngrok_dir = Path.home() / ".ngrok2"
        config_path = ngrok_dir / "ngrok.yml"

        # Check if config file exists and contains auth token
        if config_path.exists():
            with open(config_path, 'r') as f:
                if 'authtoken:' in f.read():
                    self.logger.debug("Ngrok auth token already configured")
                    return

        # Configure auth token
        auth_token = os.getenv('NGROK_AUTH_TOKEN')
        if not auth_token:
            raise ValueError("NGROK_AUTH_TOKEN not found in .env file")

        try:
            ngrok.set_auth_token(auth_token)
            self.logger.info("Ngrok auth token configured successfully")
        except Exception as e:
            self.logger.error(f"Failed to configure ngrok auth token: {str(e)}")
            raise

    def start(self, port: int) -> str:
        """
        Start ngrok tunnel for the specified port
        Returns the public URL
        """
        try:
            self._configure_auth_token()
            self.tunnel = ngrok.connect(port)
            public_url = self.tunnel.public_url
            self.logger.info(f"Ngrok tunnel established at: {public_url}")
            return public_url
        except Exception as e:
            self.logger.error(f"Failed to start ngrok tunnel: {str(e)}")
            raise

    def stop(self):
        """Stop the ngrok tunnel"""
        if self.tunnel:
            ngrok.disconnect(self.tunnel.public_url)
            self.logger.info("Ngrok tunnel closed") 

            