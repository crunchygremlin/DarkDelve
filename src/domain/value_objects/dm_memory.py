"""DM Global Memory value object for throttled poetic memory."""

from dataclasses import dataclass


@dataclass
class DMGlobalMemory:
    """Global poetic memory for the Dungeon Master agent.
    
    Bounded by headroom tokens to prevent context overflow.
    """
    summary: str = ""
    max_tokens: int = 8192
    version: int = 0
    last_updated_level: int = 0

    def refresh(self, narrative: str, headroom_tokens: int) -> None:
        """Combine old summary + new narrative, then bound to headroom.
        
        Args:
            narrative: New narrative text to add
            headroom_tokens: Available headroom in tokens
        """
        combined = f"{self.summary}\n{narrative}".strip()
        est = estimate_tokens(combined)
        if est > headroom_tokens:
            # Keep the most recent ~headroom_tokens worth (poetic tail).
            allowed_chars = max(0, headroom_tokens * 4)
            self.summary = combined[-allowed_chars:]
        else:
            self.summary = combined
        self.version += 1

    def context_string(self) -> str:
        """Return the memory context string."""
        return self.summary

    def truncate_to_headroom(self, headroom_tokens: int) -> str:
        """Truncate summary to fit within headroom.
        
        Args:
            headroom_tokens: Available headroom in tokens
            
        Returns:
            Truncated summary string
        """
        if estimate_tokens(self.summary) <= headroom_tokens:
            return self.summary
        return self.summary[-(headroom_tokens * 4):]


def estimate_tokens(text: str) -> int:
    """Rough token estimation. ~4 chars per token for English text."""
    return max(1, len(text) // 4)