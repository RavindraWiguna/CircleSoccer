import pygame
import pymunk
import pymunk.pygame_util
from ball import Ball
from player import Player
from math_util import *

### === PYGAME SETUP === ###
pygame.init()
MULT = 8
WIDTH, HEIGHT = 160*MULT, 95*MULT
window = pygame.display.set_mode((WIDTH, HEIGHT))
bg = pygame.image.load('assets/images/bg.png')
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))


### === PYMUNK SETUP === ###
# make space where we will simulate
space = pymunk.Space()
static_body = space.static_body
# add gravity direction (x,y)
# space.gravity = (0.0, 480) # could be 9.81 just different speed
draw_options = pymunk.pygame_util.DrawOptions(window)

def draw(space, window, draw_options, objs):
    # window.fill('white')
    window.blit(bg, (0,0))
    # space.debug_draw(draw_options)
    for obj in objs:
        obj.draw(window)


def create_boundaries(space, width, height):
    # format: cx,cy, w,h
    mid_width = width/2
    mid_height = height/2
    rects = [
        # top wall
        [(mid_width, 5), (width, 10)],
        
        # bottom wall
        [(mid_width, height-5), (width, 10)],

        # left wall
        [(5, mid_height), (10, height)],

        # right wall
        [(width-5, mid_height), (10, height)]
    ]
    for pos, size in rects:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = pos

        shape = pymunk.Poly.create_box(body, size)
        shape.elasticity = 0.9
        # shape.friction = 0.9
        shape.color = (128, 8, 8, 100)
        space.add(body, shape)


def run(window, width, height):
    isRun = True
    clock = pygame.time.Clock()
    fps = 120
    step=1
    dt = 1/(step*fps)

    ### === pymunk setup === ###
    # sample object
    # ball = create_ball(space, 24, 5, (WIDTH/2,HEIGHT/2))
    ball = Ball(space, (width/2, height/2))
    team_a_1 = Player(space, (50, height/2), (200, 100, 0, 100))
    # ball = CircleObject(space, (width/2, height/2), 24, 5)
    create_boundaries(space, width, height)

    # isAiming=False
    while isRun:
        force_magnitude=7500
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
            force_magnitude=15000
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

        for _ in range(step):
            space.step(dt)
        draw(space, window, draw_options, [ball, team_a_1])
        pygame.display.update()
        clock.tick(fps)

        

    
    pygame.quit()


if __name__ == '__main__':
    run(window, WIDTH, HEIGHT)