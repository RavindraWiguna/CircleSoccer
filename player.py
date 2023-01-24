from gameobject import CircleObject

class Player(CircleObject):
    '''
    Store all player data and method
    '''
    RADIUS = 25
    MASS = 20
    ELASTICITY=0.75
    MAX_ACC = 100 # since m*a = F, i guess call this acc, i want bigger mass, faster stop
    PIVOT_MAX_FORCE = MASS*MAX_ACC # bigger = faster stop
    def __init__(self, space, position, color) -> None:
        super().__init__(space, position, self.RADIUS, self.MASS, self.ELASTICITY, self.PIVOT_MAX_FORCE, color)
    

    def _apply_force(self, force_vec):
        # print('ap', force_vec, self.body.center_of_gravity)
        self.body.apply_force_at_local_point(force_vec, (self.body.center_of_gravity))

    def move_up(self, force_magnitude=100):
        self._apply_force((0.0, -force_magnitude))
    
    def move_down(self, force_magnitude=100):
        self._apply_force((0.0, force_magnitude))
    
    def move_left(self, force_magnitude=100):
        self._apply_force((-force_magnitude, 0.0))

    def move_right(self, force_magnitude=100):
        self._apply_force((force_magnitude, 0.0))