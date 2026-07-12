"""Cache Miss Tracker for telemetry-only cache miss detection."""

import difflib
import json
import os
import time
from typing import Optional


class CacheMissTracker:
    """Track cache misses based on prompt similarity (telemetry only, no serving)."""

    def __init__(
        self,
        similarity_threshold: float = 0.75,
        telemetry_path: str = "playtest/telemetry/cache_miss.jsonl"
    ):
        self._threshold = similarity_threshold
        self._telemetry_path = telemetry_path
        self._last_prompt: Optional[str] = None

    def track_prompt(self, prompt: str, context: str = "behavior") -> bool:
        """Track a prompt and determine if it's a cache miss.
        
        Args:
            prompt: The prompt being sent to LLM
            context: The context (e.g., "behavior", "level_design")
            
        Returns:
            True if this is a cache miss (not similar enough to last prompt)
        """
        is_miss = True
        similarity = 0.0
        
        if self._last_prompt is not None:
            # Cap compared length to first 4000 chars to stay cheap
            compare_prompt = prompt[:4000] if len(prompt) > 4000 else prompt
            compare_last = self._last_prompt[:4000] if len(self._last_prompt) > 4000 else self._last_prompt
            similarity = difflib.SequenceMatcher(None, compare_last, compare_prompt).ratio()
            is_miss = similarity < self._threshold
        
        self._emit(context, similarity, is_miss, prompt)
        self._last_prompt = prompt
        return is_miss

    def _emit(self, context: str, similarity: float, is_miss: bool, prompt: str) -> None:
        """Emit telemetry entry for the prompt."""
        entry = {
            "event_type": "cache_miss",
            "timestamp": time.time(),
            "context": context,
            "similarity": round(similarity, 3),
            "is_miss": is_miss,
            "prompt_hash": hash(prompt) % (10**8)
        }
        os.makedirs(os.path.dirname(self._telemetry_path), exist_ok=True)
        with open(self._telemetry_path, "a") as f:
            f.write(json.dumps(entry) + "\n")