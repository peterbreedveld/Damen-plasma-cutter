import numpy as np
from config.settings import SMOOTHNESS, START_OFFSET

class Path2D:
    def __init__(self, points: list, angle=0):
        self.points = points
        self.angle = angle

    def __iter__(self):
        return iter(self.points)

    def __len__(self):
        return len(self.points)

    def __str__(self):
        return str(self.points)


    def hp_add_reference_points(self, width):
        '''Voegt punten toe bij begin bulb en hoogtepunt bulb als die er nog niet zijn'''
        bulb_width = 0.18*width
        bulb_peak_width = 0.08*width
        punten = [bulb_width+0.04, bulb_width, bulb_peak_width]
    
        for y in punten:
            if any(abs(coord[1] - y) <= 2*SMOOTHNESS for coord in self.points):
                continue
            for i in range(len(self.points) - 1):
                y1 = self.points[i][1]
                y2 = self.points[i + 1][1]

                if y < y1 and y > y2:
                    x1 = self.points[i][0]
                    x2 = self.points[i + 1][0]

                    x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)

                    self.points.insert(i + 1, [x, y])
                    break
                    
        return self

    def reverse(self):
        self.points.reverse()
        return self



def type0(width):
    pad = []
    pad.append([0, width+START_OFFSET])
    pad.append([0, -START_OFFSET])
    return Path2D(pad)


def type1(width):
    Y = 10 # In degrees (Automatisch bepalen!!)
    pad = []
    pad.append([np.tan(Y*np.pi/180)*START_OFFSET, width+START_OFFSET])
    pad.append([-np.tan(Y*np.pi/180)*(START_OFFSET+width), -START_OFFSET])
    return Path2D(pad, angle=Y)


def type6(width, Y=0):
    #Y = 0 # In degrees (Automatisch bepalen!!)
    pad = []
    pad.append([-0.006-START_OFFSET, width+START_OFFSET])
    pad.append([0, width-0.006])
    pad.append([-np.tan(Y*np.pi/180)*(width-0.006+START_OFFSET), -START_OFFSET])
    return Path2D(pad, angle=Y)


def type5(width):
    pad = []
    pad.append([0, width+START_OFFSET])
    pad.append([0, width-0.015])
    pad.append([np.tan(np.pi/3)*(width+START_OFFSET-0.015), -START_OFFSET])
    return Path2D(pad)


def type3(Y, width):
    pad = []
    pad.append([-np.tan(Y*np.pi/180)*START_OFFSET, width+START_OFFSET])
    pad.append([-np.tan(Y*np.pi/180)*(width+START_OFFSET), -START_OFFSET])
    return Path2D(pad)


def type11(X, Y, width):
    A = 20 #Automatisch bepalen!!
    pad = []
    pad.append([-START_OFFSET-0.006, width+START_OFFSET])
    pad.append([0, width-0.006])
    k = np.tan(A*np.pi/180)*(width-0.006-Y)
    pad.append([0-k, Y])
    pad.append([-X-k, Y])
    pad.append([-X-k, -START_OFFSET])
    return Path2D(pad)