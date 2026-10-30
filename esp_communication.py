import serial
import threading
import time
from collections import namedtuple
from config.settings import SERIAL_PORT, ENCODER_STEPS_PER_MM

# Encoder counts per mm of belt travel. MUST be calibrated: move the belt a long, known
# distance (1 m or more) and divide the counted pulses by the measured mm.

# before/after = encoder count before the move and after the belt has fully stopped
# gate_count   = count at the moment the gate triggered during this move (None = no trigger)
# overshoot_pulses = how far the belt coasted past the point where the ESP32 switched it off
MoveResult = namedtuple("MoveResult", "before after travelled_mm gate_count overshoot_pulses")


class ESP32Communicator:
    def __init__(self, port=SERIAL_PORT, baudrate=115200,
                 pulses_per_mm=ENCODER_STEPS_PER_MM, overshoot_pulses=0, settle_tolerance=5):
        self.running = False
        self.ser = None
        self.pulses_per_mm = pulses_per_mm
        self.overshoot_pulses = overshoot_pulses   # coasting distance to subtract from every move
        self.settle_tolerance = settle_tolerance   # max. count flicker (pulses) that still counts as 'stopped'

        # Results of the last belt move, filled in by the background thread
        self.move_done = threading.Event()   # set when the belt stopped (gate or target reached)
        self.gate_position = None            # encoder count at the gate during the last move
        self._gate_armed = False             # True only while a move i allowed to stop at the gate
        self.overshoot = None                # overshoot as reported by the ESP32 itself

        # Encoder readout
        self._encoder_event = threading.Event()
        self._encoder_value = None

        # Zero point: encoder count at the moment the profile front hit the gate
        self.zero_count = None

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

    def stuur_commando(self, commando, verbose=True):
        """Send a command including newline to the ESP32"""
        if self.running:
            if commando == "RESET":
                self.zero_count = None   # encoder restarts at 0: the old zero point is invalid
            self.ser.write(f"{commando}\n".encode("utf-8"))
            if verbose:
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
                if not regel.startswith("ENC:"):     # encoder polling would flood the console
                    print(f"[ESP32 ZEGT] <- {regel}")
                self._verwerk_bericht(regel)

    def _verwerk_bericht(self, bericht):
        """Route an incoming message to the right logic"""
        if bericht.startswith("ENC:"):
            self._encoder_value = int(bericht.split(":")[1])
            self._encoder_event.set()

        elif bericht.startswith("GATE_TRIGGER:"):
            # Value frozen by the ISR at the exact moment the gate triggered
            if not self.move_done.is_set():          # only the first trigger counts (bounce)
                self.gate_position = int(bericht.split(":")[1])
                self.move_done.set()

        elif bericht.startswith("STATUS:TARGET_REACHED"):
            self.move_done.set()                     # target reached, gate_position stays None

        elif bericht.startswith("OVERSHOOT:"):
            self.overshoot = int(bericht.split(":")[1])

    # ------------------------------------------------------------------
    # Encoder
    # ------------------------------------------------------------------

    def read_encoder(self, timeout=1.0):
        """Ask the ESP32 for the current encoder count."""
        self._encoder_event.clear()
        self.stuur_commando("encoderVal", verbose=False)
        if not self._encoder_event.wait(timeout):
            raise TimeoutError("Geen 'ENC:' antwoord van de ESP32 (firmware aangepast?)")
        return self._encoder_value

    def _wait_until_settled(self, window=0.3, poll=0.05, timeout=5.0):
        """
        Wait until the belt has stopped and return the settled encoder count.
        The belt counts as stopped when the count varied by no more than `settle_tolerance`
        pulses during the last `window` seconds. A tolerance is needed because the encoder
        can keep flickering by a few counts at standstill. The median of the readings in that
        window is returned, so a single stray count doesn't end up in the result.
        """
        deadline = time.time() + timeout
        metingen = []                                    # (time, count)
        while time.time() < deadline:
            nu = time.time()
            metingen.append((nu, self.read_encoder()))
            recent = [c for t, c in metingen if nu - t <= window]
 
            heeft_hele_window = nu - metingen[0][0] >= window
            if heeft_hele_window and max(recent) - min(recent) <= self.settle_tolerance:
                return sorted(recent)[len(recent) // 2]  # median
            time.sleep(poll)
 
        raise TimeoutError(
            f"Band komt niet tot stilstand: telling varieerde {min(recent)}..{max(recent)} "
            f"in de laatste {window} s (settle_tolerance={self.settle_tolerance})"
        )

    # ------------------------------------------------------------------
    # Moving
    # ------------------------------------------------------------------

    def move_mm(self, distance_mm, timeout=30, use_gate=False):
        """
        Move the belt forward `distance_mm`. Returns a MoveResult with the encoder count
        before and after the move (measured once the belt has fully stopped).
        If the gate triggers during the move the ESP32 stops the belt early:
        result.gate_count is then set and travelled_mm is shorter than requested.
        """
        if not self.running:
            raise RuntimeError("Geen verbinding met de ESP32")
        if distance_mm <= 0:
            raise ValueError("De band kan alleen vooruit")

        pulses = round(distance_mm * self.pulses_per_mm) - self.overshoot_pulses
        if pulses < 1:
            raise ValueError("Afstand is korter dan de uitloop van de band")

        # Clear old results BEFORE sending, otherwise a fast reply could be wiped
        self.gate_position = None
        self.overshoot = None
        self.move_done.clear()


        try:
            before = self.read_encoder()                 # belt is stationary: exact start count
            self.stuur_commando(f"MOVE:{pulses}")

            if not self.move_done.wait(timeout):
                print('Not done in 30 secs')
                self.stuur_commando("BELT_OFF")
                raise TimeoutError(f"Band niet gestopt binnen {timeout} s")

            print('trying to wait until settled')
            after = self._wait_until_settled()
        finally:
            # Back to the safe default: the gate is ignored again
            self._gate_armed = False
            self.stuur_commando("GATE_IGNORE_ON")

        gate = self.gate_position
        stop_count = gate if gate is not None else before + pulses   # where the ESP32 cut the motor
        return MoveResult(before, after, (after - before) / self.pulses_per_mm,
                          gate, after - stop_count)

    # ------------------------------------------------------------------
    # Profile front relative to the gate
    # ------------------------------------------------------------------

    def find_profile_front(self, max_mm, timeout=30):
        """
        Run the belt until the gate sees the front of the profile and make the encoder count
        at that exact moment the zero point. Raises RuntimeError if no profile is found.
        """
        result = self.move_mm(max_mm, timeout, use_gate=True)
        if result.gate_count is None:
            raise RuntimeError(f"Geen profiel gevonden binnen {max_mm} mm")
        self.zero_count = result.gate_count
        return result

    def front_position_mm(self, count=None):
        """
        Position of the profile front relative to the gate in mm (positive = past the gate).
        Uses the given encoder count, or reads the current one.
        """
        if self.zero_count is None:
            raise RuntimeError("Nulpunt onbekend: voer eerst find_profile_front() uit")
        if count is None:
            count = self.read_encoder()
        return (count - self.zero_count) / self.pulses_per_mm

    def move_front_to(self, target_mm, tolerance_mm=0.5, max_corrections=2, timeout=30):
        """
        Move the belt so the profile front ends up `target_mm` past the gate (the zero point).
        The belt can only go forward, so the target must be ahead of the current front position.
        If the belt stops short (overshoot compensation too big, or the gate stopped it early),
        it moves on in up to `max_corrections` extra steps.
        Returns the overshoot in mm.
        """
        positie = self.front_position_mm()
        if target_mm < positie - tolerance_mm:
            raise ValueError(f"Doel ({target_mm:.1f} mm) ligt achter de huidige positie "
                             f"({positie:.1f} mm): de band kan niet achteruit")

        for _ in range(1 + max_corrections):
            afstand = target_mm - positie
            if afstand <= tolerance_mm:
                break                                            # there (or slightly past)
            if round(afstand * self.pulses_per_mm) <= self.overshoot_pulses:
                break                                            # shorter than the coasting distance
            result = self.move_mm(afstand, timeout)
            positie = self.front_position_mm(result.after)       # settled count, no extra read

        if abs(positie - target_mm) > tolerance_mm:
            print(f"WAARSCHUWING: voorkant staat op {positie:.1f} mm, doel was {target_mm:.1f} mm")
        return positie - target_mm

    def sluit(self):
        """Close the serial port safely"""
        if self.running:
            self.running = False
            self.ser.close()
            print("Seriële verbinding gesloten.")


# --- Test Script ---
if __name__ == "__main__":
    esp = ESP32Communicator(port=SERIAL_PORT)

    if esp.running:
        try:
            # 1. Drive until the profile front hits the gate -> that count is the zero point
            r = esp.find_profile_front(max_mm=2000)
            print(f"Gate op telling {r.gate_count}, band stond stil op {r.after}")
            print(f"Voorkant profiel staat nu {esp.front_position_mm():.1f} mm voorbij de lichtsluis")

            # 2. Move 150 mm and see exactly where the front ended up
            r = esp.move_mm(150)
            print(f"voor={r.before} na={r.after} verplaatst={r.travelled_mm:.1f} mm "
                  f"uitloop={r.overshoot_pulses} pulsen")
            print(f"Voorkant profiel staat nu {esp.front_position_mm(r.after):.1f} mm voorbij de lichtsluis")

            # 3. Put the front at exactly 400 mm past the gate
            positie = esp.move_front_to(400)
            print(f"Voorkant profiel staat nu op {positie:.1f} mm voorbij de lichtsluis")
        finally:
            esp.sluit()