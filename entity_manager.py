class Entity:
    def __init__(self, x, y, character, color):
        self.x = x
        self.y = y
        self.character = character
        self.color = color

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def draw(self, console):
        console.print(self.x, self.y, self.character, fg=self.color)

class Player(Entity):
    def __init__(self, x, y, character='@', color='white'):
        super().__init__(x, y, character, color)

class Monster(Entity):
    def __init__(self, x, y, character='M', color='red'):
        super().__init__(x, y, character, color)