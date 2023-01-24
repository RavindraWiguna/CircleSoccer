from gameobject import CircleObject

class Player(CircleObject):
    '''
    Store all player data and method
    '''
    def __init__(self, space, position=(0,0), radius=1, mass=1, elasticity=0.75, color=(128, 128, 128, 100)) -> None:
        super().__init__(space, position, radius, mass, elasticity, )