"""Input controller for handling user input."""

from typing import Callable, Dict, Optional


class InputController:
    """Handle user input and map to game actions."""
    
    def __init__(self):
        self._bindings: Dict[str, Callable] = {}
        self._last_action: Optional[str] = None
    
    def bind_key(self, key: str, action: Callable) -> None:
        """Bind a key to an action."""
        self._bindings[key] = action
    
    def handle_input(self, key: str) -> Optional[str]:
        """Handle a key press and return the action."""
        if key in self._bindings:
            self._last_action = key
            return self._bindings[key]()
        return None
    
    def get_last_action(self) -> Optional[str]:
        """Get the last processed action."""
        return self._last_action
    
    def reset(self) -> None:
        """Reset the input state."""
        self._last_action = None