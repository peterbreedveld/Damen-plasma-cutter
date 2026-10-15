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
# Maak type9 voor andere kant van de balk
# Maak de angles voor rectangle balk

ROBOT_IP = "192.168.0.43"
HOME = [-0.091, 0.786, 0.0946, 0, 0, 0]   # Home is de hoek van de balk

# --- Initialiseer robot en overige componenten ---
robot = URControl(ROBOT_IP)
robot.connect()
robot.set_tcp(PINK_ANGLEPRINT_OFFSET)

esp = ESP32Communicator(port=SERIAL_PORT)

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
            # TODO: planner aanmaken en paden berekenen
            # planner = RobotPlanner(robot, HOME, profile)
            # planner.create_robot_paths()   # zet pad om naar robotcoordinaten

            esp.stuur_commando("Pneumatic_Sys_ON")
            esp.stuur_commando("CLAMP_1_OFF")
            esp.stuur_commando("CLAMP_2_OFF")

            nul_positie = esp.move_until_gate(max_pulses=100000, timeout=30)
            print(nul_positie)

            for i, cut_args in enumerate(job["cut_args"]):
                if estop.is_set():
                    break
                hmi.set_actieve_snede(i)     # toont in de HMI welke snede nu bezig is

                #Check claude code en continue process
                CUTTING_DISTANCE_FROM_CONVEYOR+END_WASTE
                # 1. Conveyor: balk naar de juiste positie brengen
                print(f"[{i + 1}] TODO conveyor verplaatsen")
                estop.wait(1)                # vervang door echte aansturing

                # 2. Clamp pistons dicht
                print(f"[{i + 1}] TODO clamps dicht")
                estop.wait(1)

                # 3. Snede uitvoeren
                print(f"[{i + 1}] TODO snijden: {cut_args}")
                # planner.execute_cut()      # eventueel per snede, afhankelijk van je planner
                estop.wait(1)

                # 4. Clamp pistons open
                print(f"[{i + 1}] TODO clamps open")
                estop.wait(1)

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
robot.move_l(HOME, speed=0.02, acc=0.5)  # naar homepositie

root.mainloop()                            # Tk draait in de hoofdthread

# Venster gesloten: netjes afsluiten
estop.set()
jobs.put(None)
robot_thread.join(timeout=5)
robot.stop_robot_control()

esp.stuur_commando("Pneumatic_Sys_OFF")
esp.sluit()