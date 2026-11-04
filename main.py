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

# TODO nulpositie v_cut gaat nog niet goed

HMI_THEMA = "modern"   # "modern" of "retro" (green phosphor terminal)

# --- Initialiseer robot en overige componenten --- 
robot = URControl(ROBOT_IP)
robot.connect()
robot.set_tcp(MARKER_ENDEFFECTOR_OFFSET)

esp = ESP32Communicator(port=SERIAL_PORT, pulses_per_mm=ENCODER_STEPS_PER_MM)

# --- Communicatie tussen HMI (hoofdthread) en robotthread ---
jobs = queue.Queue()         # HMI -> robot. Een opdracht per START, None = afsluiten
estop = threading.Event()    # wordt gezet bij noodstop; robotthread controleert dit 
laatste_job = {}             # de laatst bevestigde opdracht (profiel_args + cut_args)
robot_bezig = threading.Event()   # staat aan zolang de robotthread een opdracht uitvoert


# --- Hulpfuncties: sturen de hardware aan EN melden de stand aan de HMI ---
def clamp(nummer, dicht):
    """Zet clamp `nummer` (1-3) dicht of open en toon dat in de HMI."""
    esp.stuur_commando(f"CLAMP_{nummer}_{'ON' if dicht else 'OFF'}")
    hmi.set_clamp(nummer, dicht)


def pneumatiek(aan):
    """Zet het pneumatische systeem aan/uit en toon dat in de HMI."""
    esp.stuur_commando(f"Pneumatic_Sys_{'ON' if aan else 'OFF'}")
    hmi.set_pneumatiek(aan)


def conveyor_beweegt(functie, *args, **kwargs):
    """Voert een bandbeweging uit en toont in de HMI dat de band loopt zolang de functie bezig is.
    Werkt ervan uitgaande dat `functie` pas terugkeert als de beweging klaar is."""
    hmi.set_conveyor(True)
    try:
        return functie(*args, **kwargs)
    finally:
        hmi.set_conveyor(False)


def on_start():
    """START ingedrukt: opdracht naar de robotthread sturen."""
    estop.clear()
    jobs.put(dict(laatste_job))


def on_reset():
    """RESET ingedrukt: opdracht vergeten, zodat een nieuw profiel gesneden kan worden.
    Geeft False terug als de robotthread nog bezig is (dan mag er niet gereset worden)."""
    if robot_bezig.is_set():
        return False
    laatste_job.clear()
    esp.reset()  # reset ESP32 en encoder count (nulpositie kwijt)

    while True:                       # eventuele niet-gestarte opdrachten weggooien
        try:
            jobs.get_nowait()
        except queue.Empty:
            break
    return True


def on_noodstop():
    """NOODSTOP ingedrukt (draait in de HMI-thread): hardware DIRECT stoppen."""
    estop.set()
    robot.digital_emergency_stop()
    esp.stuur_commando("DigNoodStop")
    esp.stuur_commando("Pneumatic_Sys_OFF")
    # De HMI zet zelf de indicatoren terug (band stil, pneumatiek uit, clamps onbekend)


def robot_loop():
    """Draait in een eigen thread: wacht op opdrachten en voert ze uit."""
    while True:
        job = jobs.get()              # wacht tot de operator op START drukt
        if job is None:               # venster gesloten
            break

        robot_bezig.set()
        try:
            profile = Profile(**job["profiel_args"])


            for cut_args in job["cut_args"]:
                profile.add_cut(**cut_args)

            print(profile)

            planner = RobotPlanner(robot, HOME, profile)
            planner.move_to_rest_pos()
            estop.wait(2)

            pneumatiek(True)
            estop.wait(0.1)
            clamp(1, False)
            estop.wait(0.1)
            clamp(2, False)
            estop.wait(0.1)
            clamp(3, True)
            estop.wait(2)

            print('Conveyor beweegt naar nulpositie:')
            nul_positie = conveyor_beweegt(esp.find_profile_front, max_mm=2000)
            estop.wait(2)

            for i, cut_args in enumerate(job["cut_args"]):
                if estop.is_set():
                    break
                hmi.set_actieve_snede(i)     # toont in de HMI welke snede nu bezig is 

                print('Conveyor beweegt tot juiste snijpositie')
                cut_start = CUTTING_DISTANCE_FROM_CONVEYOR
                extra_distance = 0
                stomme_correctie = 0 # Er gaat iets fout, dit is een hotfix
                if cut_args['side']=='left' and cut_args['cuttype']=='v_cut':
                    extra_distance += 0.1
                    stomme_correctie = 0.01
                elif cut_args['side']=='right' and cut_args['cuttype']=='v_cut':
                    stomme_correctie = -0.01

                if cut_args['side'] == 'right':
                    add = profile[i].cut_width
                else:
                    add = 0

                overshoot = 0.001 * conveyor_beweegt(
                    esp.move_front_to,
                    1000*(CUTTING_DISTANCE_FROM_CONVEYOR + END_WASTE + extra_distance + profile[i].at_position + add + stomme_correctie),
                )
                print('Moving front to:', (cut_start + END_WASTE + profile[i].at_position + add))
                estop.wait(1)

                print('Clamps gaan dicht')
                clamp(1, True)
                estop.wait(0.1)
                clamp(2, True)
                estop.wait(1)
                clamp(3, False)
                estop.wait(4)

                print('Robotarm gaat nu snijden op positie:', overshoot+extra_distance+CUTTING_DISTANCE_FROM_CONVEYOR)
                planner = RobotPlanner(robot, HOME, profile)
                planner.create_robot_path(profile[i], offset=overshoot+extra_distance+CUTTING_DISTANCE_FROM_CONVEYOR)
                
                hmi.set_robot_beweegt(True)          # HMI: robotarm beweegt (hele snijcyclus)
                try:
                    planner.approach_cut()           # naar de snijpositie, plasma nog uit
                    hmi.set_plasma(True)             # HMI: plasmasnijder aan
                    try:
                        planner.execute_cut()        # daadwerkelijk snijden
                    finally:
                        hmi.set_plasma(False)
                    planner.retreat_cut()            # terugtrekken, plasma weer uit
                finally:
                    hmi.set_robot_beweegt(False)
                estop.wait(1)

                print('Clamps gaan open')
                clamp(3, True)
                estop.wait(5)
                clamp(1, False)
                estop.wait(0.1)
                clamp(2, False)
                estop.wait(2)

            conveyor_beweegt(esp.move_front_to, 1500+1000*profile.length)

            if not estop.is_set():
                hmi.snijden_klaar()

        except Exception as fout:
            traceback.print_exc()
            on_noodstop()                    # bij een fout: alles stoppen
            hmi.set_status(f"Fout: {fout}", "red")
            root.after(0, hmi.noodstop)      # UI ontgrendelen / terug naar veilige toestand
        finally:
            robot_bezig.clear()              # klaar (of gestopt): reset is weer toegestaan


# --- Start ---
root = tk.Tk()
hmi = DamenPlasmaHMI(root,on_job_submitted=laatste_job.update,on_start=on_start,on_noodstop=on_noodstop,on_reset=on_reset,thema=HMI_THEMA)

robot_thread = threading.Thread(target=robot_loop, daemon=True)
robot_thread.start()

root.mainloop()                            # Tk draait in de hoofdthread

# Venster gesloten: netjes afsluiten
estop.set()
jobs.put(None)
robot_thread.join(timeout=5)
robot.stop_robot_control()

esp.stuur_commando("Pneumatic_Sys_OFF")   # direct naar de ESP: de HMI bestaat niet meer
esp.sluit()