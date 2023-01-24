from gameobject import CircleObject

class Ball(CircleObject):
    '''
    Store all ball data and method
    '''
    RADIUS = 20
    MASS = 5
    ELASTICITY=0.8
    MAX_ACC = 100 # idk what to call, i guess acc, since mass * acc 
    PIVOT_MAX_FORCE = MASS*MAX_ACC # kinda like a friction, if bigger = move slower = faster stop
    def __init__(self, space, position=(0,0)) -> None:
        super().__init__(space, position, self.RADIUS, self.MASS, self.ELASTICITY, self.PIVOT_MAX_FORCE, imgPath='assets/images/betterball.png')
    
