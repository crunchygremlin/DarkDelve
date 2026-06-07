"""
Roguelike Symbol and Character Registry
Defines all visual symbols used in the game with consistent theming
"""

# Color palette (RGB tuples)
COLORS = {
    'player': (255, 255, 0),      # Yellow
    'wall': (80, 80, 80),          # Dark gray
    'floor': (100, 100, 100),      # Medium gray
    'door': (150, 100, 50),        # Brown
    'gold': (255, 215, 0),         # Gold
    'blood': (200, 0, 0),          # Red
    'poison': (0, 200, 0),         # Green
    'magic': (150, 100, 255),      # Purple
    'water': (100, 150, 255),      # Blue
    'fire': (255, 100, 0),         # Orange
    'item': (200, 200, 100),       # Light yellow
    'enemy_weak': (100, 200, 100), # Light green
    'enemy_normal': (100, 150, 200), # Light blue
    'enemy_tough': (200, 100, 100), # Light red
    'enemy_boss': (255, 0, 0),     # Bright red
    'equipment': (150, 150, 150),  # Gray
}

# Roguelike Symbol Registry
ROGUELIKE_SYMBOLS = {
    # === TERRAIN ===
    'floor': {
        'char': '.',
        'color': COLORS['floor'],
        'name': 'Floor',
        'walkable': True,
    },
    'wall': {
        'char': '#',
        'color': COLORS['wall'],
        'name': 'Wall',
        'walkable': False,
    },
    'door': {
        'char': '+',
        'color': COLORS['door'],
        'name': 'Door',
        'walkable': True,
    },
    'stair_down': {
        'char': '>',
        'color': COLORS['gold'],
        'name': 'Stairs Down',
        'walkable': True,
    },
    'stair_up': {
        'char': '<',
        'color': COLORS['gold'],
        'name': 'Stairs Up',
        'walkable': True,
    },
    
    # === PLAYER ===
    'player': {
        'char': '@',
        'color': COLORS['player'],
        'name': 'Adventurer',
        'walkable': False,
    },
    
    # === ITEMS ===
    'weapon': {
        'char': '/',
        'color': COLORS['item'],
        'name': 'Weapon',
        'types': ['sword', 'axe', 'bow', 'dagger'],
    },
    'armor': {
        'char': '[',
        'color': COLORS['equipment'],
        'name': 'Armor',
        'types': ['helm', 'chest', 'legs', 'shield'],
    },
    'potion': {
        'char': '!',
        'color': COLORS['poison'],
        'name': 'Potion',
        'types': ['health', 'mana', 'strength', 'invisibility'],
    },
    'scroll': {
        'char': '?',
        'color': COLORS['magic'],
        'name': 'Scroll',
        'types': ['fireball', 'lightning', 'heal', 'identify'],
    },
    'gold': {
        'char': '$',
        'color': COLORS['gold'],
        'name': 'Gold',
    },
    'misc': {
        'char': '*',
        'color': COLORS['item'],
        'name': 'Item',
        'types': ['gem', 'ring', 'amulet', 'key'],
    },
    
    # === ENEMY TIERS (will be customized by LLM) ===
    'enemy_minion': {
        'char': 'g',
        'color': COLORS['enemy_weak'],
        'name': 'Minion',
        'tier': 'minion',
    },
    'enemy_soldier': {
        'char': 's',
        'color': COLORS['enemy_normal'],
        'name': 'Soldier',
        'tier': 'soldier',
    },
    'enemy_elite': {
        'char': 'E',
        'color': COLORS['enemy_tough'],
        'name': 'Elite',
        'tier': 'elite',
    },
    'enemy_boss': {
        'char': 'B',
        'color': COLORS['enemy_boss'],
        'name': 'Boss',
        'tier': 'boss',
    },
}

# Symbol convenience function
def get_symbol(symbol_type):
    """Get symbol data by type"""
    return ROGUELIKE_SYMBOLS.get(symbol_type, ROGUELIKE_SYMBOLS['misc'])

def get_symbol_char(symbol_type):
    """Get just the character"""
    return ROGUELIKE_SYMBOLS.get(symbol_type, {}).get('char', '?')

def get_symbol_color(symbol_type):
    """Get just the color"""
    return ROGUELIKE_SYMBOLS.get(symbol_type, {}).get('color', COLORS['item'])
