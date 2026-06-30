"""Service that builds seed-aware prompts for content generation."""

from __future__ import annotations
from typing import List, Dict, Any
from src.infrastructure.repositories.content_repository import ContentRepository, SeedContent


class ContentSeeder:
    """Builds prompts that include seed content as inspiration for new generation."""

    def __init__(self, content_repository: ContentRepository):
        self._repo = content_repository

    def build_item_prompt(
        self,
        tags: List[str],
        count: int,
        player_summary: str = "Unknown",
    ) -> str:
        """Build an LLM prompt for item generation seeded with prior items."""
        seeds = self._repo.get_seeds_by_tags(tags, limit=3)
        seed_text = self._format_seeds_for_prompt(seeds)

        return f"""You are generating items for a roguelike dungeon game.

PLAYER PROFILE: {player_summary}

SEED IDEAS from previously generated content (use these as INSPIRATION, create NEW items):
{seed_text}

Generate {count} NEW items that are thematically similar but NOT identical to the seeds.
Each item must have: name, type (weapon/armor/potion/scroll/food/misc), rarity (common/uncommon/rare/epic/legendary),
damage (if weapon), defense (if armor), description, special effect.

Return JSON: {{"items": [...]}}"""

    def build_monster_prompt(
        self,
        tags: List[str],
        count: int,
        tier: int = 3,
        player_summary: str = "Unknown",
    ) -> str:
        """Build an LLM prompt for monster generation seeded with prior monsters."""
        seeds = self._repo.get_seeds_by_tags(tags, limit=3)
        seed_text = self._format_seeds_for_prompt(seeds)

        return f"""You are generating monsters for a roguelike dungeon game.

PLAYER PROFILE: {player_summary}
TIER: {tier} (1-5, higher is stronger)

SEED IDEAS from previously generated content (use these as INSPIRATION, create NEW monsters):
{seed_text}

Generate {count} NEW monsters that are thematically similar but NOT identical to the seeds.
Each monster must have: name, symbol (single ASCII char), tier (1-5), hp, power, defense, speed,
skills (list of 1-3), ai_type (Aggressive/Defensive/Stealthy).

Return JSON: {{"mobs": [...]}}"""

    def build_level_prompt(
        self,
        tags: List[str],
        level_number: int,
        player_summary: str = "Unknown",
    ) -> str:
        """Build an LLM prompt for level description seeded with prior levels."""
        seeds = self._repo.get_seeds_by_tags(tags, limit=2)
        seed_text = self._format_seeds_for_prompt(seeds)

        return f"""You are generating a level description for a roguelike dungeon game.

PLAYER PROFILE: {player_summary}
LEVEL NUMBER: {level_number}

SEED IDEAS from previously generated content (use these as INSPIRATION, create a NEW level):
{seed_text}

Generate a NEW level description with: title, description (2-3 sentences of atmospheric text),
and 3-5 key features (traps, rooms, special encounters).

Return JSON: {{"title": "...", "description": "...", "features": [...]}}"""

    def _format_seeds_for_prompt(self, seeds: List[SeedContent]) -> str:
        """Format seed content as text for inclusion in prompt."""
        if not seeds:
            return "(No seed content available — generate from scratch.)"

        lines = []
        for seed in seeds:
            # Truncate each seed to 300 chars to keep prompt size manageable
            truncated = seed.raw_json[:300]
            lines.append(f"- [{seed.key}] {truncated}")
        return "\n".join(lines)