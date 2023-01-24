from gameobject import CircleObject

class Player(CircleObject):
    '''
    Store all player data and method
    '''
    RADIUS = 30
    MASS = 20
    ELASTICITY=0.75
    def __init__(self, space, position, color) -> None:
        super().__init__(space, position, self.RADIUS, self.MASS, self.ELASTICITY, color)