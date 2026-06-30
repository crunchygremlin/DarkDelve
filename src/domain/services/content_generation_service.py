"""Orchestration service that generates and persists content for a new game."""

from __future__ import annotations
import time
import uuid
from typing import Dict, Any, List, Optional
from src.infrastructure.repositories.content_repository import ContentRepository
from src.application.services.content_seeder import ContentSeeder
from src.domain.value_objects.llm_logging import LLMLogger, LLMCallLog, estimate_tokens


class ContentGenerationService:
    """Orchestrates seed-based content generation for a new game."""

    def __init__(
        self,
        content_repository: ContentRepository,
        content_seeder: ContentSeeder,
        ollama_service: Any,          # OllamaService
        llm_logger: LLMLogger,
    ):
        self._repo = content_repository
        self._seeder = content_seeder
        self._ollama = ollama_service
        self._logger = llm_logger

    def generate_game_content(
        self,
        item_tags: List[str],
        monster_tags: List[str],
        level_tags: List[str],
        player_summary: str = "Unknown",
        items_per_batch: int = 5,
        monsters_per_batch: int = 4,
    ) -> Dict[str, Any]:
        """Generate a full set of content for a new game.
        
        Returns dict with keys: items, monsters, level_descriptions.
        Each value is the parsed JSON from the LLM response.
        """
        results: Dict[str, Any] = {
            "items": [],
            "monsters": [],
            "level_descriptions": [],
        }

        # Generate items
        item_prompt = self._seeder.build_item_prompt(
            tags=item_tags, count=items_per_batch, player_summary=player_summary
        )
        item_response = self._call_llm(item_prompt, "content_items")
        if item_response:
            results["items"] = item_response.get("items", [])

        # Generate monsters
        monster_prompt = self._seeder.build_monster_prompt(
            tags=monster_tags, count=monsters_per_batch, player_summary=player_summary
        )
        monster_response = self._call_llm(monster_prompt, "content_monsters")
        if monster_response:
            results["monsters"] = monster_response.get("mobs", [])

        # Generate level descriptions
        level_prompt = self._seeder.build_level_prompt(
            tags=level_tags, level_number=1, player_summary=player_summary
        )
        level_response = self._call_llm(level_prompt, "content_level")
        if level_response:
            results["level_descriptions"] = [level_response]

        return results

    def _call_llm(self, prompt: str, content_key: str) -> Optional[Dict[str, Any]]:
        """Call the LLM and log the result."""
        import json as _json

        start = time.time()
        try:
            response = self._ollama.generate(prompt)
            latency = (time.time() - start) * 1000
            parsed = self._parse_json_response(response)

            self._logger.log_call(LLMCallLog(
                call_id=str(uuid.uuid4()),
                timestamp=start,
                context="content_generation",
                entity_id=None,
                prompt_summary=prompt[:200],
                response_summary=response[:200],
                latency_ms=latency,
                tokens_used=estimate_tokens(prompt) + estimate_tokens(response),
                success=parsed is not None,
                prompt_tokens=estimate_tokens(prompt),
                response_tokens=estimate_tokens(response),
                model="qwen2.5-coder:7b-instruct",
                temperature=0.7,
            ))
            return parsed
        except Exception as e:
            latency = (time.time() - start) * 1000
            self._logger.log_call(LLMCallLog(
                call_id=str(uuid.uuid4()),
                timestamp=start,
                context="content_generation",
                entity_id=None,
                prompt_summary=prompt[:200],
                response_summary="",
                latency_ms=latency,
                tokens_used=0,
                success=False,
                error=str(e),
                model="qwen2.5-coder:7b-instruct",
                temperature=0.7,
            ))
            return None

    @staticmethod
    def _parse_json_response(response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from LLM response."""
        import json as _json
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            try:
                return _json.loads(response[start:end])
            except _json.JSONDecodeError:
                pass
        return None