import os
import re

class_pattern = re.compile(r'^\\s*class\\s+(\\w+)(?:\\s*\\((.*)\\))?:')
game_loop_pattern = re.compile(r'while.*running|pygame.*game.*loop|game.*loop', re.IGNORECASE)

for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except Exception as e:
                print(f"Error reading {path}: {e}")
                continue
            for i, line in enumerate(lines, 1):
                line = line.rstrip('\\n')
                class_match = class_pattern.match(line)
                if class_match:
                    class_name = class_match.group(1)
                    inheritance = class_match.group(2) if class_match.group(2) else ''
                    print(f"CLASS: {path}:{i}: class {class_name}({inheritance})")
                if game_loop_pattern.search(line):
                    print(f"GAME_LOOP: {path}:{i}: {line}")
