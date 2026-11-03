import numpy as np
from numpy import sqrt, pi
import time
import copy
from geometry.profiles import Profile
from config.settings import END_WASTE, SAFE_SPEED, APPROACH_SPEED, CUTTING_DISTANCE_FROM_CONVEYOR
from geometry.path import Node


class RobotPlanner:

    def __init__(self, robot, home, profile):
        self.robot = robot
        self.home = copy.copy(home)
        self.rest_pos = [CUTTING_DISTANCE_FROM_CONVEYOR, -0.1, -0.03, 0, 0, 0]
        self.profile = profile
        self.profile_type = profile.profile_type

        self.robot_cutpath = None
        self.approach_positions = []
        self.retreat_positions = []
        

    def __str__(self):
        return f"RobotPlanner(cutpath={self.cutpath}, robot_path={self.robot_cutpath})"


    def _add_points_angle_cut(self, offset=0):
        a = [[offset, 0.1, -0.03, 0, 0, 0]]

        r = [[offset, -0.05, 0.05, -0.5*np.pi, 0, 0]]

        for node in a:
            self.approach_positions.append(self.robot.add_home(self.home, node))
        for node in r:
            self.retreat_positions.append(self.robot.add_home(self.home, node))


    def _add_points_HP_cut(self, offset=0):
        a = [[offset-0.05, -0.1, 0.01, 0, -0.5*np.pi, 0],
             [offset, -0.05, 0.05, 0, np.pi, 0],
             [offset, 0.05, 0.03, 0, np.pi, 0]]
        
        r = [[offset, -0.02, 0.05, 0, np.pi, 0],
             [offset-0.05, -0.1, 0.05, 0, -0.5*np.pi, 0],
             [offset, -0.05, -0.05, 0, 0, 0]]

        for node in a:
            self.approach_positions.append(self.robot.add_home(self.home, node))
        for node in r:
            self.retreat_positions.append(self.robot.add_home(self.home, node))


    def _add_points_square_cut(self, offset=0):
        a = [[offset, 0.05, -0.03, 0, 0, 0]]
        r = [
            [offset, 0.1, 0.1, 0, np.pi, 0],
            [offset+0.05, -0.05, 0.1, 0, 0.5*np.pi, 0],
            [offset,-0.05, 0.05, -0.5*np.pi, 0, 0]]
        for node in a:
            self.approach_positions.append(self.robot.add_home(self.home, node))
        for node in r:
            self.retreat_positions.append(self.robot.add_home(self.home, node))



    def create_robot_path(self, cutpath, offset=0):
        self.robot_cutpath = []

        for node in cutpath:
            coordinaat = [node.x + offset - cutpath.min_x_value, node.y, node.z, node.rx, node.ry, node.rz]
            robot_coordinaat = self.robot.add_home(self.home, coordinaat)
            robot_node = np.append(robot_coordinaat, [node.speed, node.acc, node.blend])
            self.robot_cutpath.append(robot_node)


        if self.profile_type == "HP":
            self._add_points_HP_cut(offset=offset)
        elif self.profile_type == "Angle":
            self._add_points_angle_cut(offset=offset)
        elif self.profile_type == "Rect":
            self._add_points_square_cut(offset=offset)


    def approach_cut(self):
        robot_rest_pos = self.robot.add_home(self.home, self.rest_pos)
        
        self.robot.move_l(robot_rest_pos, SAFE_SPEED)
        time.sleep(1)

        for node in self.approach_positions:
            self.robot.move_l(node, SAFE_SPEED)
            time.sleep(0.1)

        self.robot.move_l(self.robot.cutpath[0][:6], SAFE_SPEED)

    def execute_cut(self):
        self.robot.move_l_path(self.robot_cutpath)


    def retreat_cut(self):
        robot_rest_pos = self.robot.add_home(self.home, self.rest_pos)
        
        for node in self.retreat_positions:
            self.robot.move_l(node, SAFE_SPEED)
            time.sleep(0.1)
        
        self.robot.move_l(robot_rest_pos, SAFE_SPEED)

    def move_to_rest_pos(self):
        robot_rest_pos = self.robot.add_home(self.home, self.rest_pos)
        self.robot.move_l(robot_rest_pos, SAFE_SPEED)
        