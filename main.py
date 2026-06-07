import tcod
import random
import numpy as np
import threading
import queue
import urllib.request
import json
import os
import time

llm_request_queue = queue.Queue()
llm_response_queue = queue.Queue()
llm_metrics = {"requests": 0, "responses": 0, "total_latency_ms": 0.0}

def local_llm_worker():
    while True:
        try:
            prompt_data = llm_request_queue.get()
            if prompt_data is None: break
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": "llama3.2:3b", 
                "prompt": prompt_data["prompt"],
                "stream": False,
                "format": "json"
            }
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode("utf-8"), 
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                response_json = json.loads(result["response"])
                llm_response_queue.put({
                    "commander_id": prompt_data["commander_id"],
                    "commander_shout": response_json.get("commander_shout", "CHAAAARGE!"),
                    "command": response_json.get("global_command", "DEFAULT_ATTACK"),
                    "request_ts": prompt_data.get("ts", time.time()),
                    "response_ts": time.time()
                })
        except Exception as e:
            llm_response_queue.put({
                "commander_id": "SYSTEM", 
                "commander_shout": "The AI brain stumbles!", 
                "command": "DEFAULT_ATTACK"
            })
        finally:
            llm_request_queue.task_done()

threading.Thread(target=local_llm_worker, daemon=True).start()

class Entity:
    def __init__(self, x, y, char, color, name, blocks=False, hp=10, power=3, defense=1, intel_tier=1, training="None", is_commander=False):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.max_hp = hp
        self.hp = hp
        self.power = power
        self.defense = defense
        self.intel_tier = intel_tier
        self.training = training
        self.current_override = None
        self.is_commander = is_commander
        self.home_position = (x, y)
        self.current_command = None
        self.pending_command = None

    @property
    def is_alive(self):
        return self.hp > 0

    def move_towards(self, target_x, target_y, dungeon_map, entities):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = max(abs(dx), abs(dy))
        if distance > 0:
            step_x = int(round(dx / distance))
            step_y = int(round(dy / distance))
            dest_x = self.x + step_x
            dest_y = self.y + step_y
            if 0 <= dest_x < dungeon_map.shape[0] and 0 <= dest_y < dungeon_map.shape[1]:
                if dungeon_map[dest_x, dest_y]:
                    if not any(e.blocks for e in entities if e.x == dest_x and e.y == dest_y and e is not self):
                        self.x = dest_x
                        self.y = dest_y
    
    def move_to(self, x, y, dungeon_map, entities):
        """Move to a specific location if possible"""
        if 0 <= x < dungeon_map.shape[0] and 0 <= y < dungeon_map.shape[1]:
            if dungeon_map[x, y]:
                if not any(e.blocks for e in entities if e.x == x and e.y == y and e is not self):
                    self.x = x
                    self.y = y
                    return True
        return False

def tunnel_between(start, end):
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:
        for x in range(min(x1, x2), max(x1, x2) + 1): yield x, y1
        for y in range(min(y1, y2), max(y1, y2) + 1): yield x2, y
    else:
        for y in range(min(y1, y2), max(y1, y2) + 1): yield x1, y
        for x in range(min(x1, x2), max(x1, x2) + 1): yield x, y2

def generate_dungeon(map_width, map_height, max_rooms, room_min_size, room_max_size, max_monsters_per_room):
    dungeon_map = np.zeros((map_width, map_height), dtype=bool, order="F")
    rooms = []
    entities = []
    for r in range(max_rooms):
        w = random.randint(room_min_size, room_max_size)
        h = random.randint(room_min_size, room_max_size)
        x = random.randint(0, map_width - w - 1)
        y = random.randint(0, map_height - h - 1)
        x1, y1, x2, y2 = x, y, x + w, y + h
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)
        overlap = False
        for rx1, ry1, rx2, ry2, _, _ in rooms:
            if x1 < rx2 and x2 > rx1 and y1 < ry2 and y2 > ry1:
                overlap = True
                break
        if overlap: continue
        dungeon_map[x1+1:x2, y1+1:y2] = True
        if len(rooms) == 0:
            player = Entity(center_x, center_y, "@", (255, 255, 0), "Player", blocks=True, hp=30, power=5, defense=2)
            entities.append(player)
        else:
            prev_room = rooms[-1]
            prev_center = (prev_room[4], prev_room[5])
            for tx, ty in tunnel_between(prev_center, (center_x, center_y)):
                dungeon_map[tx, ty] = True
            if len(rooms) == 1:
                commander = Entity(center_x, center_y, "G", (255, 0, 0), "Goblin Warlord", blocks=True, hp=25, power=4, defense=2, intel_tier=3, is_commander=True)
                commander.home_position = (center_x, center_y)
                entities.append(commander)
                for _ in range(12):
                    mx = random.randint(x1 + 1, x2 - 1)
                    my = random.randint(y1 + 1, y2 - 1)
                    if not any(e.x == mx and e.y == my for e in entities):
                        entities.append(Entity(mx, my, "z", (150, 75, 0), "Zombie", blocks=True, hp=8, power=2, defense=0, intel_tier=0, training="Shield Wall"))
            else:
                num_monsters = random.randint(0, max_monsters_per_room)
                for _ in range(num_monsters):
                    mx = random.randint(x1 + 1, x2 - 1)
                    my = random.randint(y1 + 1, y2 - 1)
                    if not any(e.x == mx and e.y == my for e in entities):
                        if random.random() < 0.8:
                            entities.append(Entity(mx, my, "o", (63, 127, 63), "Orc", blocks=True, hp=10, power=3, defense=0, intel_tier=2))
                        else:
                            entities.append(Entity(mx, my, "T", (0, 127, 0), "Troll", blocks=True, hp=16, power=4, defense=1, intel_tier=1))
        rooms.append((x1, y1, x2, y2, center_x, center_y))
    return dungeon_map, entities

def find_path(start, goal, dungeon_map, entities):
    """Find a path from start to goal using A* algorithm"""
    from heapq import heappush, heappop
    
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    blocked = set()
    for e in entities:
        if e.blocks:
            blocked.add((e.x, e.y))
    
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    
    while open_set:
        current = heappop(open_set)[1]
        
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return list(reversed(path))
        
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            neighbor = (current[0] + dx, current[1] + dy)
            
            if not (0 <= neighbor[0] < dungeon_map.shape[0] and 0 <= neighbor[1] < dungeon_map.shape[1]):
                continue
            if not dungeon_map[neighbor[0], neighbor[1]]:
                continue
            if neighbor in blocked and neighbor != goal:
                continue
            
            tentative_g = g_score[current] + (1.414 if abs(dx) + abs(dy) == 2 else 1)
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristic(neighbor, goal)
                f_score[neighbor] = f
                heappush(open_set, (f, neighbor))
    
    return [start, goal]

def validate_llm_response(response):
    """Validate and sanitize LLM response"""
    valid_commands = [
        "ATTACK_PLAYER", "DEFEND_COMMANDER", "RETREAT_TO_ROOM",
        "HOLD_POSITION", "FLANK_LEFT", "FLANK_RIGHT",
        "DEFAULT_ATTACK", "WAIT"
    ]
    
    command = response.get("command", "DEFAULT_ATTACK")
    if command not in valid_commands:
        command = "ATTACK_PLAYER"
    
    shout = response.get("commander_shout", "CHAAAARGE!")
    
    return {
        "command": command,
        "commander_shout": shout
    }

def interpret_commander_action(commander, player, dungeon_map, entities):
    """Convert commander's current_command to an action and target"""
    if not commander.current_command:
        return "WAIT", None
    
    cmd = commander.current_command.get("command", "WAIT")
    
    if cmd == "ATTACK_PLAYER":
        return "ATTACK", (player.x, player.y)
    elif cmd == "DEFEND_COMMANDER":
        return "DEFEND", commander.home_position
    elif cmd == "RETREAT_TO_ROOM":
        return "RETREAT", commander.home_position
    elif cmd == "HOLD_POSITION":
        return "WAIT", None
    elif cmd == "FLANK_LEFT":
        return "FLANK", "LEFT"
    elif cmd == "FLANK_RIGHT":
        return "FLANK", "RIGHT"
    else:
        return "WAIT", None

def enqueue_commander_prompt(commander, player, entities, training=None):
    """Create and queue a prompt for the LLM"""
    visible_entities = [e for e in entities if abs(e.x - commander.x) <= 10 and abs(e.y - commander.y) <= 10]
    
    visible_str = json.dumps([
        {"name": e.name, "x": e.x, "y": e.y, "hp": e.hp, "max_hp": e.max_hp}
        for e in visible_entities
    ])
    
    prompt_template_path = os.path.join(os.path.dirname(__file__), 'prompt', 'commander_prompt.txt')
    
    try:
        with open(prompt_template_path, 'r') as f:
            template = f.read()
    except FileNotFoundError:
        template = "JSONONLY {visible_entities}"
    
    prompt = template.replace("{visible_entities}", visible_str)
    
    req = {
        "commander_id": commander.name,
        "prompt": prompt,
        "ts": time.time()
    }
    
    llm_request_queue.put(req)

def process_llm_responses(entities):
    """Process all pending LLM responses"""
    while not llm_response_queue.empty():
        try:
            response = llm_response_queue.get_nowait()
            
            # Update metrics for every response received
            llm_metrics["responses"] += 1
            if "request_ts" in response and "response_ts" in response:
                latency = (response["response_ts"] - response["request_ts"]) * 1000
                llm_metrics["total_latency_ms"] += latency
            
            # Find the commander this response belongs to
            commander_id = response.get("commander_id")
            commander = None
            for e in entities:
                if e.is_commander and e.name == commander_id:
                    commander = e
                    break
            
            if commander:
                validated = validate_llm_response(response)
                commander.current_command = {
                    "command": validated["command"],
                    "shout": validated["commander_shout"]
                }
        except queue.Empty:
            break

def get_llm_metrics():
    """Get current LLM metrics"""
    avg_latency = 0.0
    if llm_metrics["responses"] > 0:
        avg_latency = llm_metrics["total_latency_ms"] / llm_metrics["responses"]
    
    return {
        "requests": llm_metrics["requests"],
        "responses": llm_metrics["responses"],
        "avg_latency_ms": avg_latency,
        "total_latency_ms": llm_metrics["total_latency_ms"]
    }

def main_text():
    """Main game loop - text-based version for terminal"""
    dungeon_map, entities = generate_dungeon(80, 50, 10, 10, 20, 5)
    player = entities[0]  # Player is always first
    
    turn = 0
    game_over = False
    
    print("\n" + "="*60)
    print("DARKDELVE - AI ROGUELIKE")
    print("="*60)
    print(f"Generated dungeon with {len(entities)} entities")
    print(f"Player HP: {player.max_hp}")
    print("\nGame started! (Text mode - terminal compatible)")
    print("Commands: move <x> <y>, wait, status, quit")
    print("="*60 + "\n")
    
    import sys
    while not game_over and player.is_alive:
        turn += 1
        print(f"\n[TURN {turn}] Player at ({player.x}, {player.y}) - HP: {player.hp}/{player.max_hp}")
        
        # Show visible entities
        visible = [e for e in entities if e != player and abs(e.x - player.x) <= 15 and abs(e.y - player.y) <= 15 and e.is_alive]
        if visible:
            print(f"Visible entities ({len(visible)}):")
            for e in visible[:5]:
                print(f"  - {e.name} at ({e.x}, {e.y}), HP: {e.hp}/{e.max_hp}")
        
        # Get player input
        try:
            cmd = input("\n> ").strip().lower().split()
            if not cmd:
                continue
            
            action = cmd[0]
            
            if action == "quit":
                game_over = True
                break
            elif action == "wait":
                dx, dy = 0, 0
            elif action == "move" and len(cmd) >= 3:
                try:
                    dx = int(cmd[1]) - player.x
                    dy = int(cmd[2]) - player.y
                except ValueError:
                    print("Invalid coordinates")
                    continue
            elif action == "status":
                print(f"\nPlayer: {player.name}")
                print(f"HP: {player.hp}/{player.max_hp}")
                print(f"Position: ({player.x}, {player.y})")
                print(f"Power: {player.power}, Defense: {player.defense}")
                print(f"Alive Entities: {len([e for e in entities if e.is_alive])}")
                continue
            else:
                print("Unknown command. Try: move <x> <y>, wait, status, quit")
                continue
            
            # Move player
            if dx != 0 or dy != 0:
                new_x = player.x + dx
                new_y = player.y + dy
                if player.move_to(new_x, new_y, dungeon_map, entities):
                    print(f"Moved to ({new_x}, {new_y})")
                else:
                    print("Cannot move there!")
            
            # Enemy AI: move and act
            alive_enemies = [e for e in entities if e.is_alive and e != player]
            for entity in alive_enemies:
                if entity.is_commander:
                    # Enqueue LLM prompt for commander
                    enqueue_commander_prompt(entity, player, entities)
                    llm_metrics["requests"] += 1
                else:
                    # Simple AI: move towards player
                    if abs(entity.x - player.x) <= 20 and abs(entity.y - player.y) <= 20:
                        entity.move_towards(player.x, player.y, dungeon_map, entities)
            
            # Process LLM responses
            process_llm_responses(entities)
            
            # Execute commander actions
            for entity in alive_enemies:
                if entity.is_alive and entity.is_commander and entity.current_command:
                    action, target = interpret_commander_action(entity, player, dungeon_map, entities)
                    if action == "ATTACK" and target:
                        path = find_path((entity.x, entity.y), target, dungeon_map, entities)
                        if len(path) > 1:
                            entity.move_to(path[1][0], path[1][1], dungeon_map, entities)
                            # Check for combat
                            if path[1] == (player.x, player.y):
                                damage = max(1, entity.power - player.defense + random.randint(-2, 2))
                                player.hp -= damage
                                print(f"{entity.name} attacks for {damage} damage!")
                    elif action == "RETREAT" and target:
                        path = find_path((entity.x, entity.y), target, dungeon_map, entities)
                        if len(path) > 1:
                            entity.move_to(path[1][0], path[1][1], dungeon_map, entities)
            
            # Check for win/lose
            if not player.is_alive:
                print("\n*** YOU DIED ***")
                game_over = True
            elif not any(e.is_alive and e.is_commander for e in entities):
                print("\n*** YOU WON! ***")
                game_over = True
                
        except KeyboardInterrupt:
            print("\n\nGame interrupted.")
            game_over = True
        except EOFError:
            print("\n\nGame ended.")
            game_over = True
    
    print("\nGame Over!")
    print(f"Final Stats: Turns: {turn}, Player HP: {player.hp}/{player.max_hp}")
    print(f"LLM Metrics: {llm_metrics['requests']} requests, {llm_metrics['responses']} responses")

def main():
    """Main game loop"""
    import os
    import sys
    
    # Detect headless environment
    is_headless = (
        not os.environ.get('DISPLAY') or 
        os.environ.get('SSH_CONNECTION') or
        'HEADLESS' in os.environ
    )
    
    # Try to check if we're actually in a terminal-only environment
    if sys.stdin and not sys.stdin.isatty():
        is_headless = True
    
    if is_headless:
        # Headless environment - use text mode immediately
        main_text()
        return
    
    # Try graphics mode (but use a signal alarm to avoid hanging)
    try:
        screen_width = 120
        screen_height = 40
        
        # Set environment to hint tcod about headless environment
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        
        # This will fail gracefully on headless systems now
        console = tcod.Console(screen_width, screen_height, order="F")
        
        # Create game window - this is where it might hang on headless systems
        with tcod.context.new_terminal(
            screen_width,
            screen_height,
            tileset=tcod.tileset.load_tilesheet(
                "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
            ),
            title="DarkDelve - AI Roguelike",
            vsync=True,
        ) as context:
            # Generate dungeon and entities
            dungeon_map, entities = generate_dungeon(80, 50, 10, 10, 20, 5)
            player = entities[0]  # Player is always first
            
            turn = 0
            game_over = False
            
            while not game_over:
                # Render
                console.clear()
                
                # Draw dungeon
                for x in range(dungeon_map.shape[0]):
                    for y in range(dungeon_map.shape[1]):
                        if dungeon_map[x, y]:
                            console.print(x, y, ".", (100, 100, 100))
                        else:
                            console.print(x, y, "#", (50, 50, 50))
                
                # Draw entities
                for entity in entities:
                    if entity.is_alive:
                        console.print(entity.x, entity.y, entity.char, entity.color)
                
                # Draw UI
                ui_y = dungeon_map.shape[1] + 2
                console.print(0, ui_y, f"Turn: {turn} | Entities: {len([e for e in entities if e.is_alive])}", (200, 200, 200))
                console.print(0, ui_y + 1, f"Player HP: {player.hp}/{player.max_hp}", (0, 255, 0) if player.hp > 0 else (255, 0, 0))
                
                metrics = get_llm_metrics()
                console.print(0, ui_y + 2, f"LLM: {metrics['responses']} responses, {metrics['avg_latency_ms']:.0f}ms avg", (150, 150, 255))
                console.print(0, ui_y + 3, "Controls: WASD=move, Q=quit, SPACE=wait", (200, 200, 200))
                
                context.present(console)
                
                # Handle input
                for event in tcod.event.wait():
                    if isinstance(event, tcod.event.Quit):
                        game_over = True
                    elif isinstance(event, tcod.event.KeyDown):
                        key = event.sym
                        dx, dy = 0, 0
                        
                        if key == tcod.event.K_w:
                            dy = -1
                        elif key == tcod.event.K_s:
                            dy = 1
                        elif key == tcod.event.K_a:
                            dx = -1
                        elif key == tcod.event.K_d:
                            dx = 1
                        elif key == tcod.event.K_SPACE:
                            dx, dy = 0, 0
                        elif key == tcod.event.K_q:
                            game_over = True
                            continue
                        
                        # Move player
                        new_x = player.x + dx
                        new_y = player.y + dy
                        player.move_to(new_x, new_y, dungeon_map, entities)
                        
                        # Enemy AI: move commanders towards player
                        for entity in entities:
                            if entity.is_alive and entity != player:
                                if entity.is_commander:
                                    # Enqueue LLM prompt
                                    enqueue_commander_prompt(entity, player, entities)
                                else:
                                    # Simple AI: move towards player
                                    entity.move_towards(player.x, player.y, dungeon_map, entities)
                        
                        # Process LLM responses
                        process_llm_responses(entities)
                        
                        # Execute commander actions
                        for entity in entities:
                            if entity.is_alive and entity.is_commander and entity.current_command:
                                action, target = interpret_commander_action(entity, player, dungeon_map, entities)
                                if action == "ATTACK":
                                    path = find_path((entity.x, entity.y), target, dungeon_map, entities)
                                    if len(path) > 1:
                                        entity.move_to(path[1][0], path[1][1], dungeon_map, entities)
                                elif action == "RETREAT":
                                    path = find_path((entity.x, entity.y), target, dungeon_map, entities)
                                    if len(path) > 1:
                                        # Move towards home
                                        entity.move_to(path[1][0], path[1][1], dungeon_map, entities)
                        
                        turn += 1
                        
                        # Check win/lose conditions
                        if not player.is_alive:
                            game_over = True
                        
                        # Update LLM request counter for metrics
                        for entity in entities:
                            if entity.is_commander:
                                llm_metrics["requests"] += 1
                        
                        break
    except (RuntimeError, OSError, Exception) as e:
        # Graphics failed - fallback to text mode
        print(f"Graphics mode unavailable, using text mode...\n", file=sys.stderr)
        main_text()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame interrupted.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Falling back to text mode...")
        main_text()
