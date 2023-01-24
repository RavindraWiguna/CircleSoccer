from gameobject import CircleObject

class Ball(CircleObject):
    '''
    Store all ball data and method
    '''
    RADIUS = 20
    MASS = 5
    ELASTICITY=0.75
    def __init__(self, space, position=(0,0)) -> None:
        super().__init__(space, position, self.RADIUS, self.MASS, self.ELASTICITY, imgPath='assets/images/betterball.png')
    
