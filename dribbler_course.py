import pygame
import pymunk
import pymunk.pygame_util

from ball import Ball
from player import Player
from gameobject import RectObject
from enums import CollisionType, GamePhase
from math_util import *

import time
import os
import random
from functools import partial
import neat
from neatUtils import visualize

### === PYGAME SETUP === ###
pygame.init()
MULT = 8
WIDTH, HEIGHT = 160*MULT, 95*MULT
min_dim = min(WIDTH, HEIGHT)
norm_div = min_dim/2
constant = 2/min_dim
max_distance_possible = calculate_distance((0,0), (WIDTH, HEIGHT))
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

def clear_screen(window):
    window.blit(bg, (0,0))

def draw(window, objs, score_data, space=None, drawing_options=None, isDebug=False):
    draw_score(window, score_data['A'], score_data['B'])
    
    if(isDebug):
        space.debug_draw(drawing_options)
    else:
        for obj in objs:
            obj.draw(window)

def draw_ball_vec_vel(window, ball):
    Px, Py = ball.body.position
    maxMag = max(abs(Vx), abs(Vy)) + 1
    Vx /= maxMag
    Vy /= maxMag
    end_position = (Px + Vx*100, Py + Vy*100)
    pygame.draw.line(window, (16, 128, 128), ball.body.position, end_position, 5)

def draw_ball_to_goal_line(window, ball, opo_goal):
    Px, Py = ball.body.position
    gPx, gPy = opo_goal.body.position
    distance = calculate_distance((Px, Py), (gPx, gPy))    
    Dx = (gPx - Px)/distance
    Dy = (gPy - Py)/distance
    end_position = (Px + Dx*100, Py + Dy*100)
    pygame.draw.line(window, (16, 16, 16), ball.body.position, end_position, 5)

### === GAME SPECIFIC FUNCTIONS === ###
def create_boundaries(space, width, height, bwidth):
    # format: cx,cy, w,h
    mid_width = width/2
    mid_height = height/2
    offset = bwidth/3
    rects = [
        # top wall
        [(mid_width, -offset), (width, bwidth), CollisionType.WALL_TOP.value],
        
        # bottom wall
        [(mid_width, height+offset), (width, bwidth), CollisionType.WALL_BOTTOM.value],

        # left wall
        [(-offset, mid_height), (bwidth, height), CollisionType.WALL_LEFT.value],

        # right wall
        [(width+offset, mid_height), (bwidth, height), CollisionType.WALL_RIGHT.value]
    ]
    for pos, size, coltype in rects:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = pos

        shape = pymunk.Poly.create_box(body, size)
        shape.elasticity = 0.9
        shape.friction = 0.5
        shape.color = (128, 8, 8, 100)
        space.add(body, shape)
        shape.collision_type=coltype


def make_slopes(space, width, height, n, bwidth, goal_right_top, goal_right_bottom, goal_left_top, goal_left_bottom, width_tiang):    
    const_val = n+bwidth

    # goal-right-top-center-x, goal-right-top-center-y
    grtcx, grtcy = goal_right_top
    grbcx, grbcy = goal_right_bottom
    gltcx, gltcy = goal_left_top
    glbcx, glbcy = goal_left_bottom

    hw = width_tiang/2

    slopes = [
        # top left
        [(n, 0),(const_val, 0), (0, const_val), (0, n)],

        # bottom left
        [(0,height-const_val), (0, height-n), (n, height), (const_val, height)],

        # top right
        [(width-n, 0),(width-const_val, 0), (width, const_val), (width, n)],

        # bottom right
        [(width-const_val, height),(width-n, height), (width, height-n), (width, height-const_val)],

        # goal right-top (or rigt-left uh, i confuse and once said top is left di kode bagian bawah, so 2 phrase 1 arti)
        [(grtcx-hw, grtcy),(grtcx+bwidth-hw, grtcy), (width, grtcy-width_tiang), (width, grtcy-width_tiang-bwidth)],

        # goal right bottom
        [(grbcx-hw, grbcy), (grbcx+bwidth-hw, grbcy), (width, grbcy+width_tiang), (width, grbcy+width_tiang+bwidth)],

        # goal left top
        [(gltcx+hw, gltcy),(gltcx+hw+bwidth, gltcy), (0, gltcy+width_tiang), (0, gltcy+width_tiang+bwidth)],

        # goal left bottom
        [(glbcx+hw, glbcy), (glbcx+hw+bwidth, glbcy), (0, glbcy-width_tiang), (0, glbcy-width_tiang-bwidth)]

    ]

    for poly in slopes:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        # print(poly)
        shape = pymunk.Poly(body, poly)
        shape.elasticity = 0.9
        shape.color = (128, 8, 8, 100)
        space.add(body, shape)


'''
=====================
   SEPAK BOLA FUNC
=====================
'''
def isTeamA(id):
    return id < 6 and id > 0

def isTeamB(id):
    return id > 6


def ball_touch_handler(collision_type_toucher, arbiter, space, data):
    global just_sentuh
    just_sentuh=True #ONLY WORK IF SOLO, karna 1 yg di observe
    return True

# make partial func
team_a1_ball_handler = partial(ball_touch_handler, CollisionType.A_P1.value)
team_a2_ball_handler = partial(ball_touch_handler, CollisionType.A_P2.value)
team_a3_ball_handler = partial(ball_touch_handler, CollisionType.A_P3.value)

team_b1_ball_handler = partial(ball_touch_handler, CollisionType.B_P1.value)
team_b2_ball_handler = partial(ball_touch_handler, CollisionType.B_P2.value)
team_b3_ball_handler = partial(ball_touch_handler, CollisionType.B_P3.value)

'''
==============
  GAME UTIL
==============
'''

def reset_objects(objs):
    for obj in objs:
        obj.reset()

def reset_score():
    global score_data
    score_data['A']=0
    score_data['B']=0

def kick_player(player):
    player.body._set_position((-250,-250))

def get_player_team_goal(team_A, team_B, goal_a, goal_b, asA):
    if(asA):
        player = team_A[0]
        self_team=team_A
        opo_team=team_B
        self_goal=goal_a
        opo_goal=goal_b
    else:
        player = team_B[0]
        self_team=team_B
        opo_team=team_A
        self_goal=goal_b
        opo_goal=goal_a
    
    return player, self_team, opo_team, self_goal, opo_goal

'''
=======================
  GAME TERMINATION UTL
=======================
'''
def out_of_bound_check(objs, width, height):
    existOutOfBound=False
    for obj in objs:
        px, py = obj.body.position
        # print(px, py)
        if(px < -10 or py < -10 or px > width or py > height):
            # endgame_fitness() keluar juga ga dikasi reward
            existOutOfBound=True
            print(obj.body.velocity)
            print('out of bound with tolerance')
            break
    
    return existOutOfBound

def wall_collision_handler(offset_id_wall, offset_id_toucher, arbiter, space, data):
    global isHitWall
    isHitWall[offset_id_wall+offset_id_toucher]=1
    # print(offset_id_toucher, 'touch', offset_id_wall)
    return True

# make partial func for wall
top_wall_hit_handler    = partial(wall_collision_handler, 0)
bottom_wall_hit_handler = partial(wall_collision_handler, 6)
left_wall_hit_handler   = partial(wall_collision_handler, 12)
right_wall_hit_handler  = partial(wall_collision_handler, 18)
goal_a_hit_handler      = partial(wall_collision_handler, 24)
goal_b_hit_handler      = partial(wall_collision_handler, 30)

# make partial func for collision each player
team_a1_twall_handler = partial(top_wall_hit_handler, 0)
team_a2_twall_handler = partial(top_wall_hit_handler, 1)
team_a3_twall_handler = partial(top_wall_hit_handler, 2)
team_b1_twall_handler = partial(top_wall_hit_handler, 3)
team_b2_twall_handler = partial(top_wall_hit_handler, 4)
team_b3_twall_handler = partial(top_wall_hit_handler, 5)

team_a1_bwall_handler = partial(bottom_wall_hit_handler, 0)
team_a2_bwall_handler = partial(bottom_wall_hit_handler, 1)
team_a3_bwall_handler = partial(bottom_wall_hit_handler, 2)
team_b1_bwall_handler = partial(bottom_wall_hit_handler, 3)
team_b2_bwall_handler = partial(bottom_wall_hit_handler, 4)
team_b3_bwall_handler = partial(bottom_wall_hit_handler, 5)

team_a1_lwall_handler = partial(left_wall_hit_handler, 0)
team_a2_lwall_handler = partial(left_wall_hit_handler, 1)
team_a3_lwall_handler = partial(left_wall_hit_handler, 2)
team_b1_lwall_handler = partial(left_wall_hit_handler, 3)
team_b2_lwall_handler = partial(left_wall_hit_handler, 4)
team_b3_lwall_handler = partial(left_wall_hit_handler, 5)

team_a1_rwall_handler = partial(right_wall_hit_handler, 0)
team_a2_rwall_handler = partial(right_wall_hit_handler, 1)
team_a3_rwall_handler = partial(right_wall_hit_handler, 2)
team_b1_rwall_handler = partial(right_wall_hit_handler, 3)
team_b2_rwall_handler = partial(right_wall_hit_handler, 4)
team_b3_rwall_handler = partial(right_wall_hit_handler, 5)

team_a1_gawall_handler = partial(goal_a_hit_handler, 0)
team_a2_gawall_handler = partial(goal_a_hit_handler, 1)
team_a3_gawall_handler = partial(goal_a_hit_handler, 2)
team_b1_gawall_handler = partial(goal_a_hit_handler, 3)
team_b2_gawall_handler = partial(goal_a_hit_handler, 4)
team_b3_gawall_handler = partial(goal_a_hit_handler, 5)

team_a1_gbwall_handler = partial(goal_b_hit_handler, 0)
team_a2_gbwall_handler = partial(goal_b_hit_handler, 1)
team_a3_gbwall_handler = partial(goal_b_hit_handler, 2)
team_b1_gbwall_handler = partial(goal_b_hit_handler, 3)
team_b2_gbwall_handler = partial(goal_b_hit_handler, 4)
team_b3_gbwall_handler = partial(goal_b_hit_handler, 5)

# kalau tembok atas 1, bawah = 2, kiri = 4, kanan = 8, gak kena = 0 (semua bit mati) 
# ( tapi ya gak mungkin semua bit nyala, atas bawah nyala impos)
def detect_kena_tembok(position):
    '''
    bahaya kalo ganti width length but for now gud
    '''
    x, y = position
    
    sensor = 0
    # tembok ci- i mean atas-bawah:
    if(y < 30.0):
        # atas
        sensor +=1
    elif(y > 730):
        # bawah
        sensor +=2
    
    # tembok kiri kanan
    if(x < 77):
        # di kiri gawang or tembok kiri
        sensor += 4
    elif(x > 1196):
        # kanan, gawang or tembok kanan
        sensor +=8
    
    return sensor

def judge_wall_hit(isNabrakTop, isNabrakBottom, isNabrakLeft, isNabrakRight, dirX, dirY):
    # top wall only
    if(isNabrakTop and dirX==0):
        # nyentuh dan nabrak but gak gerak kiri kanan
        return True
    
    # bottom wall only
    if(isNabrakBottom and dirX==0):
        return True

    # left wall only
    if(isNabrakLeft and dirY==0):
        return True

    # right wall only
    if(isNabrakRight and dirY==0):
        return True
    
    # top/bottom and left/right
    if((isNabrakTop or isNabrakBottom) and (isNabrakRight or isNabrakLeft)):
        return True

    # gak semua
    return False

# player id udah include sama tim, 0-5
def check_wall_hit_based_collision(player_id, player:Player):
    global isHitWall
    topoff, botoff, leftoff, rightoff, gaoff, gboff = 0,6,12,18, 24, 30
    dirX, dirY = player.direction
    isNabrakTop = isHitWall[topoff+player_id]==1 and (dirY==-1)
    isNabrakBottom = isHitWall[botoff+player_id]==1 and( dirY==1)
    isNabrakLeft = isHitWall[leftoff+player_id]==1 and (dirX == -1)
    isNabrakRight = isHitWall[rightoff+player_id]==1 and (dirX ==1)
    # print('c|', isNabrakTop, isNabrakBottom, isNabrakLeft, isNabrakRight,'|', dirX, dirY,'|', player.body.velocity)
    classic_wall_hit = judge_wall_hit(isNabrakTop, isNabrakBottom, isNabrakLeft, isNabrakRight, dirX, dirY)
    if(classic_wall_hit):
        return classic_wall_hit

    # goal judge
    isNabrakGoalA = isHitWall[gaoff+player_id]==1 and (dirX == -1)
    isNabrakGoalB = isHitWall[gboff+player_id]==1 and (dirX ==  1)

    goal_hit = judge_wall_hit(False, False, isNabrakGoalA, isNabrakGoalB, dirX, dirY)
    return goal_hit


# make sur to check theez nut, imean coor
def check_wall_hit_based_coor(player:Player):
    bit_top, bit_bottom, bit_left, bit_right = 1,2,4,8
    position = player.body.position
    dirX, dirY = player.direction
    sensor = detect_kena_tembok(position)
    isNabrakTop = (sensor & bit_top) and( dirY==-1)
    isNabrakBottom = (sensor & bit_bottom) and (dirY==1)
    isNabrakLeft = (sensor & bit_left) and (dirX == -1)
    isNabrakRight = (sensor & bit_right) and (dirX ==1)
    # print('s|', isNabrakTop, isNabrakBottom, isNabrakLeft, isNabrakRight,'|', dirX, dirY)
    return judge_wall_hit(isNabrakTop, isNabrakBottom, isNabrakLeft, isNabrakRight, dirX, dirY)

'''
return true if above threshold
''' 
def check_velocity(velocity, threshold, isEuclid=False):
    vx, vy = velocity
    if(not isEuclid):
        if(abs(vx)+abs(vy) > threshold):
            return True
        return False
    else:
        if(calculate_distance((0,0), velocity) > threshold):
            return True
        return False

def check_force(force, threshold):
    fx, fy = force
    total_mag = calculate_distance((0,0), (fx, fy))
    if(total_mag > threshold):
        return True
    return False


def checkAllStandStill(players, ball, doWallCheck):
    existMovement=False
    vel_threshold = 1e-6

    for index, obj in players:            
        existMovement = check_velocity(obj.body.velocity, vel_threshold)
        if(existMovement):
            # cek apa gerak tapi nabrak tembok
            # isHittingWall_cor = check_wall_hit_based_coor(obj)
            isHittingWall_col = check_wall_hit_based_collision(index, obj)
            # isHittingWall = check_wall_hit_based_collision(index, obj)
            if(isHittingWall_col ):
                existMovement=False

        # kalau lewat 2 2 nya ok ada gerakan        
        if(existMovement):break
    
    ### END OF FOR LOOP ###

    # kalau player gak gerak, cek bola
    if(not existMovement):
        ball_vel_good = check_velocity(ball.body.velocity, vel_threshold)
        existMovement=ball_vel_good

    return existMovement

def check_ball_ngeliwat_gawang(ball, width, width_tiang):
    if(ball.body.position[0] <= width_tiang or ball.body.position[0] > (width-width_tiang)):
        return True
    
    return False


def player_is_gerak_menjauh(player, ball, threshold_player_vel, threshold_angle, threshold_ok_distance):
    angle_vec = get_ball_vec_angle(player) # trick player as a ball
    angle_goal = get_ball_to_goal_angle(player, ball) # trick ball as goal
    dtetha = calculate_diff_angle(angle_goal, angle_vec, False)
    if(dtetha > threshold_angle and check_velocity(player.body.velocity, threshold_player_vel, True)):
        distance_to_ball = calculate_distance(player.body.position, ball.body.position)
        if(distance_to_ball > threshold_ok_distance):
            return True
    
    return False

'''
==================
   AI INPUT UTIL
=================
'''

def get_ball_pos_vel(ball, constant, norm_vel_div):
    ball_datas = []
    x,y = ball.body.position
    x = -1 + (x * constant)
    y = -1 + (y  * constant)

    vx, vy = ball.body.velocity/norm_vel_div
    ball_datas.extend([x,y, vx, vy])
    return ball_datas

def get_player_pos_vel(body, constant, norm_vel_div):
    x,y = body.position
    x = -1 + (x * constant)
    y = -1 + (y  * constant) # yes ttp pakek max x

    vx, vy = body.velocity/norm_vel_div
    return [x,y, vx, vy]


def get_team_pos_vel(team, skip_id, min_dim, norm_vel_div):
    team_mate_pos_vel = []
    constant = 2/min_dim
    for i, player in enumerate(team):
        if(i == skip_id):
            continue
        
        x,y,vx,vy = get_player_pos_vel(player.body, constant, norm_vel_div)
        team_mate_pos_vel.extend([x,y,vx,vy])
    
    return team_mate_pos_vel
    

def get_boundary_distance(position, max_x, max_y, constant):
    # top wall -> sama dgn y koor
    # ---
    
    # left wall -> sama dgn x koor
    # ---

    # bottom wall
    d_bottom = max_y - position[1]
    d_bottom *= constant

    # right wall
    d_right = max_x - position[0]
    d_right *= constant
    return [d_bottom, d_right]

def get_position_distance(src_pos, dst_pos, constant):
    dx = dst_pos[0]-src_pos[0]
    dy = dst_pos[1]-src_pos[1]
    
    dx*=constant
    dy*=constant
    return [dx, dy]

def make_data_masuk_dribble(player, ball, target_position):
    vx, vy = player.body.velocity
    px, py = player.body.position
    Bvx, Bvy = ball.body.velocity
    Bpx, Bpy = ball.body.position
    tx, ty = target_position

    bias = 0.5

    the_input = [
        px, py, vx, vy, Bpx, Bpy, Bvx, Bvy, tx, ty, bias
    ]

    return the_input

def get_random_wp(ball, distance, min_x, min_y, max_x, max_y):
    increment = np.pi/360
    tetha = 0.0
    Bx, By = ball.body.position
    pool_end = []

    while(tetha < np.pi*2):
        addX = distance*np.cos(tetha)
        addY = distance*np.sin(tetha)

        endX = Bx + addX
        endY = By + addY

        tetha += increment

        if(endX < min_x):continue
        if(endX > max_x):continue
        if(endY < min_y):continue
        if(endY > max_y):continue

        # aman
        pool_end.append((endX, endY))

    # now choose
    if(pool_end==[]):
        return ((min_x+max_x)/2, (min_y+max_y)/2)
    
    selected_wp = random.choice(pool_end)
    return selected_wp




'''
================
 AI FITNESS UTIL
================
'''
def initialize_fitness(genome):
    if(genome.fitness == None):
        genome.fitness=0.0

# FITNESS BALLZkalo mendekati bola
def calculate_ball_fitness(player, ball):
    final_distance_ball = calculate_distance(player.body.position, ball.body.position)
    max_fitness = calculate_distance((0,0), (WIDTH, HEIGHT))
    fitness = 1 - final_distance_ball/max_fitness
    fitness *=17
    return fitness

def calculate_ball_goal_fitness(opo_goal, ball):
    final_distance_goal = calculate_distance(opo_goal.body.position, ball.body.position)
    max_fitness = calculate_distance((0,0), (WIDTH, HEIGHT))
    fitness = 1 - final_distance_goal/max_fitness
    fitness *=1000
    return fitness, final_distance_goal

def get_ball_vec_angle(ball):
    Vx, Vy = ball.body.velocity
    angle = calculate_angle((0,0), (Vx, Vy))
    return angle

def get_ball_to_goal_angle(ball, opo_goal):
    Px, Py = ball.body.position
    gPx, gPy = opo_goal.body.position
    angle = calculate_angle((Px, Py), (gPx, gPy))
    return angle

'''
=================
  AI OUTPUT UTIL
=================
'''
def cap_magnitude(val, max_val, min_val):
    val = max(min_val, min(max_val, val))
    return val

# get vx vy
def process_output(output, player):
    addVx = output[0] - output[1]
    addVy = output[2] - output[3]
    # print(output)
    addVx*=10
    addVy*=10 # biar gampangan cpet
    player.change_velocity(addVx, addVy)

### ==== MAIN FUNCTION ==== ###

def game(window, width, height, genomes, config, doRandom, asA):
    global game_phase, score_data, last_ball_toucher_id, second_last_toucher, fitness_recorder, ronde_time, solo_touch_ball_counter, isHitWall, iter_to_touch, just_sentuh
    '''
    =============================
      PYGAME-PYMUNK LOOP SETUP
    =============================
    '''
    isRun = True
    clock = pygame.time.Clock()
    fps = 120
    step=5
    dt = 1/(step*fps)

    '''
    ======================================
           SPAWN GAME'S OBJECTS
    ======================================
    '''
    # BORDER FOR BOUNCE
    wall_width=50
    create_boundaries(space, width, height, wall_width)
    wall_width=4
    
    # GAME'S BALL
    ball = Ball(space, (width/2, height/2))
    ball.shape.collision_type=CollisionType.BALL.value
     
    # GOALS variable
    height_goal = 175
    width_goal=6
    width_tiang=48
    height_tiang=width_goal
    offsetb=-6

    grtc = (width-wall_width-width_tiang/2+offsetb, height/2-height_goal/2-height_tiang/2)
    grbc = (width-wall_width-width_tiang/2+offsetb, height/2+height_goal/2+height_tiang/2)
    gltc = (wall_width+width_tiang/2, height/2+height_goal/2+height_tiang/2)
    glbc = (wall_width+width_tiang/2, height/2-height_goal/2-height_tiang/2)

    goal_a = [
        # vertical sensor
        RectObject(space, (wall_width+width_goal/2, height/2), (width_goal, height_goal), 1, 0.2, 500, isDynamic=False, color=(225, 225, 225, 100)),
        
        # tiang bawah
        RectObject(space, glbc, (width_tiang, height_tiang), 1, 1, 500, isDynamic=False, color=(225, 225, 225, 100)),

        # tiang atas
        RectObject(space, gltc, (width_tiang, height_tiang), 1, 1, 500, isDynamic=False, color=(225, 225, 225, 100))
    ]

    goal_a[0].shape.collision_type=CollisionType.GOAL_A.value


    goal_b = [
        # vertical sensor
        RectObject(space, (width-wall_width-width_goal/2+offsetb, height/2), (width_goal, height_goal), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100)),
        
        # tiang bawah
        RectObject(space, grbc, (width_tiang, height_tiang), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100)),

        # tiang atas
        RectObject(space, grtc, (width_tiang, height_tiang), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100))
    ]

    goal_b[0].shape.collision_type=CollisionType.GOAL_B.value

    # anti ballz stucc
    make_slopes(space, width, height, 35, 10, grtc, grbc, gltc, glbc, width_tiang)


    ## === TEAM A === LEFT IS THE RIGHT SIDE!
    COLOR_A = (200, 100, 0, 100)
    team_A = [
        # keeper (ceritanya)
        Player(space, (width/8, height/2), COLOR_A),
    ]
    team_A[0].shape.collision_type=CollisionType.A_P1.value

    team_A_sensors = [
        # collision type, function
        [[ball.shape.collision_type, team_a1_ball_handler], [CollisionType.WALL_TOP.value, team_a1_twall_handler], 
        [CollisionType.WALL_BOTTOM.value, team_a1_bwall_handler], [CollisionType.WALL_LEFT.value, team_a1_lwall_handler],
        [CollisionType.WALL_RIGHT.value, team_a1_rwall_handler], [CollisionType.GOAL_A.value, team_a1_gawall_handler], [CollisionType.GOAL_B.value, team_a1_gbwall_handler]],
    ]
    # add collision handler to space
    for i, player_collision_stuff in enumerate(team_A_sensors):
        for coltype, function in player_collision_stuff:
            temporary = space.add_collision_handler(coltype, team_A[i].shape.collision_type)
            temporary.begin = function

    ### === TEAM B === ###
    COLOR_B = (0, 100, 200, 100)
    team_B = [
        # keeper (ceritanya)
        Player(space, (width/8*7, height/2), COLOR_B),
    ]
    team_B[0].shape.collision_type=CollisionType.B_P1.value

    team_B_sensors = [
        # collision type, function
        [[ball.shape.collision_type, team_b1_ball_handler], [CollisionType.WALL_TOP.value, team_b1_twall_handler], 
        [CollisionType.WALL_BOTTOM.value, team_b1_bwall_handler], [CollisionType.WALL_LEFT.value, team_b1_lwall_handler],
        [CollisionType.WALL_RIGHT.value, team_b1_rwall_handler],[CollisionType.GOAL_A.value, team_b1_gawall_handler], [CollisionType.GOAL_B.value, team_b1_gbwall_handler]],
    ]

    for i, player_collision_stuff in enumerate(team_B_sensors):
        for coltype, function in player_collision_stuff:
            temporary = space.add_collision_handler(coltype, team_B[i].shape.collision_type)
            temporary.begin = function

    if(doRandom):
        objs = [*team_A, *team_B]
        for obj in objs:
            rx = random.uniform(100, width-100)
            ry = random.uniform(100, height-100)
            obj.body._set_position((rx, ry))

    # ball random
    cut = 0.275
    sisa = 1-cut
    rx = random.uniform(width*cut, width*sisa)
    ry = random.uniform(height*cut, height*sisa)
    ball.body._set_position((rx, ry))

    # ball target room
    cut = 0.1
    sisa = 1-cut
    ball_to_wp_init_distance = 256
    max_iter_wp = 332
    counter_iter_to_wp = 0
    wp_threshold_disance = 16
    min_x, min_y, max_x, max_y = width*cut, height*cut, width*sisa, height*sisa
    target_wp = get_random_wp(ball, ball_to_wp_init_distance, min_x, min_y, max_x, max_y)

    # kick player
    if(asA):
        need_kick = [team_B[0]]
    else:
        need_kick = [team_A[0]]
    
    for player in need_kick:
        kick_player(player)

    '''
    ====================
       Making 1 models
    ====================
    '''

    team_net = [
        (neat.nn.RecurrentNetwork.create(genomes[0][1], config), genomes[0]),
    ]

    # initlaize fitness
    for genomeid, genome in genomes:
        initialize_fitness(genome)


    '''
    ========================
            MAIN LOOP
    ========================
    '''
    # get player, self goal, opo goal, team, etc
    net, genome = team_net[0]
    player, self_team, opo_team, self_goal, opo_goal = get_player_team_goal(team_A, team_B, goal_a, goal_b, asA)
    
    player_index = 0 if asA else 3
    player_cek = [[player_index, player]]


    forceQuit=False
    total_iter = 1
    wpke=1
    ronde_time = time.perf_counter()
    while isRun:
        total_iter+=1
        doVisualize=False
        isHitWall = [0]*36
        for event in pygame.event.get():
            if(event.type== pygame.QUIT):
                forceQuit=True
                isRun=False
                print('force quit')
                break
        
        keys = pygame.key.get_pressed()
        if(keys[pygame.K_SPACE]):
            doVisualize=True

        # gerakin player
        the_input = make_data_masuk_dribble(player, ball, target_wp)
        # output probability action
        output = net.activate(the_input)
        process_output(output, player)
        
        # update world and graphics
        for _ in range(step):
            space.step(dt)
        
        if(doVisualize):
            clear_screen(window)
            draw(window, [ball, *team_A, *team_B, *goal_a, *goal_b], score_data, space, draw_options, False)
            pygame.draw.circle(window, (200, 20, 20), target_wp, wp_threshold_disance)
            pygame.display.update()
            # clock.tick(fps)


        # cek jarak target sama bola
        distance_ball_target = calculate_distance(ball.body.position, target_wp)
        if(distance_ball_target > wp_threshold_disance):
            if(counter_iter_to_wp > max_iter_wp):
                isRun=False
                # kurangi fitness
                genomes[0][1].fitness -= distance_ball_target
                # print('time out target')
            
            else:
                # masih belum time out, counting
                counter_iter_to_wp+=1

        else:
            # sampai, ganti target
            target_wp = get_random_wp(ball, ball_to_wp_init_distance, min_x, min_y, max_x, max_y)
            # tambah fitness
            genomes[0][1].fitness += wp_threshold_disance + (1/total_iter)*10000

            # reset hitungan
            counter_iter_to_wp = 0
            total_iter=0
            print(f'reached wp #{wpke}')
            wpke+=1


        existMovement=checkAllStandStill(player_cek, ball, True)
        if(not existMovement):
            # lsg break
            isRun=False
            # print('no move')
            genomes[0][1].fitness -= 500

    ### === END OF WHILE LOOP === ###


    # remove object from space? or just remove space
    for obj in space.bodies:
        space.remove(obj)
    for obj in space.shapes:
        space.remove(obj)
    for obj in space.constraints:
        space.remove(obj)
    # pygame.quit()
    return forceQuit

def set_fitness_val(genomes, val=0.0):
    for gid, genome in genomes:
        genome.fitness= val


import pickle
def eval_genomes(genomes, config):
    set_fitness_val(genomes)
    best_fitness = -100000000
    best_id = 0
    total_fitness = 0.0
    for id_genome in range(len(genomes)):
        train_genom = genomes[id_genome]
        game(window, WIDTH, HEIGHT, [train_genom], config, True, True)
        game(window, WIDTH, HEIGHT, [train_genom], config, True, False)


def run(config_file):
    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # # Add a stdout reporter to show progress in the terminal.

    # Run for up to 300 generations.
    import pickle
    # p = pickle.load(open('pop_vel.pkl', 'rb'))
    # p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-148')
    # p.config=config
     
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(30))
    try:
        winner = p.run(eval_genomes, 1000)
        with open('winner_vel_fit.pkl', 'wb') as mfile:
            pickle.dump(winner, mfile)
            mfile.close()
            print('FINISHED')
    except KeyboardInterrupt:
        print('voila')

    visualize.plot_stats(p.reporters.reporters[1], ylog=False, view=True)
    visualize.plot_species(p.reporters.reporters[1], view=True)



    with open('pop_vel_fit.pkl', 'wb') as mfile:
        pickle.dump(p, mfile)
        mfile.close()
        print('save population')



if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, './neatUtils/config-neat-vel-dribble')
    run(config_path)
    pygame.quit()