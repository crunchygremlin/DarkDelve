"""
LLM Map Generator - Generate dungeon maps from LLM descriptions.

Uses the existing async queue pattern (llm_worker_func) to generate
structured map data from natural language descriptions.
"""

import json
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from src.domain.services.map_builder import MapBuilder


# JSON schema expected from LLM for map generation
MAP_JSON_SCHEMA = """
{
  "width": 60,
  "height": 40,
  "rooms": [
    {"x": 5, "y": 5, "width": 10, "height": 8, "room_id": "entrance"}
  ],
  "corridors": [
    {"start": [15, 9], "end": [25, 9], "width": 1}
  ],
  "stairs": [
    {"x": 7, "y": 7, "direction": "up"},
    {"x": 30, "y": 15, "direction": "down"}
  ],
  "entities": [
    {"x": 10, "y": 10, "type": "goblin", "name": "Goblin Scout"}
  ]
}
"""


class LLMMapGenerator:
    """
    Generate dungeon maps from LLM text descriptions.

    Uses the existing llm_worker_func for non-blocking operation.
    Falls back to procedural generation if LLM is unavailable.
    """

    def __init__(self, ollama_service: Any = None, llm_logger: Any = None):
        self.ollama = ollama_service
        self.logger = llm_logger

    def build_map_prompt(
        self,
        description: str,
        width: int = 60,
        height: int = 40,
        depth: int = 1,
    ) -> str:
        """
        Build the LLM prompt for map generation.

        Args:
            description: Natural language description of the desired map
            width: Map width
            height: Map height
            depth: Dungeon depth (for difficulty scaling)

        Returns:
            Prompt string
        """
        return f"""You are a dungeon architect. Design a roguelike dungeon floor layout.

DESCRIPTION: {description}

MAP DIMENSIONS: {width} x {height}
DEPTH: {depth}

Design a dungeon with:
1. 4-8 rooms connected by corridors
2. Stairs up (near entrance) and stairs down (far from entrance)
3. Entity placements appropriate to depth {depth}

Return ONLY valid JSON in this exact format:
{MAP_JSON_SCHEMA}

Rules:
- Rooms must not overlap (leave at least 2 tiles gap)
- Corridors connect room centers
- Stairs must be inside rooms
- Entity positions must be on floor tiles (inside rooms)
- All coordinates must be within map bounds (0 to {width-1}, 0 to {height-1})
"""

    def parse_map_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse LLM response into structured map data.

        Args:
            response: Raw LLM response string

        Returns:
            Parsed map data dict, or None if parsing fails
        """
        if not response:
            return None

        try:
            # Try to extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start < 0 or end <= 0:
                return None

            json_str = response[start:end]
            data = json.loads(json_str)

            # Validate required fields
            required_fields = ["width", "height", "rooms", "corridors", "stairs"]
            for field_name in required_fields:
                if field_name not in data:
                    return None

            return data
        except (json.JSONDecodeError, ValueError):
            return None

    def generate_map(
        self,
        description: str,
        width: int = 60,
        height: int = 40,
        depth: int = 1,
        timeout: int = 30,
    ) -> Tuple[Optional[MapBuilder], bool]:
        """
        Generate a map from an LLM description.

        Args:
            description: Natural language description
            width: Map width
            height: Map height
            depth: Dungeon depth
            timeout: LLM call timeout in seconds

        Returns:
            Tuple of (MapBuilder or None, used_llm: bool)
        """
        if self.ollama is None:
            return None, False

        prompt = self.build_map_prompt(description, width, height, depth)

        try:
            response = self.ollama.generate(prompt, timeout=timeout)
            map_data = self.parse_map_response(response)

            if map_data is None:
                return None, False

            # Create MapBuilder from parsed data
            builder = MapBuilder.from_map_data(map_data)

            # Validate the generated map
            validation = builder.validate_map()
            if not validation["valid"]:
                return None, False

            return builder, True

        except Exception:
            return None, False

    def generate_map_async(
        self,
        description: str,
        request_queue: Any,
        width: int = 60,
        height: int = 40,
        depth: int = 1,
        turn_number: int = 0,
    ) -> None:
        """
        Enqueue a map generation request to the LLM worker queue.

        Uses the existing async queue pattern (non-blocking).

        Args:
            description: Natural language description
            request_queue: The llm_request_queue (Queue)
            width: Map width
            height: Map height
            depth: Dungeon depth
            turn_number: Current game turn
        """
        try:
            request_queue.put_nowait({
                "type": "map_generation",
                "description": description,
                "width": width,
                "height": height,
                "depth": depth,
                "turn_number": turn_number,
                "prompt_summary": f"Map: {description[:50]}...",
            })
        except Exception:
            pass  # Queue full — skip

    def process_map_response(self, response: Dict[str, Any]) -> Optional[MapBuilder]:
        """
        Process an LLM response from the response queue into a MapBuilder.

        Args:
            response: Dict from llm_response_queue

        Returns:
            MapBuilder if successful, None otherwise
        """
        if not response.get("success"):
            return None

        map_data = response.get("map_data")
        if map_data is None:
            return None

        try:
            builder = MapBuilder.from_map_data(map_data)
            validation = builder.validate_map()
            if not validation["valid"]:
                return None
            return builder
        except Exception:
            return None

    def generate_fallback(
        self,
        width: int = 60,
        height: int = 40,
        room_count: int = 6,
        seed: Optional[int] = None,
    ) -> MapBuilder:
        """
        Generate a procedural fallback map when LLM is unavailable.

        Args:
            width: Map width
            height: Map height
            room_count: Number of rooms
            seed: Random seed

        Returns:
            Validated MapBuilder instance
        """
        builder = MapBuilder(width=width, height=height)
        builder.generate_procedural(room_count=room_count, seed=seed)
        return builder
