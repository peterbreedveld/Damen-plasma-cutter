import numpy as np

from config.settings import SPEED_PER_THICKNESS, ACC, SMOOTHNESS, CURVE

class Node:
    def __init__(self, x, y, z=0, rx=0, ry=0, rz=0, speed=None, acc=None, blend=None):
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

    def __init__(self, path_3d, profile):
        self.path3d = path_3d
        self.path6d = None
        self.at_position = None

        self.profile_type = profile.profile_type
        self.width = profile.width
        self.height = profile.height
        self.thickness = profile.thickness
        self.cut_speed = SPEED_PER_THICKNESS[self.thickness]
        


    def __iter__(self):
        return iter(self.path6d)
    
    def __len__(self):
        return len(self.path6d)
    
    def __str__(self):
        return str(self.path6d)


    def reverse(self):
        self.path.reverse()
        return None

    def make_6d(self):
        if self.profile_type == "HP":
            self.make_hp_6d()

        elif self.profile_type == "Angle":
            self.make_angle_6d()

        elif self.profile_type == "Rect":
            self.make_rectangle_6d()

        else:
            raise ValueError(f"Onbekend profieltype: {self.profile_type}")
        

    def make_hp_6d(self):
        self.path6d = []
        for node in self.path3d:
            if node.speed is not None:
                speed = node.speed
            else:
                speed = self.cut_speed
            
            self.path6d.append(Node(node.x, node.y, node.z, 0, np.pi, 0, speed, ACC, SMOOTHNESS))

    
    def make_angle_6d(self):
        self.path6d = []
        for node in self.path3d:
            if node.y >= self.thickness:
                rx = 0
            elif node.z < self.thickness:
                rx = -0.25*np.pi*(node.z- node.y + self.thickness)/self.thickness
            else:
                rx = -0.5*np.pi

            if node.speed is not None:
                speed = node.speed
            else:
                speed = self.cut_speed

            self.path6d.append(Node(node.x, node.y, node.z, rx, 0, 0, speed, ACC, SMOOTHNESS))



    def make_rectangle_6d(self):
        self.path6d = []

        for node in self.path3d:

            if node.speed is not None:
                speed = node.speed
            else:
                speed = self.cut_speed

            self.path6d.append(Node(node.x, node.y, node.z, 0, 0, 0, speed, ACC, SMOOTHNESS))




def get_direction(node1, node2):
    vector = np.array([
        node2.x - node1.x,
        node2.y - node1.y,
        node2.z - node1.z
    ])

    return vector / np.linalg.norm(vector)