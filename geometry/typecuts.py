from turtle import width

import numpy as np
from config.settings import START_OFFSET, NOZZLE_DISTANCE, CORNER_SPEED
from geometry.path import Node




def hp_type6(width, thickness, height=None, Y=0, side='right', H=0.006):
    bulb_height = 0.21*width
    bulb_width = 0.18*width
    bulb_peak_width = 0.08*width
    
    a = np.tan(Y*np.pi/180)
    
    if side == 'right':
        multiplier = -1
    elif side == 'left':
        multiplier = 1

    x0_index = 1
    c1 = Node(multiplier*(H+START_OFFSET), width+START_OFFSET, thickness)
    c2 = Node(0, width-H, thickness)
    c3 = Node(multiplier*a*(width-H-bulb_width), bulb_width, thickness)
    c4 = Node(multiplier*a*(width-H-bulb_peak_width), bulb_peak_width, bulb_height)
    c5 = Node(multiplier*a*(width-H+START_OFFSET), -START_OFFSET, bulb_height)

    pad = [c1, c2, c3, c4, c5]

    return pad

def hp_type9(width, thickness, height=None,Y=0, side='right', H=0.006):
    Y_rad = Y*np.pi/180
    bulb_height = 0.21*width
    bulb_width = 0.18*width
    bulb_peak_width = 0.08*width
    bulb_diagonal_length = np.sqrt((bulb_width-bulb_peak_width)**2+(bulb_height-thickness)**2)
    bulb_angle = Y_rad-np.tan((bulb_height-thickness)/(bulb_width-bulb_peak_width))


    c1 = Node(-H-START_OFFSET, width+START_OFFSET, thickness)
    c2 = Node(0, width-H, thickness)
    c3 = Node((width-bulb_height)*np.sin(Y_rad)-np.tan(Y_rad)*H, (width-bulb_height)*np.sin(Y_rad), thickness)
    c4 = Node(c3.x+np.sin(bulb_angle)*bulb_diagonal_length, c3.y+np.cos(bulb_angle)*bulb_diagonal_length, thickness)
    c5 = Node(c4.x+np.tan(Y_rad)*(c4.y+START_OFFSET), -START_OFFSET, bulb_height)

    pad = [c1, c2, c3, c4, c5]

    return pad

def angle_type11(width, height, thickness, X, Y, Angle, H=0.006, side='right'):
    # Ik ga er hier vanuit dat Y == thickness
    if side == 'right':
        multiplier = -1
    elif side == 'left':
        multiplier = 1

    k = np.tan(Angle*np.pi/180)*(width-0.006-Y)

    c1 = Node(multiplier*(START_OFFSET+H), width+START_OFFSET, -NOZZLE_DISTANCE)
    c2 = Node(0, width-H, -NOZZLE_DISTANCE)
    c3 = Node(multiplier*k, Y, -NOZZLE_DISTANCE)
    c4 = Node(multiplier*(k+X), Y, -NOZZLE_DISTANCE)
    c5 = Node(multiplier*(k+X), -NOZZLE_DISTANCE, -NOZZLE_DISTANCE, speed=CORNER_SPEED)
    c6 = Node(multiplier*(k+X), -NOZZLE_DISTANCE, thickness, speed= CORNER_SPEED)
    c7 = Node(multiplier*(k+X), -NOZZLE_DISTANCE, height+ START_OFFSET)

    pad = [c1, c2, c3, c4, c5, c6, c7]

    return pad

def angle_type83(width, height, thickness, side = 'right'):
    if side == 'right':
        multiplier = -1
    elif side == 'left':
        multiplier = 1

    c6 = Node(0,0, height+START_OFFSET)
    c5 = Node(0,0,0)
    c4 = Node(0,thickness, 0)
    c3 = Node(multiplier*0.025, thickness, 0)
    c2 = Node(multiplier*0.025, thickness+0.01, 0)
    c1 = Node(multiplier*np.tan(np.pi/3)*(width-thickness-0.01+START_OFFSET), width+ START_OFFSET, 0)

    pad = [c1, c2, c3, c4, c5, c6]

    return pad

def rect_v_cut(width, height, thickness=None, lengthwise=True, side="right"):
    if side == 'right':
        multiplier = -1
    elif side == 'left':
        multiplier = 1

    if lengthwise:
        c1 = Node(0, width+START_OFFSET, 0)
        c2 = Node(0,0,0)
        c3 = Node(multiplier*0.5*height, 0, 0.5*height)
        c4 = Node(0,0,height)
        c5 = Node(0, width, height)
        c6 = Node(multiplier*0.5*height, width, 0.5*height)
        c7 = Node(START_OFFSET, width, -START_OFFSET)
    else:
        c1 = Node(START_OFFSET, width+START_OFFSET, 0)
        c2 = Node(multiplier*0.5*width, -0.5*width, 0)
        c3 = Node(0,0,0)
        c4 = Node(0, 0, height)
        c5 = Node(multiplier*0.5*width, 0.5*width, height)
        c6 = Node(0, width, height)
        c7 = Node(0, width, -START_OFFSET)

    pad = [c1, c2, c3, c4, c5, c6, c7]

    return pad

def rect_type85(width, height, A, thickness=None):
    a = np.tan(A*np.pi/180)

    c1 = Node((width+START_OFFSET)/a, width+START_OFFSET, 0)
    c2 = Node(0,0,0)
    c3 = Node(0,0,height)
    c4 = Node(width/a, width, height)
    c5 = Node(width/a, width, -START_OFFSET)

    pad = [c1, c2, c3, c4, c5]
    return pad


