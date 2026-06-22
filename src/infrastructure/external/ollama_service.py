"""Ollama service for LLM integration."""

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

import requests

from src.shared.exceptions.infrastructure_exceptions import ExternalServiceException


class OllamaService:
    """Manage local Ollama instance and API calls."""
    
    def __init__(
        self,
        model: str = "qwen2.5-coder:7b-instruct",
        base_url: str = "http://127.0.0.1:11434",
        ollama_path: Optional[str] = None,
    ):
        self.model = model
        self.base_url = base_url
        self.ollama_path = ollama_path or "ollama"
        self._process: Optional[subprocess.Popen] = None
        self._started = False
    
    def start(self, timeout: int = 30) -> bool:
        """Start the Ollama server."""
        if self._started:
            return True
        
        try:
            self._process = subprocess.Popen(
                [self.ollama_path, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return self._wait_ready(timeout)
        except Exception as e:
            raise ExternalServiceException(f"Failed to start Ollama: {e}")
    
    def _wait_ready(self, timeout: int) -> bool:
        """Wait for Ollama to be ready."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
                if resp.status_code == 200:
                    self._started = True
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False
    
    def ensure_model(self) -> bool:
        """Ensure the required model is available."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = [m.get('name', '') for m in resp.json().get('models', [])]
                if any(self.model in m for m in models):
                    return True
            
            # Pull model
            resp = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model},
                timeout=300
            )
            return resp.status_code == 200
        except Exception as e:
            raise ExternalServiceException(f"Model check failed: {e}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "num_predict": kwargs.get("num_predict", 1024),
            }
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=kwargs.get("timeout", 30)
            )
            if resp.status_code == 200:
                return resp.json().get('response', '').strip()
        except Exception as e:
            raise ExternalServiceException(f"Generation error: {e}")
        return ""
    
    def generate_json(self, prompt: str, **kwargs) -> Optional[dict]:
        """Generate JSON response from Ollama."""
        response = self.generate(prompt, **kwargs)
        if not response:
            return None
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        return None
    
    def stop(self) -> None:
        """Stop the Ollama server."""
        if self._process:
            self._process.terminate()
            self._process.wait(timeout=5)
            self._started = False