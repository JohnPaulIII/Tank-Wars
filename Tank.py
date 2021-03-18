class Tank:
    def __init__(self, tankx, tanky, angle1, angle2, name, color):
        self.x = tankx
        self.y = tanky
        self.rotation = angle1
        self.turrent = angle2
        self.name = name
        self.color = color
        self.dead = False
        self.nowdead = False
        self.fireframe = 0
        self.exploding = False
        self.explosionframe = 0
        self.xOffset = 0
        self.yOffset = 0
        self.rotationOffset = 0
        self.turrentOffset = 0