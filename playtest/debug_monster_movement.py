#!/usr/bin/env python3
"""Debug: Check if monsters move toward player on floor 1."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from darkdelve import Game

game = Game()
game.initialize()
p = game.player
print("Player at (%d, %d)" % (p.x, p.y))
for e in game.entities:
    if e is not p and getattr(e, 'blocks', False):
        dist = max(abs(e.x - p.x), abs(e.y - p.y))
        print("  %s at (%d, %d) dist=%d" % (e.name, e.x, e.y, dist))

print("\nWaiting 10 turns...")
for _ in range(10):
    game.main_loop(action='e', render_to_stdout=False)

p = game.player
print("After wait - Player at (%d, %d)" % (p.x, p.y))
for e in game.entities:
    if e is not p and getattr(e, 'blocks', False) and e.is_alive:
        dist = max(abs(e.x - p.x), abs(e.y - p.y))
        print("  %s at (%d, %d) dist=%d" % (e.name, e.x, e.y, dist))
