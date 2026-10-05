from geometry.typecuts import Path2D, type0, type1, type6, type5, type3, type11
#from geometry.profiles import plat_profiel, hp_profiel
from config.settings import *
from universalcontrol import URControl
from geometry.path import CutPath
from planning.planner import RobotPlanner


import numpy as np
import copy
import time

### TO-DO's
# Voeg Hoek profiel toe
# Voeg type9 toe\
# Maak meerdere cuts per bar mogelijk
# Maak gehele main loop met inpunts en outputs
# Cuts moeten inverteerbaar zijn


robot_ip = "192.168.0.43"  
home1 = [-0.357, 0.499, 0.223, 3.14, 0, 0]
home2 = [-0.402, 0.514, 0.102, 3.14, 0, 0] # Gebruik deze voor opstelling


robot = URControl(robot_ip)
robot.connect()

robot.set_tcp(BLUE_PIPE_OFFSET)

loca = robot.get_tcp_pos() # Eenmalig
print(loca)




zes = type6(width=0.08, Y=50)
zes.hp_add_reference_points(width=0.080)

pad6 = CutPath(zes)
pad6.create_hp_profile(0.08, 0.005)

planner = RobotPlanner(robot, home2) # Home is de hoek van de balk

planner.create_robot_path(pad6)

planner.execute_cut()


#robot.move_l(home2, speed=0.01)

robot.stop_robot_control()
