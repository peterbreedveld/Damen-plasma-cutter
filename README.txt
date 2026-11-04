DAMEN ROBOT PLASMASNIJDER
=========================

Een UR-cobot snijdt met een plasmatoorts sneden in stalen profielen
(rechthoekig, Holland/bulb, hoekprofiel). De operator voert profiel en sneden
in via een HMI. Een loopband brengt het profiel op positie, clamps houden het
vast en de robot snijdt.


HOE HET WERKT
-------------

  HMI (Tkinter) --opdracht--> main.py --> robot-thread
                                            |- Profile -> sneden -> 3D-pad -> 6D-robotpad
                                            |- RobotPlanner / URControl (UR-robot)
                                            '- ESP32Communicator --USB--> ESP32
                                                 (loopband, encoder, lichtsluis,
                                                  clamps, noodstop)

  1. Operator kiest profiel + afmetingen, voegt sneden toe en BEVESTIGT.
     Pas daarna werkt START.
  2. De band rijdt het profiel tot de voorkant de lichtsluis raakt. Die
     encoderstand is het NULPUNT.
  3. Per snede: profiel op positie -> clamps dicht -> snijden -> clamps open.
     De HMI toont de actieve snede.


PROJECTSTRUCTUUR (indicatief, afgeleid uit de imports)
------------------------------------------------------

  main.py                    start HMI (hoofdthread) en robot-thread
  HumanInterface.py          Tkinter-HMI (DamenPlasmaHMI)
  config/settings.py         alle instellingen en kalibratiewaarden
  geometry/profiles.py       Profile: profieltype, afmetingen, add_cut()
  geometry/typecuts.py       3D-snijpad per snedetype
  geometry/path.py           Node, CutPath (3D -> 6D)
  planning/planner.py        paden naar robotcoordinaten
  universalcontrol.py        UR-aansturing (URControl)
  esp32_communicator.py      seriele communicatie met de ESP32
  ESP32-firmware (.ino)      band, encoder, lichtsluis, clamps, noodstop


PROFIELEN EN SNEDEN
-------------------

  Profiel       Code                                Sneden
  -----------   ---------------------------------   -------------------------------
  Rectangular   Rect                                v_cut, type85 (nog te programmeren)
  Holland       HP                                  type6, type9 (hoek Y < 45 graden)
  Angular       Angle (AngleEven: hoogte=breedte)   type11, type83

  Profile.add_cut(cuttype, position, side, ...) zoekt de snijfunctie in
  CUT_FUNCTIONS, maakt het 3D-pad, zet dat om naar 6D en bewaart "position"
  (positie van de snede langs het profiel).

  Een nieuw snedetype toevoegen: functie in typecuts.py, regel in
  CUT_FUNCTIONS en regel in de HMI-definitie.

  Eenheden: HMI in mm, de rest in meter en graden (rotaties als rotatievector
  in radialen).
  Profielstelsel: x = lengte, y = breedte, z = hoogte; oorsprong in de
  onderste hoek.


STARTEN
-------

  pip install numpy pyserial     (tkinter zit bij Python; Linux: python3-tk)
  python main.py                 (Esc = schermvullend verlaten)

  Zet vooraf SERIAL_PORT en ROBOT_IP in config/settings.py en flash de ESP32
  (115200 baud).


BELANGRIJKSTE INSTELLINGEN (config/settings.py)
-----------------------------------------------

  START_OFFSET, NOZZLE_DISTANCE, END_WASTE
      aanloopafstand, tuitafstand tot materiaal, ongebruikt stuk aan het begin
  SAFE_SPEED, APPROACH_SPEED, CORNER_SPEED
      snelheden rond/naar het profiel en om hoeken
  SPEED_PER_THICKNESS
      snijsnelheid per dikte. De dikte (in m) is de sleutel; een onbekende
      dikte geeft een KeyError
  ACC, SMOOTHNESS, CURVE
      versnelling, blend-radius xy, blend-radius z
  SERIAL_PORT, ROBOT_IP
      verbindingen
  HOME
      onderste hoek van de balk op de lichtsluis (robotcoordinaten)
  ENCODER_STEPS_PER_MM
      KALIBREREN met loopband en encoder
  MARKER_ENDEFFECTOR_OFFSET
      KALIBREREN via de cobot
  CUTTING_DISTANCE_FROM_CONVEYOR
      minimale afstand snijkop - band


LOOPBAND EN NULPUNT (ESP32)
---------------------------

  esp = ESP32Communicator(pulses_per_mm=ENCODER_STEPS_PER_MM)
  esp.find_profile_front(max_mm=2000)  # rijden tot lichtsluis -> nulpunt vastleggen
  esp.move_front_to(400)               # voorkant 400 mm voorbij de sluis
  esp.move_mm(150)                     # 150 mm vooruit -> MoveResult(before, after,
                                       #   travelled_mm, ...)
  esp.front_position_mm()              # positie voorkant t.o.v. de sluis

  - Het nulpunt is de encoderstand op het exacte moment van de
    lichtsluis-trigger. De encoder wordt niet gereset (RESET wist het
    nulpunt).
  - De sluis is standaard UIT en alleen actief tijdens find_profile_front
    (GATE_IGNORE_ON/OFF). GATE_BLANK blokkeert hem even na de start, en een
    trigger telt pas als hij 10 ms dicht blijft (GATE_GLITCH = gefilterd).
  - Commando's: BELT_ON/OFF, SPEED_FAST/SLOW, CLAMP_1/2_ON/OFF,
    Pneumatic_Sys_ON/OFF, MOVE:<pulsen>, encoderVal (-> ENC:<n>), RESET,
    GATE_*, DigNoodStop.
  - De band kan alleen vooruit. Stel overshoot_pulses (uitloop) en
    settle_tolerance in na kalibratie.


VEILIGHEID
----------

  - De NOODSTOP-knop in de HMI is GEEN veiligheidsvoorziening: gebruik altijd
    de fysieke noodstop van robot en installatie.
  - De hardware-noodstop op de ESP32 (GPIO 15) zet band en pneumatiek uit en
    LAAT DE CLAMPS LOS. Controleer of dat gewenst is.
  - In main.py zijn de stopcommando's voor robot en band in on_noodstop()
    nog TODO.


TO-DO
-----

  - rect_type85 programmeren, hoeken (angles) voor de rechthoekige balk
    afmaken
  - Hoofdloop in main.py afmaken: planner, loopband en clamps koppelen
  - CutPath.reverse() gebruikt self.path, dat niet bestaat (path3d/path6d)