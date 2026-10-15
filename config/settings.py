# Behaviour configuration
END_WASTE = 0.01
START_OFFSET = 0.01
NOZZLE_DISTANCE = 0.005


# Environment configuration
SERIAL_PORT = "COM3"
BLUE_PIPE_OFFSET = [0.01971, 0.00202, 0.1253, 0.6484, -0.1938, 3.0477]
ANGLE_PRINT_OFFSET = [0.0879, -0.0667, 0.1461, 1.5713, 0.3712, 0.8294]
PINK_ANGLEPRINT_OFFSET = [-0.0418, 0.0576, 0.150, 0.295, -0.949, -2.229]

ENCODER_STEPS_PER_MM = 12540/2148
CUTTING_DISTANCE_FROM_CONVEYOR = 0.25


# Settings
SAFE_SPEED = 0.1
APPROACH_SPEED = 0.01
CORNER_SPEED = 0.15
SPEED_PER_THICKNESS = {0.004:0.01, 0.005:0.02, 0.006:0.01, 0.008:0.01, 0.01:0.009, 0.015:0.007}

ACC = 1
SMOOTHNESS = 0.001 # Cirkel om node heen waar pad doorheen wordt gesmooth (blend radius voor xy veranderingen)
CURVE = 0.002 # Blend radius voor Z verandering