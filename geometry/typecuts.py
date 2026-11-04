from numpy import pi, sin, cos, tan, sqrt
from config.settings import START_OFFSET, NOZZLE_DISTANCE, CORNER_SPEED, SAFE_SPEED
from geometry.path import Node



def hp_type6(width, thickness, height=None, Y=0, side='right', H=0.006):
    bulb_height = 0.21*width
    bulb_width = 0.18*width*0.9
    bulb_peak_width = 0.08*width*0.9
    
    a = tan(Y*pi/180)
    
    if side == 'right':
        multiplier = -1
    elif side == 'left':
        multiplier = 1

    c1 = Node(multiplier*(H+START_OFFSET), width+START_OFFSET, thickness+NOZZLE_DISTANCE)
    c2 = Node(0, width-H, thickness+NOZZLE_DISTANCE)
    c3 = Node(-multiplier*a*(width-H-bulb_width), bulb_width, thickness+NOZZLE_DISTANCE)
    c4 = Node(-multiplier*a*(width-H-bulb_peak_width), bulb_peak_width, bulb_height+NOZZLE_DISTANCE)
    c5 = Node(-multiplier*a*(width-H+START_OFFSET), -START_OFFSET, bulb_height+NOZZLE_DISTANCE)

    pad = [c1, c2, c3, c4, c5]


    less_offset = a*START_OFFSET if Y>0 else 0

    if side =='right':
        offset = max(c.x for c in pad) - less_offset
    elif side == 'left':
        offset = min(c.x for c in pad) - less_offset
            
    for c in pad:
        c.x -= offset

    return pad


def hp_type9(width, thickness, height=None, Y=0, side='right', H=0.006, plate_shift=None):
    if Y >= 45:
        raise ValueError("Y moet kleiner zijn dan 45 graden (anders klopt de 45-graden afschuining niet)")

    Y_rad = Y*pi/180
    bulb_peak_width = 0.007
    bulb_width = 0.62*(height-thickness) + bulb_peak_width
    bulb_diagonal_length = sqrt((bulb_width-bulb_peak_width)**2 + (height-thickness)**2)
    bulb_angle = 63*pi/180

    s = -1 if side == 'right' else 1

    # Extra verschuiving van het begin van de bulb-hoek (alleen bij Y > 0:
    # loodrechte profiel zit met achterkant tegen de bodemplaat)
    if plate_shift is None:
        plate_shift = H*tan(Y_rad) if Y > 0 else 0.0

    # Richting van de snijlijn (eenheidsvector) vanaf de rand (0, width)
    d = (-s*sin(Y_rad), -cos(Y_rad))

    # --- 2D hoekpunten ---
    c1 = (s*(H+START_OFFSET), width+START_OFFSET)

    h = H/(cos(Y_rad) - sin(Y_rad))          # == H*sin(45)/sin(45-Y)
    c2 = (h*d[0], width + h*d[1])

    L3 = (width - bulb_width) + plate_shift
    c3 = (L3*d[0], width + L3*d[1])

    corner = (c3[0] + s*bulb_diagonal_length*sin(bulb_angle - Y_rad),
              c3[1] - bulb_diagonal_length*cos(bulb_angle - Y_rad))

    # Na de bulb-hoek verder langs de richting van de snijlijn tot onder de rand
    end = (corner[0] - s*(corner[1] + START_OFFSET)*tan(Y_rad), -START_OFFSET)

    pts = [c1, c2, c3, corner, end]

    # --- z als functie van y ---
    def z_of(y):
        if y >= bulb_width:
            return thickness + NOZZLE_DISTANCE
        if y <= bulb_peak_width:
            return height + NOZZLE_DISTANCE
        frac = (bulb_width - y)/(bulb_width - bulb_peak_width)
        return thickness + NOZZLE_DISTANCE + frac*(height - thickness)

    # --- Segmenten splitsen op de y-waarden waar de hoogte verandert ---
    breaks = [bulb_width, bulb_peak_width]
    xy = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        ts = []
        for brk in breaks:
            if (a[1] - brk)*(b[1] - brk) < 0:
                ts.append((a[1] - brk)/(a[1] - b[1]))
        for t in sorted(ts):
            xy.append((a[0] + t*(b[0]-a[0]), a[1] + t*(b[1]-a[1])))
        xy.append(b)

    # --- Samenvallende punten verwijderen ---
    cleaned = [xy[0]]
    for p in xy[1:]:
        if (p[0]-cleaned[-1][0])**2 + (p[1]-cleaned[-1][1])**2 > 1e-4**2:
            cleaned.append(p)

    pad = [Node(x, y, z_of(y)) for x, y in cleaned]

    # --- x-offset zodat het profiel tegen x = 0 ligt ---

    if side == 'right':
        offset = max(c.x for c in pad)
    else:
        offset = min(c.x for c in pad)
    for c in pad:
        c.x -= offset

    return pad




def angle_type11(width, height, thickness, X, Y, Angle, H=0.006, side='right'):
    # Ik ga er hier vanuit dat Y == thickness
    Y = thickness
    if side == 'right':
        multiplier = -1
    elif side == 'left':
        multiplier = 1

    k = -tan(Angle*pi/180)*(width-0.006-Y)

    c1 = Node(multiplier*(START_OFFSET+H), width+START_OFFSET, -NOZZLE_DISTANCE, speed=SAFE_SPEED)
    c2 = Node(0, width-H, -NOZZLE_DISTANCE)
    c3 = Node(multiplier*k, Y, -NOZZLE_DISTANCE)
    c4 = Node(multiplier*(k+X), Y, -NOZZLE_DISTANCE)
    c5 = Node(multiplier*(k+X), -NOZZLE_DISTANCE, -NOZZLE_DISTANCE, speed=CORNER_SPEED)
    c6 = Node(multiplier*(k+X), -NOZZLE_DISTANCE, thickness, speed= CORNER_SPEED)
    c7 = Node(multiplier*(k+X), -NOZZLE_DISTANCE, height+ START_OFFSET)

    pad = [c1, c2, c3, c4, c5, c6, c7]


    if side =='right':
        offset = max(c.x for c in pad)
    elif side == 'left':
        offset = min(c.x for c in pad)

   

    for c in pad:
        c.x -= offset

    return pad


def angle_type83(width, height, thickness, side='right'):
    if side == 'right':
        multiplier = -1
    elif side == 'left':
        multiplier = 1

    c7 = Node(0,-NOZZLE_DISTANCE, height+START_OFFSET)
    c6 = Node(0, -NOZZLE_DISTANCE, thickness, speed=CORNER_SPEED)
    c5 = Node(0,-NOZZLE_DISTANCE,-NOZZLE_DISTANCE, speed=CORNER_SPEED, blend=0.003)
    c4 = Node(0,thickness, -NOZZLE_DISTANCE)
    c3 = Node(multiplier*0.025, thickness, -NOZZLE_DISTANCE)
    c2 = Node(multiplier*0.025, thickness+0.01, -NOZZLE_DISTANCE)
    c1 = Node(multiplier*tan(pi/3)*(width-thickness-0.01+START_OFFSET), width+ START_OFFSET, -NOZZLE_DISTANCE, speed=SAFE_SPEED)

    pad = [c1, c2, c3, c4, c5, c6, c7]

    return pad

def rect_v_cut(width, height, thickness=None, lengthwise=True, side="right"):

    if side == 'right':
        multiplier = -1
    elif side == 'left':
        multiplier = 1

    r2 = 0.5*sqrt(2)*pi # Root 2 over 2 times Pi

    
    if lengthwise:
        c1 = Node(-multiplier*NOZZLE_DISTANCE, width+START_OFFSET, -NOZZLE_DISTANCE, ry=multiplier*0.25*pi, speed=CORNER_SPEED)
        c2 = Node(-multiplier*NOZZLE_DISTANCE, -NOZZLE_DISTANCE, -NOZZLE_DISTANCE, ry=multiplier*0.25*pi)
        c3 = Node(-multiplier*NOZZLE_DISTANCE, -NOZZLE_DISTANCE, -NOZZLE_DISTANCE, rx=-0.5*pi, ry=0, speed=CORNER_SPEED)
        c4 = Node(multiplier*0.5*height, -NOZZLE_DISTANCE, 0.5*height, rx=-0.5*pi)
        c5 = Node(-multiplier*NOZZLE_DISTANCE, -NOZZLE_DISTANCE,height+NOZZLE_DISTANCE, rx=-0.5*pi)
        c6 = Node(-multiplier*NOZZLE_DISTANCE, -NOZZLE_DISTANCE,height+NOZZLE_DISTANCE, rx=0, ry=pi, speed=2*CORNER_SPEED)
        c7 = Node(-multiplier*NOZZLE_DISTANCE, -NOZZLE_DISTANCE,height+NOZZLE_DISTANCE, ry=(1-multiplier*0.25)*pi, speed=CORNER_SPEED)
        c8 = Node(-multiplier*NOZZLE_DISTANCE, width+NOZZLE_DISTANCE, height+NOZZLE_DISTANCE, ry=(1-multiplier*0.25)*pi)
        c9 = Node(-multiplier*NOZZLE_DISTANCE, width+NOZZLE_DISTANCE, height+NOZZLE_DISTANCE, ry=-r2, rz=r2, speed=CORNER_SPEED)
        c10 = Node(multiplier*0.5*height, width+NOZZLE_DISTANCE, 0.5*height, ry=-r2, rz=r2)
        c11 = Node(-multiplier*(START_OFFSET+NOZZLE_DISTANCE), width+NOZZLE_DISTANCE, -START_OFFSET, ry=-r2, rz=r2)

    else:
        c1 = Node(-multiplier*START_OFFSET, width+START_OFFSET, -NOZZLE_DISTANCE)
        c2 = Node(multiplier*0.5*width, 0.5*width, -NOZZLE_DISTANCE)
        c3 = Node(-multiplier*NOZZLE_DISTANCE, -NOZZLE_DISTANCE, -NOZZLE_DISTANCE)
        c4 = Node(-multiplier*NOZZLE_DISTANCE, -NOZZLE_DISTANCE, -NOZZLE_DISTANCE, rx=-1.482190, ry=multiplier*0.613943, rz=-multiplier*0.613943, speed=CORNER_SPEED)
        c5 = Node(-multiplier*NOZZLE_DISTANCE, -NOZZLE_DISTANCE, height+NOZZLE_DISTANCE, rx=-1.482190, ry=multiplier*0.613943, rz=-multiplier*0.613943)
        c6 = Node(-multiplier*NOZZLE_DISTANCE, -NOZZLE_DISTANCE, height+NOZZLE_DISTANCE, rx=-0.5*pi, speed=CORNER_SPEED)
        c7 = Node(-multiplier*NOZZLE_DISTANCE, -NOZZLE_DISTANCE, height+NOZZLE_DISTANCE, ry=pi, speed=3*CORNER_SPEED)
        c8 = Node(multiplier*0.5*width, 0.5*width, height+NOZZLE_DISTANCE, ry=pi)
        c9 = Node(-multiplier*NOZZLE_DISTANCE, width+NOZZLE_DISTANCE, height+NOZZLE_DISTANCE, ry=pi)

        if side =='left': #Misschien maar 1 van deze nodig met nieuwe end effector
            c10 = Node(-multiplier*NOZZLE_DISTANCE, width+NOZZLE_DISTANCE, height+NOZZLE_DISTANCE, rx=0.5*pi, ry=-multiplier*0.5*pi, rz=multiplier*r2, speed=CORNER_SPEED)
            c11 = Node(-multiplier*NOZZLE_DISTANCE, width+NOZZLE_DISTANCE, -START_OFFSET, rx=0.5*pi, ry=-multiplier*0.5*pi, rz=multiplier*r2)
        elif side == 'right':
            c10 = Node(-multiplier*NOZZLE_DISTANCE, width+NOZZLE_DISTANCE, height+NOZZLE_DISTANCE, rx=-1.136, ry=-1.7, rz=2, speed=CORNER_SPEED)
            c11 = Node(-multiplier*NOZZLE_DISTANCE, width+NOZZLE_DISTANCE, -START_OFFSET, rx=-1.136, ry=-1.7, rz=2)

    if side == 'left':
        c7.speed = 2*CORNER_SPEED
        pad = [c1, c2, c3, c4, c5, c7, c8, c9, c10, c11]
    elif side == 'right':
        pad = [c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11]
        

    for c in pad:
        c.x -= multiplier*START_OFFSET

    return pad



def rect_type85(width, height, A, thickness=None, lenthwise=True, side='right'):
    # TODO Deze unit programmeren
    a = tan(A*pi/180)

    # if lengthwise:

    c1 = Node((width+START_OFFSET)/a, width+START_OFFSET, 0)
    c2 = Node(0,0,0)
    c3 = Node(0,0,height)
    c4 = Node(width/a, width, height)
    c5 = Node(width/a, width, -START_OFFSET)

    pad = [c1, c2, c3, c4, c5]

    return pad


