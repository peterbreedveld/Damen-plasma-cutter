import queue
import threading
import traceback
import tkinter as tk
import time
from scipy.spatial.transform import Rotation as R

from HumanInterface import DamenPlasmaHMI
from geometry.profiles import Profile
from config.settings import *
from universalcontrol import URControl
from planning.planner import RobotPlanner
from geometry.typecuts import *
from esp_communication import ESP32Communicator

from geometry.path import CutPath

estop = threading.Event()
esp = ESP32Communicator(port=SERIAL_PORT, pulses_per_mm=ENCODER_STEPS_PER_MM, settle_tolerance=10)

esp.stuur_commando("Pneumatic_Sys_ON")
estop.wait(0.5)
esp.stuur_commando("CLAMP_3_ON")
estop.wait(1)
esp.find_profile_front(max_mm=2000)

while True:
    text = input('Typ om the beeindigen')
    esp.move_front_to(int(text))


# ROBOT_IP = "192.168.0.43"
# HOME = [-0.3401, 0.7702, 0.0946, 0, 0, 0]
# rest_pos = [-0.191, 0.771-0.1, 0.0961-0.05, 0, 0, 0]
# robot = URControl(ROBOT_IP)
# robot.connect()
# robot.set_tcp(MARKER_ENDEFFECTOR_OFFSET)

# #robot.move_l(rest_pos, speed=0.04)
# home = robot.get_tcp_pos()
# print(home)
      
'''
width = 0.02
height = 0.02
thickness = 0.005
side = 'left'


profile = Profile(profiel='Angle', width=0.08, thickness=0.005, length=1.2, height=0.05)
profile.add_cut(cuttype='type11', position=0, side='right', X=0.02, Y=0.005, Angle=20, H=0.006)
profile.add_cut(cuttype='type83', position=0.5, side='left')

# profile = Profile(profiel='Rect', width=0.02, thickness=0.002, length=1.2, height=0.02)
# profile.add_cut(cuttype='v_cut',  lengthwise=False, side="right")

# profile = Profile(profiel='HP', width=0.06, height=0.0124, thickness=0.0033, length=1.2)
# profile.add_cut(cuttype='type9', Y=-20, side='right')

# ROBOT PATH TESTING
ROBOT_IP = "192.168.0.43"
HOME = [-0.191, 0.771, 0.0961, 0, 0, 0]
robot = URControl(ROBOT_IP)
robot.connect()
robot.set_tcp(MARKER_ENDEFFECTOR_OFFSET)


cut = CutPath(profile[0], profile)
cut.make_6d()

planner = RobotPlanner(robot, HOME, profile)
planner.create_robot_path(cut, offset=0)

planner.execute_cut()

robot.stop_robot_control()
'''

'''
# TEST VAN ALLES INTEGRATIE (behalve HMI)
ROBOT_IP = "192.168.0.43"
HOME = [-0.091, 0.771, 0.0961, 0, 0, 0]
robot = URControl(ROBOT_IP)
robot.connect()
robot.set_tcp(PINK_ANGLEPRINT_OFFSET)

profile = Profile(profiel='Angle', width=0.08, thickness=0.005, length=1.2, height=0.05)
profile.add_cut(cuttype='type11', position=0.1, side='right', X=0.02, Y=0.005, Angle=20, H=0.006)
profile.add_cut(cuttype='type83', position=0.8, side='left')


estop = threading.Event()
esp = ESP32Communicator(port=SERIAL_PORT, pulses_per_mm=ENCODER_STEPS_PER_MM, settle_tolerance=10)

esp.stuur_commando("Pneumatic_Sys_ON")
estop.wait(0.1)
esp.stuur_commando("CLAMP_1_OFF")
estop.wait(0.1)
esp.stuur_commando("CLAMP_2_OFF")

estop.wait(2)
print('Conveyor beweegt naar nulpositie:')
nul_positie = esp.find_profile_front(max_mm=2000)
print('Nul positie is:',nul_positie)

input("Press a key to move to first cut position")

for i, cut in enumerate(profile):
    print(cut)
    print('Conveyor beweegt tot juiste snijpositie')
    print('dat is positie: ', 1000*(CUTTING_DISTANCE_FROM_CONVEYOR + cut.at_position + cut.cut_width + END_WASTE))
    overshoot = 0.001 * esp.move_front_to(1000*(CUTTING_DISTANCE_FROM_CONVEYOR + cut.at_position + cut.cut_width + END_WASTE))
    estop.wait(1)

    print('Clamps gaan dicht')
    esp.stuur_commando("CLAMP_1_ON")
    estop.wait(0.1)
    esp.stuur_commando("CLAMP_2_ON")
    estop.wait(1)

    print('Robotarm gaat nu snijden')
    input('confirm to continue')
    planner = RobotPlanner(robot, HOME, profile)
    planner.create_robot_path(cut, offset=overshoot)
    planner.execute_cut()
    estop.wait(1)

    print('Clamps gaan open')
    esp.stuur_commando("CLAMP_1_OFF")
    estop.wait(0.1)
    esp.stuur_commando("CLAMP_2_OFF")
    estop.wait(1)

esp.move_front_to(1000*profile.length)

robot.stop_robot_control()

'''