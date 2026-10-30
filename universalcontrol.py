import rtde_control  # for controlling the robot
import rtde_receive  # for receiving data from the robot
import rtde_io        # for robot IO

import time
import logging
import numpy as np

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class URControl:
    """Wraps ur_rtde for a UR robot. Create with the robot's IP address, then call connect()."""

    def __init__(self, robot_ip):
        self.robot_ip = robot_ip
        self.rtde_ctrl = None
        self.rtde_rec = None
        self.rtde_inout = None

    def connect(self):
        """Connect to the robot, retrying a few times if it's not ready yet."""
        max_retries = 10
        retry_delay = 0.5  # seconds between retries

        for attempt in range(1, max_retries + 1):
            try:
                self.rtde_ctrl = rtde_control.RTDEControlInterface(self.robot_ip)
                self.rtde_rec = rtde_receive.RTDEReceiveInterface(self.robot_ip)
                self.rtde_inout = rtde_io.RTDEIOInterface(self.robot_ip)
                logging.info(f"Connected to robot: {self.robot_ip} on attempt {attempt}")
                return
            except Exception as e:
                logging.error(f"Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    logging.error("Max retries reached. Unable to connect to the robot.")
                    raise

    def stop_robot_control(self):
        self.rtde_ctrl.stopScript()
        logging.info("Stopped connection with robot")

    def digital_emergency_stop(self):
        self.rtde_ctrl.stopScript()
        print("Emergency stop activated. Robot script stopped.")


    def set_tool_frame(self, tool_frame):
        try:
            self.rtde_ctrl.setTcp(tool_frame)
        except Exception as e:
            logging.error(f"Error setting tool frame: {e}")

    def set_tcp(self, tool_frame):
        self.set_tool_frame(tool_frame)

    def set_payload(self, payload, cog):
        """Set payload (kg) and center of gravity [CoGx, CoGy, CoGz]. (not tested by the original author)"""
        try:
            self.rtde_ctrl.setPayload(payload, cog)
        except Exception as e:
            logging.error(f"Cannot set CoG and/or payload: {e}")

    def set_digital_output(self, output_id, state):
        try:
            self.rtde_inout.setStandardDigitalOut(output_id, state)
            logging.info(f"Digital output {output_id} is {state}")
        except Exception as e:
            logging.error(f"Error setting digital output {output_id}: {e}")

    def pulse_digital_output(self, output_id, duration):
        """Set a digital output high for `duration` seconds, then low again."""
        self.set_digital_output(output_id=output_id, state=True)
        time.sleep(duration)
        self.set_digital_output(output_id=output_id, state=False)

    def move_l(self, pos, speed=0.5, acc=0.5):
        try:
            self.rtde_ctrl.moveL(pos, speed, acc)
            
        except Exception as e:
            logging.error(f"Cannot move: {e}")

    def move_l_path(self, path):
        try:
            self.rtde_ctrl.moveL(path)
        except Exception as e:
            logging.error(f"Cannot move: {e}")

    def move_j(self, pos, speed=0.5, acc=0.5):
        """(not tested by the original author)"""
        try:
            self.rtde_ctrl.moveJ(pos, speed, acc)
        except Exception as e:
            logging.error(f"Cannot move: {e}")

    def move_add_l(self, relative_move, speed=0.5, acc=0.5):
        """Relative linear move based on the current TCP position."""
        try:
            current_tcp_pos = self.get_tcp_pos()
            new_linear_move = [current_tcp_pos[i] + relative_move[i] for i in range(6)]
            self.move_l(new_linear_move, speed, acc)
        except Exception as e:
            logging.error(f"Cannot do relative move: {e}")

    def move_add_j(self, relative_move, speed=0.5, acc=0.5):
        """Relative joint move based on the current TCP position."""
        try:
            current_tcp_pos = self.get_tcp_pos()
            new_joint_move = [current_tcp_pos[i] + relative_move[i] for i in range(6)]
            self.move_j(new_joint_move, speed, acc)
        except Exception as e:
            logging.error(f"Cannot do relative move: {e}")

    # --- helper functions for pose_trans, since RTDE has no built-in pose_trans ---

    def rodrigues_to_rotation_matrix(self, r):
        """Convert a Rodrigues rotation vector to a rotation matrix."""
        theta = np.linalg.norm(r)
        if theta < 1e-6:  # no rotation
            return np.eye(3)
        k = r / theta
        K = np.array([
            [0, -k[2], k[1]],
            [k[2], 0, -k[0]],
            [-k[1], k[0], 0],
        ])
        return np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * np.dot(K, K)

    def pose_to_matrix(self, pose):
        """Convert a 6D pose to a 4x4 transformation matrix."""
        R = self.rodrigues_to_rotation_matrix(pose[3:])
        t = np.array(pose[:3])
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = t
        return T

    def matrix_to_pose(self, matrix):
        """Convert a 4x4 transformation matrix back to a 6D pose."""
        R = matrix[:3, :3]
        t = matrix[:3, 3]
        theta = np.arccos((np.trace(R) - 1) / 2)
        if theta < 1e-6:
            r = np.zeros(3)
        else:
            r = theta / (2 * np.sin(theta)) * np.array([
                R[2, 1] - R[1, 2],
                R[0, 2] - R[2, 0],
                R[1, 0] - R[0, 1],
            ])
        return np.concatenate((t, r))

    def pose_trans(self, pose1, pose2):
        """Combine two poses via matrix multiplication (equivalent to Polyscope's pose_trans)."""
        T1 = self.pose_to_matrix(pose1)
        T2 = self.pose_to_matrix(pose2)
        T_result = np.dot(T1, T2)
        return self.matrix_to_pose(T_result)

    def get_tcp_pos(self):
        try:
            return self.rtde_rec.getActualTCPPose()
        except Exception as e:
            logging.error(f"Cannot return actual TCP pose: {e}")

    def get_joint_pos(self):
        try:
            return self.rtde_rec.getActualQ()
        except Exception as e:
            logging.error(f"Cannot return actual joint pose: {e}")

    def set_tcp_rotation(self, rx, ry, rz, speed=0.1, acc=0.1):
        """Set the rotation of the TCP, in degrees, keeping the current position."""
        current_pose = self.get_tcp_pos()  # [x, y, z, rx, ry, rz]
        current_pose[3] = rx
        current_pose[4] = ry
        current_pose[5] = rz
        self.move_l(current_pose, speed, acc)


    def add_home(self, home, coordinaat):
        return (np.array(home) + np.array(coordinaat)).tolist()



if __name__ == '__main__':
    robot = URControl('192.168.0.1')
    robot.connect()
    robot.stop_robot_control()