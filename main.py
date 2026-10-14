from HumanInterface import DamenPlasmaHMI
from geometry.profiles import Profile
from config.settings import *
from universalcontrol import URControl
from planning.planner import RobotPlanner
from geometry.typecuts import *
import threading
import tkinter as tk

import numpy as np

job_condition = threading.Condition()
job_data = None
start_requested = False
shutdown_requested = False


### TO-DO's
# Maak gehele main loop met inpunts en outputs
# Maak type9 voor andere kant van de balk en
# Maak de angles voor rectangle balk


# Initialiseer robot
robot_ip = "192.168.0.43"  
home = [-0.091, 0.786, 0.0946, 0, 0, 0]
'''
robot = URControl(robot_ip)
robot.connect()

robot.set_tcp(PINK_ANGLEPRINT_OFFSET)
'''
#EXECUTION
def interface_loop():
    root = tk.Tk()
    global app
    app = DamenPlasmaHMI(
        root,
        on_job_submitted=receive_job,
        on_start=signal_start,
    )

    def close_interface():
        signal_shutdown()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close_interface)
    root.mainloop()


def receive_job(data):
    global job_data
    with job_condition:
        job_data = data
        job_condition.notify_all()


def signal_start():
    global start_requested
    with job_condition:
        start_requested = True
        job_condition.notify_all()


def signal_shutdown():
    global shutdown_requested
    with job_condition:
        shutdown_requested = True
        job_condition.notify_all()



def robot_loop():
    global job_data
    try:
        with job_condition:
            job_condition.wait_for(
                lambda: shutdown_requested or (job_data is not None and start_requested)
            )
            if shutdown_requested:
                return
            received_job = job_data

        print("Opdracht ontvangen:", received_job)
        profile = Profile(**received_job["profiel_args"])
        for cut_args in received_job["cut_args"]:
            profile.add_cut(**cut_args)

        #planner = RobotPlanner(robot, home, profile) # Home is the corner van de balk
        #planner.create_robot_paths() # Converts path to robot coordinates
        #planner.execute_cut()
    finally:
        None
        #robot.stop_robot_control()

    
t1 = threading.Thread(target=interface_loop)
t2 = threading.Thread(target=robot_loop)


t1.start()
t2.start()
t1.join()
t2.join()

# Startknop start conveyor tot balk bij locatie bij arm
# In: positie van de balk

# Clamp pistons
# Execute cut 1
# Out: Move conveyor x steps/x distance
# 
# repeat for every cut
