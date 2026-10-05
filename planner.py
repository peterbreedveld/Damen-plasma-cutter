import numpy as np
import time
import copy
from config.settings import END_WASTE, SAFE_SPEED, APPROACH_SPEED


class RobotPlanner:
    def __init__(self, robot, home):
        self.robot = robot
        self.home = home
        self.robot_path = []
        self.rest_pos = [0, 0, 0.1, 0, 0, 0]
        self.cutpath = None
        self.approach_pos = None
        


    def __str__(self):
        return f"RobotPlanner(cutpath={self.cutpath}, robot_path={self.robot_path}, rest_pos={self.rest_pos}, approach_pos={self.approach_pos})"


    def create_robot_path(self, cutpath):
        self.cutpath = cutpath
        self.approach_pos = copy.copy(self.cutpath.path[0])
        self.approach_pos.z += 0.05

        for node in self.cutpath.path:
            coordinaat = [node.x-END_WASTE, node.y, node.z, node.rx, node.ry, node.rz]
            robot_coordinaat = self.robot.add_home(self.home, coordinaat)
            robot_node = np.append(robot_coordinaat, [node.speed, node.acc, node.blend])
            self.robot_path.append(robot_node)
        return self.robot_path


    def set_home(self, home):
        self.home = home
        return self



    def execute_cut(self):
        robot_rest_pos = self.robot.add_home(self.home, self.rest_pos)
        robot_approach_pos = self.robot.add_home(self.home, self.approach_pos.coordinaat())

        self.robot.move_l(robot_rest_pos, SAFE_SPEED)
        self.robot.move_l(robot_approach_pos, SAFE_SPEED)
        time.sleep(1)
        self.robot.move_l_path(self.robot_path)
        time.sleep(1)
        self.robot.move_l(robot_rest_pos, SAFE_SPEED)
        
        return None