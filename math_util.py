import numpy as np
def calculate_distance(src, dst):
    dx = src[0]-dst[0]
    dy = src[1]-dst[1]
    return np.sqrt(dx*dx + dy*dy)

def calculate_angle(src, dst):
    return np.arctan2(dst[1]-src[1], dst[0]-src[0])