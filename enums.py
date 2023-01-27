from enum import Enum

class CollisionType(Enum):
    # Made this way for easier logic (tak gedein takut ada yg sama sama object lain)
    BALL = 128
    GOAL_A = 10
    GOAL_B = 20
    A_P1=30
    A_P2=40
    A_P3=50
    B_P1=80
    B_P2=90
    B_P3=100
    WALL_TOP=111
    WALL_BOTTOM=222
    WALL_LEFT=333
    WALL_RIGHT=444

class GamePhase(Enum):
    Normal=0
    JUST_GOAL=1
    KICKOFF=2
