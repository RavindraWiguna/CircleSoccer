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

### === neat reward setup ###
second_last_toucher=0
last_ball_toucher_id=0
fitness_recorder = {'A':0, 'B':0} # team fitness and individu fitness too
ronde_time = time.perf_counter()
solo_touch_ball_counter=0
iter_to_touch = 1
multiplier_fitness_iter_touch = 500
max_touch = 50
max_drible = 3
just_sentuh=False
# list of 24 bool per list containing 4 boolean for 4 wall for 6 player tanda ngetouch
# males ngehandle duplikat, takut ngappend modif list gonna ada bug (barengan?)
isHitWall = [0]*36 # (tambah 6*2 for gol kiri kanan)

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

def goal_a_handler(arbiter, space, data):
    global score_data, game_phase, last_ball_toucher_id, second_last_toucher
    if(game_phase==GamePhase.Normal):
        score_data['B']+=1
        game_phase=GamePhase.JUST_GOAL

        if(isTeamB(last_ball_toucher_id)):
            # eyo dia ngegolin
            fitness_recorder[last_ball_toucher_id]+=1
            # print(last_ball_toucher_id, 'score the goal for tim B dia')

    return True

def goal_b_handler(arbiter, space, data):
    global score_data, game_phase, last_ball_toucher_id, second_last_toucher
    if(game_phase==GamePhase.Normal):
        score_data['A']+=1
        game_phase=GamePhase.JUST_GOAL

        if(isTeamA(last_ball_toucher_id)):
            fitness_recorder[last_ball_toucher_id]+=1

    return True

def ball_touch_handler(collision_type_toucher, arbiter, space, data):
    global fitness_recorder, last_ball_toucher_id, second_last_toucher, ronde_time, solo_touch_ball_counter, iter_to_touch, just_sentuh
    
    if(not fitness_recorder.__contains__(collision_type_toucher)):
        fitness_recorder[collision_type_toucher]=0
    
    # print(collision_type_toucher, 'touch the ball')
    # fitness_recorder[collision_type_toucher]
    just_sentuh=True #ONLY WORK IF SOLO, karna 1 yg di observe
    solo_touch_ball_counter+=1
    solo_touch_ball_counter = min(max_touch, solo_touch_ball_counter)
    if(solo_touch_ball_counter < max_touch):
        ronde_time = time.perf_counter()

    # check if someone lose the ball
    if(last_ball_toucher_id==0):
        # skip, gak ada lose ball
        pass

    # ok semua ke cek, now return
    if(last_ball_toucher_id==collision_type_toucher):
        # ga ada beda, dari pada second sama last sama
        return True
    
    # ok beda orang, ganti
    second_last_toucher=last_ball_toucher_id
    last_ball_toucher_id=collision_type_toucher
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

def make_data_masuk_solo(player, opo_goal, ball, width, needFlip):
    vx, vy = player.body.velocity
    px, py = player.body.position
    Bvx, Bvy = ball.body.velocity
    Bpx, Bpy = ball.body.position
    Gpx, Gpy = opo_goal.body.position


    if(needFlip):
        # flip velocity x
        vx *= -1
        Bvx *= -1

        # flip pos x
        px = width-px
        Bpx = width-Bpx
        Gpx = width - Gpx

    # self posv
    self_pos_vel            = [px, py, vx, vy]
    
    # ball posv dis
    ball_data               = [Bpx, Bpy, Bvx, Bvy]
    ball_to_player_dis           = [Bpx-px, Bpy-py]

    # ball to goal
    ball_to_gawang = [Gpx-Bpx, Gpy-Bpy] 
    
    bias=0.5
    the_input = [
        *self_pos_vel, *ball_data, *ball_to_player_dis, *ball_to_gawang, bias
    ]
    return the_input

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
def process_output(output, player, needFlip):
    addVx = output[0] - output[1]
    addVy = output[2] - output[3]
    addVx*=10
    addVy*=10 # biar gampangan cpet

    if(needFlip):
        addVx *= -1

    player.change_velocity(addVx, addVy)

def solve_players(players):
    for player in players:
        player.solve()


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
    # print(ball.shape.collision_type, goal_a[0].shape.collision_type)
    goal_a_sensor = space.add_collision_handler(ball.shape.collision_type, goal_a[0].shape.collision_type)
    goal_a_sensor.begin=goal_a_handler


    goal_b = [
        # vertical sensor
        RectObject(space, (width-wall_width-width_goal/2+offsetb, height/2), (width_goal, height_goal), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100)),
        
        # tiang bawah
        RectObject(space, grbc, (width_tiang, height_tiang), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100)),

        # tiang atas
        RectObject(space, grtc, (width_tiang, height_tiang), 1, 0.4, 500, isDynamic=False, color=(225, 225, 225, 100))
    ]

    goal_b[0].shape.collision_type=CollisionType.GOAL_B.value
    # print(ball.shape.collision_type, goal_b[0].shape.collision_type)
    goal_b_sensor = space.add_collision_handler(ball.shape.collision_type, goal_b[0].shape.collision_type)
    goal_b_sensor.begin=goal_b_handler

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
    start_time_after_goal=None
    wait_after_goal=0.0
    max_ronde_time =4.0 # reset

    # reset global var
    score_data = {'A':0,'B':0}
    game_phase = GamePhase.Normal
    second_last_toucher=0
    last_ball_toucher_id=0
    fitness_recorder = {'A':0, 'B':0} # team fitness and individu fitness too
    solo_touch_ball_counter=0
    iter_to_touch=1

    # get player, self goal, opo goal, team, etc
    net, genome = team_net[0]
    player, self_team, opo_team, self_goal, opo_goal = get_player_team_goal(team_A, team_B, goal_a, goal_b, asA)
    
    player_index = 0 if asA else 3
    player_cek = [[player_index, player]]

    # termination helper
    total_ngeliwat_gawang=0
    max_ngeliwat_gawang=40

    forceQuit=False
    total_iter = 1
    bola_stay_time = time.perf_counter()
    ronde_time = time.perf_counter()
    while isRun:
        total_iter+=1
        iter_to_touch+=1
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
        the_input = make_data_masuk_solo(player, opo_goal[0], ball, width, not asA)
        # output probability action
        output = net.activate(the_input)
        process_output(output, player, not asA)
        
        # update world and graphics
        for _ in range(step):
            space.step(dt)
        
        if(doVisualize):
            clear_screen(window)
            draw(window, [ball, *team_A, *team_B, *goal_a, *goal_b], score_data, space, draw_options, False)
            pygame.display.update()
            # clock.tick(fps)

        # FITNESS INSIDE LOOP (DANGER VIN, BUT I BELIEVE IN MATH), fitnes kalo nendang ke arah bener dapt bons
        if(just_sentuh):
            just_sentuh=False
            isRun=False # belajar nyentuh
            
            # angle_vec = get_ball_vec_angle(ball)
            # angle_goal = get_ball_to_goal_angle(ball, opo_goal[0])
            # dtetha = calculate_diff_angle(angle_goal, angle_vec, False)
            # double_dtetha = dtetha*2
            # if(double_dtetha < np.pi):
            #     # fancy way detect < pi/2 is 2* < pi
            #     # bonus bener nendang:
            #     bonus_bener_nendang = 1 - double_dtetha/np.pi
            #     fitnesfied = bonus_bener_nendang*10*(solo_touch_ball_counter < max_touch) # di cap
            #     genomes[0][1].fitness += fitnesfied


        # cek time out based by ball
        bola_is_gerak = check_velocity(ball.body.velocity, 20, True)
        # CATCH BOLA diem lama
        if(bola_is_gerak):
            bola_stay_time = time.perf_counter()
        else:
            # ok diem, cek berapa lama diem, kalu lama, end
            if(time.perf_counter() - bola_stay_time > 0.6):
                max_ronde_time = 0.0
        
        # cek termination by player ngejauh by angle
        player_isGettingFurther = player_is_gerak_menjauh(player, ball, 2.0, np.pi*0.75, 200)
        # alasan gak isRUn=player is bla bla, takutnya isRun udah di set false entah di kode atas right now or in the future
        if(player_isGettingFurther): 
            genomes[0][1].fitness -= 11000
            # print('menjauh')
            isRun=False
        
        # cek termination by bola ngeliwat gawang
        ball_isNgeliwat = check_ball_ngeliwat_gawang(ball, width, width_tiang)
        if(ball_isNgeliwat):
            total_ngeliwat_gawang+=1
            if(total_ngeliwat_gawang >= max_ngeliwat_gawang):
                isRun=False
                print('cuk anda lewat gawang > dari', max_ngeliwat_gawang, 'iterasi')
        else:
            total_ngeliwat_gawang=0

        # check termination
        if(game_phase==GamePhase.JUST_GOAL):

            if(start_time_after_goal is None):
                start_time_after_goal=time.perf_counter()
            
            # jika melebihi 3 detik setelah goal (yes pakek if because if training.. uhh..., mengding gpp stpi skip 1.0)
            if(time.perf_counter()-start_time_after_goal >= wait_after_goal):
                # end ronde
                isRun=False
                # print('get to 1 goal stop')
                break
        
        # same, check termination
        existMovement=checkAllStandStill(player_cek, ball, True)
        if(not existMovement):
            # lsg break
            # endgame_fitness() no move ga dikasi reward
            isRun=False
            # punish!!!!!!!!!!
            fitness_recorder['A']-=11000
            fitness_recorder['B']-=11000
            # print('no move, faster detect time out')
            # ga usah di punish
        else:
            game_phase=GamePhase.Normal

        # cek apakah out o bound
        objs = [ball, player]
        isOutOfBound = out_of_bound_check(objs, width, height)
        if(isOutOfBound):
            isRun=False
            # punish
            fitness_recorder['A'] -=11000
            fitness_recorder['B'] -=11000
            print('out of bound')

        # jika time out dan bola udah gak gerak
        if (time.perf_counter()-ronde_time) > max_ronde_time and not bola_is_gerak:
            isRun=False
            # punish
            fitness_recorder['A'] -= 11000
            fitness_recorder['B'] -= 11000
            print('time out! PUNISH TO THE HELL kalo kalah')
            break
    ### === END OF WHILE LOOP === ###

    # hitung jarak ke gol
    distance_to_goal = calculate_distance(ball.body.position, opo_goal[0].body.position)
    norm_distance = distance_to_goal/max_distance_possible * 100
    # ceritanya hitung MSE, tapi negatif, makin gede distance makin kecil
    sqe = (norm_distance*norm_distance)
    if(solo_touch_ball_counter == 0):
        sqe = 10000
    elif(total_ngeliwat_gawang >= max_ngeliwat_gawang):
        # hoo dia berhenti karna bola lewat gawang, hm, punish mse jadi 2500 aja anggap gak ngapa ngapai
        sqe=2500

    # gak ke pake tapi
    genomes[0][1].nendang += solo_touch_ball_counter

    # bonus time ngegol + fix sqe
    if(game_phase == GamePhase.JUST_GOAL):
        if(asA and score_data['A'] > score_data['B']):
            fitness_time_goal = (400000/total_iter)
            genomes[0][1].ngegol += 1
            sqe = 0 
            print('a ngegol must be tru->', asA)

        elif(not asA and score_data['B'] > score_data['A']):
            fitness_time_goal = (400000/total_iter)
            genomes[0][1].ngegol += 1
            sqe=0
            print('B ngegol must be tru->', not asA)

        else:
            fitness_time_goal=0.0
            genomes[0][1].own_goal +=1
            print('bunuh diri wtf')

        genomes[0][1].fitness += fitness_time_goal
    
    # tambah sqe yg uda di proses
    genomes[0][1].sqe_dis2_goal.append(sqe)

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

def create_team(genomes, id):
    if(id + 3 <= len(genomes)):
        return genomes[id:id+3], id+3
    else:
        print('nanggung..., skip aja males mikir')
        return None, len(genomes)

def make_teams(genomes):
    teams = []
    id = 0
    while id < len(genomes):
        team, new_id = create_team(genomes, id)
        if(team):
            teams.append(team)
        id=new_id
    return teams

import pickle
def eval_genomes(genomes, config):
    set_fitness_val(genomes)
    best_fitness = -100000000
    best_id = 0
    total_fitness = 0.0
    for id_genome in range(len(genomes)):
        genomes[id_genome][1].ngegol = 0
        genomes[id_genome][1].nendang = 0
        genomes[id_genome][1].own_goal = 0
        genomes[id_genome][1].sqe_dis2_goal = []
        
        # prev_nendang = 0
        # prev_og = 0
        prev_goal = 0
        counter = 0
        max_try = 1000
        hasChance=True
        max_patience = 0
        patience_count=0

        while(genomes[id_genome][1].ngegol < 201 and counter < max_try and hasChance):
            counter+=1
            # do 1 game
            fq = game(window, WIDTH, HEIGHT, [genomes[id_genome]], config, True, True)
            fq = game(window, WIDTH, HEIGHT, [genomes[id_genome]], config, True, False)
            if(fq):break
            
            if(genomes[id_genome][1].ngegol - prev_goal > 1):
                patience_count = 0
            else:
                patience_count+=1
            
            if(patience_count > max_patience):
                hasChance=False
                # print('reach patience')
            else:
                hasChance=True
                # print('lanjut')

            # prev_nendang = genomes[id_genome][1].nendang
            # prev_og = genomes[id_genome][1].own_goal
            prev_goal = genomes[id_genome][1].ngegol
        
        
        # calculate additional fitness
        gol_score = genomes[id_genome][1].ngegol*5000
        own_goal_score = genomes[id_genome][1].own_goal*-11000
        neg_mse = np.mean(genomes[id_genome][1].sqe_dis2_goal)*-1
        
        genomes[id_genome][1].fitness += own_goal_score  + neg_mse + gol_score
        genomes[id_genome][1].neg_mse = neg_mse
        
        if(genomes[id_genome][1].ngegol > 0):
            print('genome ke:',id_genome, f'|id:{genomes[id_genome][0]}', 'ngegol')
            seenome = genomes[id_genome][1]
            print('|gol:', seenome.ngegol, '|og:', seenome.own_goal,'|kc', seenome.nendang)

            
            if(genomes[id_genome][1].ngegol > 75):
                with open(f'genome_pengegol_{id_genome}_{genomes[id_genome][1].ngegol}.pkl','wb') as mfile:
                    pickle.dump(genomes[id_genome], mfile)
                    mfile.close()
                    print('saved gol:', genomes[id_genome][1].ngegol)

        if(best_fitness < genomes[id_genome][1].fitness):
            best_id = id_genome
            best_fitness = genomes[id_genome][1].fitness

        total_fitness += genomes[id_genome][1].fitness

    # # fix nilai
    print('best:', best_fitness)
    print('stat:')
    bgenome = genomes[best_id][1]
    print('|gol:', bgenome.ngegol, '|og:', bgenome.own_goal,'\n|kc', bgenome.nendang, '|sqe:', bgenome.sqe_dis2_goal,'\n|neg_mse:', bgenome.neg_mse)      


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
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, './neatUtils/config-neat-vel-fit')
    run(config_path)
    pygame.quit()