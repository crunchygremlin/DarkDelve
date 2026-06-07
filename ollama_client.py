"""
Ollama Local LLM Integration
Uses local Ollama instance with qwen2.5-coder for content generation
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class OllamaModel(Enum):
    QWEN_CODER = "qwen2.5-coder:7b-instruct"
    LLAMA2 = "llama2"
    MISTRAL = "mistral"


@dataclass
class OllamaConfig:
    """Configuration for Ollama connection"""
    host: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:7b-instruct"
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    num_predict: int = 512  # Max tokens (conservative for 8k context)
    repeat_penalty: float = 1.1
    timeout: int = 60


class OllamaClient:
    """Client for local Ollama LLM"""
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self.api_url = f"{self.config.host}/api/generate"
        self.cache: Dict[str, str] = {}
    
    def is_available(self) -> bool:
        """Check if Ollama is running and model is loaded"""
        try:
            response = requests.get(
                f"{self.config.host}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                models = [m.get('name', '') for m in data.get('models', [])]
                return any(self.config.model in m for m in models)
        except:
            pass
        return False
    
    def generate(
        self,
        prompt: str,
        cache_key: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """
        Generate response from Ollama
        
        Args:
            prompt: The prompt to send
            cache_key: Optional key for caching results
            stream: Whether to stream response
        
        Returns:
            Generated text response
        """
        # Check cache
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "stream": stream,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "num_predict": self.config.num_predict,
                "repeat_penalty": self.config.repeat_penalty,
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('response', '').strip()
                
                # Cache result
                if cache_key:
                    self.cache[cache_key] = text
                
                return text
            else:
                return f"Error: {response.status_code}"
        except requests.exceptions.Timeout:
            return "Error: Ollama request timed out (model may be loading)"
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Is it running? (http://localhost:11434)"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_json(
        self,
        prompt: str,
        cache_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate JSON response from Ollama
        
        Args:
            prompt: The prompt to send
            cache_key: Optional key for caching results
        
        Returns:
            Parsed JSON response or None on error
        """
        response = self.generate(prompt, cache_key)
        
        if response.startswith("Error"):
            return None
        
        try:
            # Try to extract JSON from response
            # Ollama might include extra text, so find JSON block
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return None
    
    def clear_cache(self) -> None:
        """Clear the response cache"""
        self.cache.clear()


# Global instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client(config: Optional[OllamaConfig] = None) -> OllamaClient:
    """Get or create the Ollama client"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient(config)
    return _ollama_client


def check_ollama_status() -> Dict[str, Any]:
    """Check Ollama status and model availability"""
    client = get_ollama_client()
    
    status = {
        "available": client.is_available(),
        "host": client.config.host,
        "model": client.config.model,
        "context_limit": 8192,
        "max_tokens": client.config.num_predict,
    }
    
    if not status["available"]:
        status["warning"] = (
            "Ollama not found. Start with: "
            "ollama run qwen2.5-coder:7b-instruct"
        )
    
    return status
