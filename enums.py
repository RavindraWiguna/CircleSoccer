from enum import Enum

class CollisionType(Enum):
    # Made this way for easier logic
    BALL = 128
    GOAL_A = 1
    GOAL_B = 2
    A_P1=3
    A_P2=4
    A_P3=5
    B_P1=8
    B_P2=9
    B_P3=10

class GamePhase(Enum):
    Normal=0
    JUST_GOAL=1
    KICKOFF=2
