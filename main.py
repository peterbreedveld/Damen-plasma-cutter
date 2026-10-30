import queue
import threading
import traceback
import tkinter as tk

from HumanInterface import DamenPlasmaHMI
from geometry.profiles import Profile
from config.settings import *
from universalcontrol import URControl
from planning.planner import RobotPlanner
from geometry.typecuts import *
from esp_communication import ESP32Communicator

### TO-DO's
# TODO type9 voor andere kant van de balk
# TODO Profiel verder of minder ver duwen afhangkelijk van l of r snijkant (schuin snijden, dus ruimte voor robot pols)
# TODO Alles testen met nieuwe end effector (misschien widthwise v-cut versimpelen dan)

ROBOT_IP = "192.168.0.43"
HOME = [-0.3401, 0.7702, 0.0946, 0, 0, 0]   # Home is de hoek van de balk

# --- Initialiseer robot en overige componenten ---
robot = URControl(ROBOT_IP)
robot.connect()
robot.set_tcp(MARKER_ENDEFFECTOR_OFFSET)

esp = ESP32Communicator(port=SERIAL_PORT, pulses_per_mm=ENCODER_STEPS_PER_MM)

# --- Communicatie tussen HMI (hoofdthread) en robotthread ---
jobs = queue.Queue()         # HMI -> robot. Een opdracht per START, None = afsluiten
estop = threading.Event()    # wordt gezet bij noodstop; robotthread controleert dit
laatste_job = {}             # de laatst bevestigde opdracht (profiel_args + cut_args)


def on_start():
    """START ingedrukt: opdracht naar de robotthread sturen."""
    estop.clear()
    jobs.put(dict(laatste_job))


def on_noodstop():
    """NOODSTOP ingedrukt (draait in de HMI-thread): hardware DIRECT stoppen."""
    estop.set()
    robot.digital_emergency_stop()
    esp.stuur_commando("DigNoodStop")
    esp.stuur_commando("Pneumatic_Sys_OFF")


def robot_loop():
    """Draait in een eigen thread: wacht op opdrachten en voert ze uit."""
    while True:
        job = jobs.get()              # wacht tot de operator op START drukt
        if job is None:               # venster gesloten
            break

        try:
            profile = Profile(**job["profiel_args"])


            for cut_args in job["cut_args"]:
                profile.add_cut(**cut_args)

            print(profile)

            planner = RobotPlanner(robot, HOME, profile)
            planner.move_to_rest_pos()
            estop.wait(2)

            esp.stuur_commando("Pneumatic_Sys_ON")
            estop.wait(0.1)
            esp.stuur_commando("CLAMP_1_OFF")
            estop.wait(0.1)
            esp.stuur_commando("CLAMP_2_OFF")
            estop.wait(0.1)
            esp.stuur_commando("CLAMP_3_ON")
            estop.wait(2)

            print('Conveyor beweegt naar nulpositie:')
            nul_positie = esp.find_profile_front(max_mm=2000)
            estop.wait(2)

            for i, cut_args in enumerate(job["cut_args"]):
                if estop.is_set():
                    break
                hmi.set_actieve_snede(i)     # toont in de HMI welke snede nu bezig is 

                print('Conveyor beweegt tot juiste snijpositie')
                cut_start = CUTTING_DISTANCE_FROM_CONVEYOR
                extra_distance = 0
                if cut_args['side']=='left' and cut_args['cuttype']=='v_cut':
                    extra_distance += 0.1

                overshoot = 0.001 * esp.move_front_to(1000*(CUTTING_DISTANCE_FROM_CONVEYOR+extra_distance + profile[i].at_position + profile[i].cut_width))
                print('Moving front to:', (cut_start + profile[i].at_position + profile[i].cut_width))
                estop.wait(1)

                print('Clamps gaan dicht')
                esp.stuur_commando("CLAMP_1_ON")
                estop.wait(0.1)
                esp.stuur_commando("CLAMP_2_ON")
                estop.wait(1)
                esp.stuur_commando("CLAMP_3_OFF")
                estop.wait(4)

                print('Robotarm gaat nu snijden op positie:', overshoot+extra_distance+CUTTING_DISTANCE_FROM_CONVEYOR)
                planner = RobotPlanner(robot, HOME, profile)
                planner.create_robot_path(profile[i], offset=overshoot+extra_distance+CUTTING_DISTANCE_FROM_CONVEYOR)
                planner.execute_cut()
                estop.wait(1)

                print('Clamps gaan open')
                esp.stuur_commando("CLAMP_3_ON")
                estop.wait(5)
                esp.stuur_commando("CLAMP_1_OFF")
                estop.wait(0.1)
                esp.stuur_commando("CLAMP_2_OFF")
                estop.wait(2)

            esp.move_front_to(1000*profile.length)

            if not estop.is_set():
                hmi.snijden_klaar()

        except Exception as fout:
            traceback.print_exc()
            on_noodstop()                    # bij een fout: alles stoppen
            hmi.set_status(f"Fout: {fout}", "red")
            root.after(0, hmi.noodstop)      # UI ontgrendelen / terug naar veilige toestand


# --- Start ---
root = tk.Tk()
hmi = DamenPlasmaHMI(root,on_job_submitted=laatste_job.update,on_start=on_start,on_noodstop=on_noodstop,)

robot_thread = threading.Thread(target=robot_loop, daemon=True)
robot_thread.start()

root.mainloop()                            # Tk draait in de hoofdthread

# Venster gesloten: netjes afsluiten
estop.set()
jobs.put(None)
robot_thread.join(timeout=5)
robot.stop_robot_control()

esp.stuur_commando("Pneumatic_Sys_OFF")
esp.sluit()