import rtde_control
import rtde_receive
import rtde_io

from robotcontrol import URControl

robot_ip = "192.168.0.1"  # replace with your robot's IP address, see [How to find and set the IP address for connecting a PC to a UR robot](/t/how-to-find-and-set-the-ip-address-for-connecting-a-pc-to-a-ur-robot/4721)

home = [0.16, 0.25, 0.12, -2.83, 1.32, -0.00]

robot = URControl(robot_ip)
robot.connect()

loca = robot.get_tcp_pos()

print(loca)



velocity = 0.3
acceleration = 1
path_pose1 = [0.36, 0.25, 0.12, -2.83, 1.32, -0.00, velocity, acceleration, 0.05]
path_pose2 = [0.36, 0.45, 0.12, -2.83, 1.32, -0.00, velocity, acceleration, 0.05]
path_pose3 = [0.36, 0.45, 0.32, -2.83, 1.32, -0.00, velocity, acceleration, 0.05]
path_pose4 = [0.16, 0.45, 0.32, -2.83, 1.32, -0.00, velocity, acceleration, 0.05]
path_pose5 = [0.16, 0.25, 0.32, -2.83, 1.32, -0.00, velocity, acceleration, 0.05]
path_pose6 = [0.16, 0.25, 0.12, -2.83, 1.32, -0.00, velocity, acceleration, 0]
path = [path_pose1, path_pose2, path_pose3, path_pose4, path_pose5, path_pose6]


#robot.move_add_l([0.1,0,0,0,0,0], speed=1, acceleration = 0.1)
#robot.move_add_l([0,0.1,0,0,0,0], speed=0.1, acceleration = 2)
#robot.move_add_l([0,0,0.1,0,0,0], speed=0.1, acceleration = 5)


robot.move_l_path(path)

#robot.move_l(home, speed=1, acceleration = 0.1)

robot.stop_robot_control()