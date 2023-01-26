import pygame
import pymunk
import pymunk.pygame_util

from ball import Ball
from player import Player
from gameobject import RectObject
from enums import CollisionType, GamePhase
from math_util import *

import time

### === PYGAME SETUP === ###
pygame.init()
MULT = 8
WIDTH, HEIGHT = 160*MULT, 95*MULT
window = pygame.display.set_mode((WIDTH, HEIGHT))
bg = pygame.image.load('assets/images/bg.png')
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
SCORE_FONT = pygame.font.SysFont('magneto', 40)
score_data = {'A':0,'B':0}
game_phase = GamePhase.Normal

### === PYMUNK SETUP === ###
# make space where we will simulate
space = pymunk.Space()
static_body = space.static_body
draw_options = pymunk.pygame_util.DrawOptions(window)

### === DRAWING FUNCTIONS === ###

def draw_score(window, a, b):
    pygame.draw.rect(window, (255, 255, 255), (WIDTH/2-90, 0, 180, 50))
    score_text = SCORE_FONT.render(f'{a:02d} : {b:02d}', 1, (16, 16, 16))
    window.blit(score_text, (WIDTH/2-85, 10))

def draw(space, window, draw_options, objs, score_data):
    # window.fill('white')
    window.blit(bg, (0,0))
    draw_score(window, score_data['A'], score_data['B'])
    # space.debug_draw(draw_options)
    for obj in objs:
        obj.draw(window)


### === GAME SPECIFIC FUNCTIONS === ###

def create_boundaries(space, width, height, bwidth):
    # format: cx,cy, w,h
    mid_width = width/2
    mid_height = height/2
    rects = [
        # top wall
        [(mid_width, bwidth/2), (width, bwidth)],
        
        # bottom wall
        [(mid_width, height-bwidth/2), (width, bwidth)],

        # left wall
        [(bwidth/2, mid_height), (bwidth, height)],

        # right wall
        [(width-bwidth/2, mid_height), (bwidth, height)]
    ]
    for pos, size in rects:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = pos

        shape = pymunk.Poly.create_box(body, size)
        shape.elasticity = 0.9
        shape.friction = 0.5
        shape.color = (128, 8, 8, 100)
        space.add(body, shape)

def goal_a_handler(arbiter, space, data):
    global score_data, game_phase
    if(game_phase==GamePhase.Normal):
        score_data['B']+=1
        game_phase=GamePhase.JUST_GOAL

    return True

def goal_b_handler(arbiter, space, data):
    global score_data, game_phase
    if(game_phase==GamePhase.Normal):
        score_data['A']+=1
        game_phase=GamePhase.JUST_GOAL
    return True

def reset_objects(objs):
    for obj in objs:
        obj.reset()

def reset_score():
    global score_data
    score_data['A']=0
    score_data['B']=0

### ==== MAIN FUNCTION ==== ###

def run(window, width, height):
    global game_phase
    '''
    =============================
      PYGAME-PYMUNK LOOP SETUP
    =============================
    '''
    isRun = True
    clock = pygame.time.Clock()
    fps = 120
    step=1
    dt = 1/(step*fps)

    '''
    ======================================
           SPAWN GAME'S OBJECTS
    ======================================
    '''
    # BORDER FOR BOUNCE
    wall_width=4
    create_boundaries(space, width, height, wall_width)
    
    # GAME'S BALL
    ball = Ball(space, (width/2, height/2))
    ball.shape.collision_type=CollisionType.BALL.value
    
    # GOALS variable
    height_goal = 175
    width_goal=6
    width_tiang=48
    height_tiang=width_goal
    goal_a = [
        # vertical sensor
        RectObject(space, (wall_width+width_goal/2, height/2), (width_goal, height_goal), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100)),
        
        # tiang bawah
        RectObject(space, (wall_width+width_tiang/2, height/2+height_goal/2+height_tiang/2), (width_tiang, height_tiang), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100)),

        # tiang atas
        RectObject(space, (wall_width+width_tiang/2, height/2-height_goal/2-height_tiang/2), (width_tiang, height_tiang), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100))
    ]

    goal_a[0].shape.collision_type=CollisionType.GOAL_A.value
    print(ball.shape.collision_type, goal_a[0].shape.collision_type)
    goal_a_sensor = space.add_collision_handler(ball.shape.collision_type, goal_a[0].shape.collision_type)
    goal_a_sensor.begin=goal_a_handler

    offsetb=-6
    goal_b = [
        # vertical sensor
        RectObject(space, (width-wall_width-width_goal/2+offsetb, height/2), (width_goal, height_goal), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100)),
        
        # tiang bawah
        RectObject(space, (width-wall_width-width_tiang/2+offsetb, height/2+height_goal/2+height_tiang/2), (width_tiang, height_tiang), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100)),

        # tiang atas
        RectObject(space, (width-wall_width-width_tiang/2+offsetb, height/2-height_goal/2-height_tiang/2), (width_tiang, height_tiang), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100))
    ]

    goal_b[0].shape.collision_type=CollisionType.GOAL_B.value
    print(ball.shape.collision_type, goal_b[0].shape.collision_type)
    goal_b_sensor = space.add_collision_handler(ball.shape.collision_type, goal_b[0].shape.collision_type)
    goal_b_sensor.begin=goal_b_handler


    ## === TEAM A === LEFT IS THE RIGHT SIDE!
    COLOR_A = (200, 100, 0, 100)
    team_A = [
        # keeper (ceritanya)
        Player(space, (width/8, height/2), COLOR_A),
        
        # left wing 
        Player(space, (width/8*3, height/4), COLOR_A),

        # right wing
        Player(space, (width/8*3, height/4*3), COLOR_A),
    ]
    team_A[0].shape.collision_type=CollisionType.A_P1.value
    team_A[1].shape.collision_type=CollisionType.A_P2.value
    team_A[1].shape.collision_type=CollisionType.A_P3.value


    COLOR_B = (0, 100, 200, 100)
    team_B = [
        # keeper (ceritanya)
        Player(space, (width/8*7, height/2), COLOR_B),
        
        # left wing 
        Player(space, (width/8*5, height/4), COLOR_B),

        # right wing
        Player(space, (width/8*5, height/4*3), COLOR_B),
    ]
    team_B[0].shape.collision_type=CollisionType.B_P1.value
    team_B[1].shape.collision_type=CollisionType.B_P2.value
    team_B[1].shape.collision_type=CollisionType.B_P3.value

    '''
    ========================
            MAIN LOOP
    ========================
    '''
    min_dim = min(width, height)
    norm_div = min_dim/2
    start_time_after_goal=None
    wait_after_goal=1.5
    while isRun:
        force_magnitude=2000
        for event in pygame.event.get():
            if(event.type== pygame.QUIT):
                isRun=False
                break

        keys = pygame.key.get_pressed()
        if(game_phase==GamePhase.Normal):
            if(keys[pygame.K_LSHIFT]):
                force_magnitude=18000
            if(keys[pygame.K_UP]):
                team_A[0].move_up(force_magnitude)
            elif(keys[pygame.K_DOWN]):
                team_A[0].move_down(force_magnitude)
                # print("down")
            if(keys[pygame.K_LEFT]):
                team_A[0].move_left(force_magnitude)
                # print("left")
            elif(keys[pygame.K_RIGHT]):
                team_A[0].move_right(force_magnitude)
            
            if(keys[pygame.K_SPACE]):
                brake_force = -team_A[0].body.velocity * team_A[0].body.mass * 1.5
                team_A[0]._apply_force(brake_force)

        # for _ in range(step):
        print(team_A[0].body.velocity)
        space.step(dt)
        draw(space, window, draw_options, [ball, *team_A, *team_B, *goal_a, *goal_b], score_data)
        pygame.display.update()
        clock.tick(fps)

        if(game_phase==GamePhase.JUST_GOAL):
            if(start_time_after_goal is None):
                start_time_after_goal=time.perf_counter()
            
            # jika melebihi 3 detik setelah goal (yes pakek if because if training.. uhh..., mengding gpp stpi skip 1.0)
            if(time.perf_counter()-start_time_after_goal >= wait_after_goal):
                # restart ronde
                reset_objects([ball, *team_A, *team_B])
                game_phase=GamePhase.Normal
                start_time_after_goal=None



        

    
    pygame.quit()


if __name__ == '__main__':
    run(window, WIDTH, HEIGHT)