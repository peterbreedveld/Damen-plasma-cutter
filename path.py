import numpy as np

from config.settings import SPEED_PER_THICKNESS, ACC, SMOOTHNESS, CURVE, HP_BULB_ANGLE

class Node:
    def __init__(self, x, y, z=0, rx=0, ry=0, rz=0, speed=0, acc=0, blend=0):
        self.x = x
        self.y = y
        self.z = z
        self.rx = rx
        self.ry = ry
        self.rz = rz
        self.speed = speed
        self.acc = acc
        self.blend = blend

    def coordinaat(self):
        return [self.x, self.y, self.z, self.rx, self.ry, self.rz]

    def __iter__(self):
        return iter([self.x, self.y, self.z, self.rx, self.ry, self.rz])

    def __str__(self):
        return str([self.x, self.y, self.z, self.rx, self.ry, self.rz])

    def __repr__(self):
        return f"Node(x={self.x}, y={self.y}, z={self.z}, rx={self.rx}, ry={self.ry}, rz={self.rz})"




class CutPath:
    def __init__(self, Path2D):
        self.path2d = Path2D
        self.cut_speed = None
        self.path = None
        self.angle = Path2D.angle


    def __iter__(self):
        return iter(self.path)
    
    def __len__(self):
        return len(self.path)
    
    def __str__(self):
        return str(self.path)


    def reverse(self):
        self.path.reverse()
        return None


    def create_flat_profile(self, width, thickness):
        pad = []
        for node in self.path2d:
            point = Node(node[0], node[1], thickness)
            point.blend = SMOOTHNESS
            point.acc = ACC
            point.speed = SPEED_PER_THICKNESS[thickness]
            pad.append(point)

        pad[0].blend = 0 # start en eind punt met 0 blend
        pad[-1].blend = 0
        self.path = pad
        return pad


    def hp_y_to_z(self, y, width, thickness):
        bulb_height = 0.21*width
        bulb_width = 0.18*width
        bulb_peak_width = 0.08*width

        if y < bulb_peak_width:
            return bulb_height
        elif(y < bulb_width):
            return thickness + (bulb_height-thickness)*(bulb_width-y)/(bulb_width-bulb_peak_width)
        else:
            return thickness


    def hp_y_to_speed(self, y, width, thickness):
        bulb_peak_width = 0.08*width
        bulb_width = 0.18*width

        return SPEED_PER_THICKNESS[thickness]

        if y < bulb_peak_width:
            return SPEED_PER_THICKNESS[thickness]/3 # Deze moet veranderd worden
        elif y < bulb_width:
            return SPEED_PER_THICKNESS[thickness]/(3*(bulb_width-y)/(bulb_width-bulb_peak_width))
        else:
            return SPEED_PER_THICKNESS[thickness]


    def hp_y_to_rx_ry(self, y, width):
        bulb_peak_width = 0.08*width
        bulb_width = 0.18*width
        angle = self.path2d.angle

        if y > bulb_width + 0.04:
            total_angle = 0
        elif y > bulb_width:
            total_angle = HP_BULB_ANGLE*((bulb_width+0.04-y)/0.04)
        elif y > bulb_peak_width:
            total_angle = HP_BULB_ANGLE*(y-bulb_peak_width)/(bulb_width-bulb_peak_width)
        else:
            total_angle = 0

        rx = -total_angle*np.sin(angle*np.pi/180)
        ry = -total_angle*np.cos(angle*np.pi/180)

        return rx, ry



    def create_hp_profile(self, width, thickness):
        pad = []
        path2d = self.path2d.hp_add_reference_points(width)

        for node in path2d:
            point = Node(node[0], node[1])
            point.z = self.hp_y_to_z(point.y, width, thickness)
            point.rx, point.rz = self.hp_y_to_rx_ry(point.y, width)
            point.speed = self.hp_y_to_speed(point.y, width, thickness)
            point.acc = ACC
            point.blend = SMOOTHNESS
            pad.append(point)


        pad[0].blend = 0 # start en eind punt met 0 blend
        pad[-1].blend = 0
        self.path = pad

        return pad


    def angle_2d_to_3d(self, height, thickness):
        path2d = self.path2d
        path3d = []

        for coord in path2d:
            if coord[1] > thickness:
                path3d.append(coord + [thickness])
            else:
                path3d.append(coord + [height])

        for i in range(len(path3d) - 1):
            x1 = path3d[i][0]
            x2 = path3d[i + 1][0]
            y1 = path3d[i][1]
            y2 = path3d[i + 1][1]
            x = x1 + (thickness - y1) * (x2 - x1) / (y2 - y1)

            if abs(y1 -thickness) < 2*SMOOTHNESS:
                if y1 > thickness:
                    path3d.insert(i+1, [x, thickness, height])
                else:
                    path3d.insert(i, [x, thickness, thickness])
                break
            elif y1 > thickness+SMOOTHNESS and y2 < thickness-SMOOTHNESS:
                path3d.insert(i+1, [x, thickness, height])
                path3d.insert(i+1, [x, thickness, thickness])
                break

        return path3d




    def create_angle_profile(self, width, height, thickness):
        pad = []
        path2d = self.path2d.points

        #for node in path2d:



