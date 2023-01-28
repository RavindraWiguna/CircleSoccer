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

def cap_radian(rad):
    twopi = np.pi*2
    while(rad < 0):
        rad += twopi
    
    while(rad > np.pi*2):
        rad -= twopi
    
    return rad

def calculate_diff_angle(rad1, rad2):
    rad1 = cap_radian(rad1)
    rad2 = cap_radian(rad2)
    basic = abs(rad1-rad2)
    counter_part = np.pi*2 - basic
    return min(counter_part, basic)


def to_degree(rad):
    return rad*180/np.pi

if __name__ == '__main__':
    print(cap_radian(1))
    print(cap_radian(0))
    print(cap_radian(-1))
    print(cap_radian(np.pi))
    print(cap_radian(np.pi/2))
    print(cap_radian(np.pi*2))
    print(cap_radian(np.pi*2 + 1))
    print(cap_radian(np.pi*2 - 1))
    print(cap_radian(-np.pi))
    print(cap_radian(-np.pi/2))
    print(cap_radian(-2*np.pi))
    print(cap_radian(np.pi/-2))