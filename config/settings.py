# Behaviour configuration
END_WASTE = 0.01 # Stukje materiaal dat aan begin van profiel niet wordt gebruikt
START_OFFSET = 0.01 # Extra afstand van de snijkop tot het materiaal bij het starten van een snede (zodat de snijkop niet tegen het materiaal aan komt)
NOZZLE_DISTANCE = 0.0015 # Afstand van punt van end effector (stift) tot materiaal


# Settings
SAFE_SPEED = 0.4 # Snelheid bij bewegingen rondom het profiel
APPROACH_SPEED = 0.08 # Snelheid bij benaderen profiel
CORNER_SPEED = 0.25 # Snijsnelheid om de hoeken heen
SPEED_PER_THICKNESS = {0.002:0.015, 0.0033:0.015, 0.004:0.015, 0.0044:0.015, 0.005:0.015, 0.015:0.007} # Voeg diktes toe indien nodig. Snelheid van snijden

ACC = 1 # Acceleratie van de robot, 
SMOOTHNESS = 0.001 # Cirkel om node heen waar pad doorheen wordt gesmooth (blend radius voor xy veranderingen)
CURVE = 0.002 # Blend radius voor Z verandering


# Environment configuration
SERIAL_PORT = "COM3" # Laptoppoort met usb kabel naar ESP
ROBOT_IP = "192.168.0.43" #IP adress van de robot, vindbaar in de settings van robot
HOME = [-0.3338166924541298, 0.7682243848336712, 0.09463601540163476, 0, 0, 0] # Coordinaat van de onderste hoek van de balk op de light gate
MARKER_ENDEFFECTOR_OFFSET = [-0.05623, 0, 0.14853, 0.7884, -0.7227, -1.5267] # Calibreer deze via de cobot zelf

ENCODER_STEPS_PER_MM = 6.4 # Calibreer dit met de conveyor en encoder (Aantal encoder stappen per mm van de loopband)
# enc was 6.31 na Excel
CUTTING_DISTANCE_FROM_CONVEYOR = 0.15 # Minimale afstand van de snijkop tot de loopband (zodat de snijkop niet tegen de band aan komt)


# Old end effectors
BLUE_PIPE_OFFSET = [0.01971, 0.00202, 0.1253, 0.6484, -0.1938, 3.0477]
ANGLE_PRINT_OFFSET = [0.0879, -0.0667, 0.1461, 1.5713, 0.3712, 0.8294]
PINK_ANGLEPRINT_OFFSET = [-0.0418, 0.0576, 0.150, 0.295, -0.949, -2.229]
OLD_MARKER_ENDEFFECTOR_OFFSET = [-0.005668, -0.00067, 0.14877, 0.7704, -0.7504, -1.4578]