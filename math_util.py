import numpy as np
def calculate_distance(src, dst):
    dx = src[0]-dst[0]
    dy = src[1]-dst[1]
    return np.sqrt(dx*dx + dy*dy)

def calculate_angle(src, dst):
    return np.arctan2(dst[1]-src[1], dst[0]-src[0])

def rotate_point(list_of_point, angle):
    # Rotate the rectangle's vertices
    rotated_vertices = [(x*np.cos(angle)-y*np.sin(angle),x*np.sin(angle)+y*np.cos(angle)) for x,y in list_of_point]
    return rotated_vertices
