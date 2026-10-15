import serial
import threading
import time
from config.settings import SERIAL_PORT


class ESP32Communicator:
    def __init__(self, port=SERIAL_PORT, baudrate=115200):
        self.running = False
        self.ser = None

        # Results of the last belt move, filled in by the background thread
        self.move_done = threading.Event()   # set when the belt stopped (gate or target reached)
        self.gate_position = None            # encoder count at the moment the gate triggered
        self.overshoot = None                # pulses the belt coasted after it stopped

        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            self.running = True

            # Background thread that continuously reads incoming messages
            self.listen_thread = threading.Thread(target=self._read_from_serial, daemon=True)
            self.listen_thread.start()
            print(f"Succesvol verbonden met ESP32 op {port}")
            time.sleep(2)  # wait until the ESP32 has booted
        except serial.SerialException as e:
            print(f"Kan geen verbinding maken met {port}: {e}")
            self.running = False

    def stuur_commando(self, commando):
        """Send a command including newline to the ESP32"""
        if self.running:
            self.ser.write(f"{commando}\n".encode("utf-8"))
            print(f"\n[PC STUURT] -> {commando}")

    def _read_from_serial(self):
        """Runs in the background and handles every message as soon as it arrives"""
        while self.running:
            try:
                # Blocks for max. 1 s (the port timeout), so no busy-waiting
                regel = self.ser.readline().decode("utf-8", errors="ignore").strip()
            except (serial.SerialException, OSError):
                break  # port was closed
            if regel:
                print(f"[ESP32 ZEGT] <- {regel}")
                self._verwerk_bericht(regel)

    def _verwerk_bericht(self, bericht):
        """Route an incoming message to the right logic"""
        if bericht.startswith("GATE_TRIGGER:"):
            # Value frozen by the ISR at the exact moment the gate triggered
            if not self.move_done.is_set():          # only the first trigger counts (bounce)
                self.gate_position = int(bericht.split(":")[1])
                self.move_done.set()

        elif bericht.startswith("STATUS:TARGET_REACHED"):
            self.move_done.set()                     # target reached, gate_position stays None

        elif bericht.startswith("OVERSHOOT:"):
            self.overshoot = int(bericht.split(":")[1])

    def move_until_gate(self, max_pulses, timeout=30):
        """
        Run the belt for at most `max_pulses`; the ESP32 stops it as soon as the gate triggers.
        Returns the encoder count at the gate, or None if the target was reached without
        the gate triggering. Raises TimeoutError if nothing happens within `timeout` seconds.
        """
        if not self.running:
            raise RuntimeError("Geen verbinding met de ESP32")

        # Clear old results BEFORE sending, otherwise a fast reply could be wiped
        self.gate_position = None
        self.overshoot = None
        self.move_done.clear()

        self.stuur_commando(f"MOVE:{max_pulses}")

        if not self.move_done.wait(timeout):
            self.stuur_commando("BELT_OFF")
            raise TimeoutError(f"Band niet gestopt binnen {timeout} s")

        return self.gate_position

    def sluit(self):
        """Close the serial port safely"""
        if self.running:
            self.running = False
            self.ser.close()
            print("Seriële verbinding gesloten.")


# --- Test Script ---
if __name__ == "__main__":
    esp = ESP32Communicator(port=SERIAL_PORT)

    esp.stuur_commando("Pneumatic_Sys_ON")
    time.sleep(2)
    esp.stuur_commando("CLAMP_1_ON")
    time.sleep(2)
    esp.stuur_commando("CLAMP_2_OFF")
    time.sleep(2)
    esp.stuur_commando("MOVE:200")
    time.sleep(2)
    esp.sluit()