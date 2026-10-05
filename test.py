from config.settings import *
from geometry.path import CutPath
from geometry.profiles import Profile
from geometry.typecuts import type1, type3, type5, type6, type11
from planning.planner import RobotPlanner
from universalcontrol import URControl

zes = type6(0.1)

#print('2d pad enkel: ',zes.points)

#zes.hp_add_reference_points(width=0.10)

#print('met referentiepunten: ', zes.points)
print(zes)
pad6 = CutPath(zes)
print(pad6.path2d)


pad6_3d = pad6.angle_2d_to_3d(height=0.8, thickness=0.05)
print(pad6_3d)

#pad6.create_hp_profile(0.1, 0.005)
#print('6d pad is:')
#for i in pad6:
#    print(i)

#robot_ip = "192.168.0.43"
#home = [1,1,1,1,1,1]
#robot = URControl(robot_ip)
#planner = RobotPlanner(robot, home) # Home is de hoek van de balk

#print(planner)

#planner.create_robot_path(pad6)

#print(planner.robot_path)


#planner.execute_cut()
