from gameobject import CircleObject
from numpy import log

class Player(CircleObject):
    '''
    Store all player data and method
    '''
    RADIUS = 25
    MASS = 20
    ELASTICITY=0.75
    
    MAX_ACC = 100 # since m*a = F, i guess call this acc, i want bigger mass, faster stop
    PIVOT_MAX_FORCE = MASS*MAX_ACC # bigger = faster stop
    
    '''
    =================
     Diskrit param
    =================
    '''
    # TOP SPEED
    TOP_SPEED_POSITIVE = 512
    TOP_SPEED_NEGATIVE = -TOP_SPEED_POSITIVE
    ITER_TO_MAX  = 6
    ITER_TO_STOP = 3

    # INCREMENT VEL FOR EACH MOVE
    VEL_MAG = TOP_SPEED_POSITIVE/ITER_TO_MAX
    
    # SLOWING DOWN FACTOR
    BRAKE_DIV = log(TOP_SPEED_POSITIVE)/log(ITER_TO_STOP)
    # TOLERANCE BEFORE CHANGE DIRECTION
    TOLERANCE_POSITIVE = 1
    TOLERANCE_NEGATIVE = -TOLERANCE_POSITIVE
    

    '''
    ===================
    Omniparam
    ===================
    '''
    # tolerance magnitude untuk dikonsider diem
    TOL_MAG = 1e-4

    def __init__(self, space, position, color) -> None:
        super().__init__(space, position, self.RADIUS, self.MASS, self.ELASTICITY, self.PIVOT_MAX_FORCE, color)
        # 1 mean pos, 0 mean no move, -1 mean neg
        self.direction = [0,0]
    '''
    ============
       FORCE
    ============
    '''

    def _apply_force(self, force_vec):
        # print('ap', force_vec, self.body.center_of_gravity)
        # self.body.apply_force_at_local_point(force_vec, (self.body.center_of_gravity))
        self.body.apply_force_at_local_point(force_vec, (0,0))
        self.cap_vel()

    def move_up(self, force_magnitude=100):
        self._apply_force((0.0, -force_magnitude))
    
    def move_down(self, force_magnitude=100):
        self._apply_force((0.0, force_magnitude))
    
    def move_left(self, force_magnitude=100):
        self._apply_force((-force_magnitude, 0.0))

    def move_right(self, force_magnitude=100):
        self._apply_force((force_magnitude, 0.0))
    
    def cap_magnitude(self, val, max_val, min_val):
        val = min(val, max_val)
        val = max(val, min_val)
        return val
    
    def cap_vel(self):
        capped_vel_x = self.cap_magnitude(self.body.velocity[0], self.TOP_SPEED_POSITIVE, self.TOP_SPEED_NEGATIVE)
        capped_vel_y = self.cap_magnitude(self.body.velocity[1], self.TOP_SPEED_POSITIVE, self.TOP_SPEED_NEGATIVE)
        self.body._set_velocity((capped_vel_x, capped_vel_y))
    
    def set_velocity(self, vx, vy):
        vx = self.cap_magnitude(vx, self.TOP_SPEED_POSITIVE, self.TOP_SPEED_NEGATIVE)
        vy = self.cap_magnitude(vy, self.TOP_SPEED_POSITIVE, self.TOP_SPEED_NEGATIVE)
        self.body._set_velocity((vx, vy))
    
    '''
    =====================
      DISCRETE VELOCITY 
    =====================
    '''

    def calc_vel_positive(self, vel, axis):
        # cek apa sedang ke arah berlawanan
        if(vel < self.TOLERANCE_NEGATIVE):
            vel /=self.BRAKE_DIV
        else:
            vel += self.VEL_MAG
            self.direction[axis]=1
            vel = min(vel, self.TOP_SPEED_POSITIVE)
        return vel

    def calc_vel_negative(self, vel, axis):
        # cek apa sedang ke arah berlawanan
        if(vel > self.TOLERANCE_POSITIVE):
            vel /=self.BRAKE_DIV
        else:
            vel -= self.VEL_MAG
            self.direction[axis]=-1
            vel = max(vel, self.TOP_SPEED_NEGATIVE)
        return vel

    def move_up_vel(self):
        Vx, Vy = self.body.velocity
        Vy = self.calc_vel_negative(Vy, 1)
        self.body._set_velocity((Vx, Vy))
    
    def move_down_vel(self):
        Vx, Vy = self.body.velocity
        Vy = self.calc_vel_positive(Vy, 1)
        self.body._set_velocity((Vx, Vy))
    
    def move_left_vel(self):
        Vx, Vy = self.body.velocity
        Vx = self.calc_vel_negative(Vx, 0)
        self.body._set_velocity((Vx, Vy))
    
    def move_right_vel(self):
        Vx, Vy = self.body.velocity
        Vx = self.calc_vel_positive(Vx, 0)
        self.body._set_velocity((Vx, Vy))
    
    def move_timur_laut_vel(self):
        self.move_right_vel()
        self.move_up_vel()

    def move_barat_laut_vel(self):
        self.move_left_vel()
        self.move_up_vel()

    def move_tenggara_vel(self):
        self.move_right_vel()
        self.move_down_vel()

    def move_barat_daya_vel(self):
        self.move_left_vel()
        self.move_down_vel()

    # nge solve kapan harus ngerem
    def solve(self):
        dirX, dirY = self.direction
        Vx, Vy = self.body.velocity
        if(dirX==0):
            Vx /= self.BRAKE_DIV
            if(abs(Vx) < self.TOLERANCE_POSITIVE):
                Vx = 0.0
        
        if(dirY==0):
            Vy /= self.BRAKE_DIV
            if(abs(Vy) < self.TOLERANCE_POSITIVE):
                Vy = 0.0
        
        # reset direction
        self.direction[0]=0
        self.direction[1]=0

        # set velocity
        self.body._set_velocity((Vx, Vy))
    
    '''
    ==========================
    Semi Omnipotent Velocity
    ==========================
    '''
    # def calculate_final_vel(self, curVel, addVel, axis):
    #     # cek apa mereka selaras
    #     curVel_isPositive = curVel > 0.0
    #     addVel_isPositive = addVel > 0.0
    #     if(curVel_isPositive == addVel_isPositive):
    #         # ok selaras
    #         return curVel
    #     else:
    #         print('no')
    
    # def control_velocity(self, Vx, Vy):
    #     # kalau dibawah threshold tolerance gerak
    #     if(abs(Vx) < self.TOL_MAG):
    #         Vx = 0.0
    #         self.direction[0]=0
    #     else:
    #         Vx = self.move_velocity(Vx, 0)

    #     if(abs(Vy) < self.TOL_MAG):
    #         Vy = 0.0
    #         self.direction[1]=0
    #     else:
    #         Vy = self.move_velocity

    # ganti arah 1 axis
    def change_direction(self, vel, axis):
        if(abs(vel) < self.TOL_MAG):
            self.direction[axis]=0
        elif(vel > self.TOL_MAG):
            self.direction[axis]=1
        else:
            self.direction[axis]=-1
    
    # ganti arah semua axis
    def update_direction(self):
        Vx, Vy = self.body.velocity
        self.change_direction(Vx, 0)
        self.change_direction(Vy, 1)

    # simpler approach, just add the vel to this one
    def change_velocity(self, Vx, Vy):
        curVx, curVy = self.body.velocity
        curVx += Vx
        curVx = max(self.TOP_SPEED_NEGATIVE, min(curVx, self.TOP_SPEED_POSITIVE))
        # uu curvyy~~~
        curVy += Vy
        curVy = max(self.TOP_SPEED_NEGATIVE, min(curVy, self.TOP_SPEED_POSITIVE))
        self.body._set_velocity((curVx, curVy))

        self.update_direction()
        


