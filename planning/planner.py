import numpy as np
import time
import copy
from geometry.profiles import Profile
from config.settings import END_WASTE, SAFE_SPEED, APPROACH_SPEED
from geometry.path import Node


class RobotPlanner:

    def __init__(self, robot, home, profile):
        self.robot = robot
        self.home = copy.copy(home)
        self.rest_pos = [0, -0.05, -0.03, 0, 0, 0]
        self.profile = profile
        self.profile_type = profile.profile_type

        self.robot_cutpaths = []
        self.approach_positions = []
        self.retreat_positions = []
        

    def __str__(self):
        return f"RobotPlanner(cutpath={self.cutpath}, robot_path={self.robot_path}, rest_pos={self.rest_pos}, approach_pos={self.approach_pos})"


    def add_points_angle_cut(self):
        a = [[0, 0.1, -0.03, 0, 0, 0]]

        r = [[0, -0.05, 0.05, -0.5*np.pi, 0, 0]]

        for node in a:
            self.approach_positions.append(self.robot.add_home(self.home, node))
        for node in r:
            self.retreat_positions.append(self.robot.add_home(self.home, node))


    def add_points_HP_cut(self):
        a = [[-0.2, -0.1, 0.01, 0, -0.5*np.pi, 0],
             [0, -0.05, 0.05, 0, np.pi, 0],
             [0, 0.05, 0.05, 0, np.pi, 0]]
        
        r = [[0, -0.02, 0.05, 0, np.pi, 0],
             [-0.2, -0.1, 0.05, 0, -0.5*np.pi, 0],
             [0, -0.05, -0.05, 0, 0, 0]]

        for node in a:
            self.approach_positions.append(self.robot.add_home(self.home, node))
        for node in r:
            self.retreat_positions.append(self.robot.add_home(self.home, node))


    def add_points_square_cut(self):
        a = []
        r = []
        for node in a:
            self.approach_positions.append(self.robot.add_home(self.home, node))
        for node in r:
            self.retreat_positions.append(self.robot.add_home(self.home, node))



    def create_robot_path(self, cutpath):
        robot_path = []

        for node in cutpath:
            coordinaat = [node.x-END_WASTE, node.y, node.z, node.rx, node.ry, node.rz]
            robot_coordinaat = self.robot.add_home(self.home, coordinaat)
            robot_node = np.append(robot_coordinaat, [node.speed, node.acc, node.blend])
            robot_path.append(robot_node)
        return robot_path


    def create_robot_paths(self):
        
        for cutpath in self.profile.cuts:
            self.robot_cutpaths.append(self.create_robot_path(cutpath))

        if self.profile_type == "HP":
            self.add_points_HP_cut()
        elif self.profile_type == "Angle":
            self.add_points_angle_cut()
        elif self.profile_type == "Rect":
            self.add_points_square_cut()




    def execute_cut(self, index=0):
        robot_rest_pos = self.robot.add_home(self.home, self.rest_pos)
        executable_cutpath = self.robot_cutpaths[index]

        self.robot.move_l(robot_rest_pos, SAFE_SPEED)
        time.sleep(1)

        for node in self.approach_positions:
            self.robot.move_l(node, SAFE_SPEED)
            time.sleep(1)

        self.robot.move_l_path(executable_cutpath)
        time.sleep(1)

        for node in self.retreat_positions:
            self.robot.move_l(node, SAFE_SPEED)
            time.sleep(1)

        self.robot.move_l(robot_rest_pos, SAFE_SPEED)
        