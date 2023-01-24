import pygame
import pymunk
import pymunk.pygame_util
from ball import Ball
from player import Player
from math_util import *
from gameobject import RectObject

### === PYGAME SETUP === ###
pygame.init()
MULT = 8
WIDTH, HEIGHT = 160*MULT, 95*MULT
window = pygame.display.set_mode((WIDTH, HEIGHT))
bg = pygame.image.load('assets/images/bg.png')
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
SCORE_FONT = pygame.font.SysFont('magneto', 40)

### === PYMUNK SETUP === ###
# make space where we will simulate
space = pymunk.Space()
static_body = space.static_body
# add gravity direction (x,y)
# space.gravity = (0.0, 480) # could be 9.81 just different speed
draw_options = pymunk.pygame_util.DrawOptions(window)

def draw_score(window, a, b):
    pygame.draw.rect(window, (255, 255, 255), (WIDTH/2-90, 0, 180, 50))
    score_text = SCORE_FONT.render(f'{a:02d} : {b:02d}', 1, (16, 16, 16))
    window.blit(score_text, (WIDTH/2-85, 10))

def draw(space, window, draw_options, objs):
    # window.fill('white')
    window.blit(bg, (0,0))
    draw_score(window, 0, 0)
    # space.debug_draw(draw_options)
    for obj in objs:
        obj.draw(window)


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


def run(window, width, height):
    isRun = True
    clock = pygame.time.Clock()
    fps = 120
    step=1
    dt = 1/(step*fps)

    ### === game object setup/spawn === ###
    wall_width=4
    create_boundaries(space, width, height, wall_width)
    
    ball = Ball(space, (width/2, height/2))
    
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

    offsetb=-6
    goal_b = [
        # vertical sensor
        RectObject(space, (width-wall_width-width_goal/2+offsetb, height/2), (width_goal, height_goal), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100)),
        
        # tiang bawah
        RectObject(space, (width-wall_width-width_tiang/2+offsetb, height/2+height_goal/2+height_tiang/2), (width_tiang, height_tiang), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100)),

        # tiang atas
        RectObject(space, (width-wall_width-width_tiang/2+offsetb, height/2-height_goal/2-height_tiang/2), (width_tiang, height_tiang), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100))
    ]

    team_a_1 = Player(space, (50, height/2), (200, 100, 0, 100))


    # isAiming=False
    min_dim = min(width, height)
    norm_div = min_dim/2
    while isRun:
        force_magnitude=9000
        for event in pygame.event.get():
            if(event.type== pygame.QUIT):
                isRun=False
                break
                
            # elif(event.type==pygame.MOUSEBUTTONDOWN):
            #     if(not isAiming):
            #         # check if player a is clicked
            #         dplayer = calculate_distance(team_a_1.body.position, event.pos)
            #         if(dplayer<=team_a_1.radius):
            #             isAiming=True

            # elif(event.type==pygame.MOUSEBUTTONUP):
            #     if(isAiming):
            #         isAiming=False
                    
            #         # add force
            #         angle = calculate_angle(event.pos, team_a_1.body.position)
            #         magnitude = calculate_distance(event.pos, team_a_1.body.position)*40
            #         fx=np.cos(angle)*magnitude
            #         fy=np.sin(angle)*magnitude
            #         team_a_1.body.apply_impulse_at_local_point((fx, fy), (0,0))

        keys = pygame.key.get_pressed()
        if(keys[pygame.K_LSHIFT]):
            force_magnitude=18000
        if(keys[pygame.K_UP]):
            team_a_1.move_up(force_magnitude)
        elif(keys[pygame.K_DOWN]):
            team_a_1.move_down(force_magnitude)
            # print("down")
        if(keys[pygame.K_LEFT]):
            team_a_1.move_left(force_magnitude)
            # print("left")
        elif(keys[pygame.K_RIGHT]):
            team_a_1.move_right(force_magnitude)
        
        if(keys[pygame.K_SPACE]):
            brake_force = -team_a_1.body.velocity * team_a_1.body.mass * 1.5
            team_a_1._apply_force(brake_force)

        # for _ in range(step):
        space.step(dt)
        draw(space, window, draw_options, [ball, team_a_1, *goal_a, *goal_b])
        pygame.display.update()
        # print(team_a_1.body.angle, team_a_1.body.angular_velocity) no change
        # print(team_a_1.body.moment) no change
        # print(team_a_1.body.torque) no chnage
        # print(team_a_1.body.force) no change
        # print(team_a_1.body.velocity/norm_div) ok
        # print(team_a_1.body.position/min_dim) ok
        
        clock.tick(fps)


        

    
    pygame.quit()


if __name__ == '__main__':
    run(window, WIDTH, HEIGHT)