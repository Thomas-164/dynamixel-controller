import time
import numpy as np
from dynio.dynamixel_controller import DynamixelIO
from dynamixel_sdk import *  # Uses Dynamixel SDK library

dxl_io = DynamixelIO('COM3', 921600)

motor = dxl_io.new_three_mxl_motor(106)
motor.set_velocity_mode()
motor.set_acceleration(1500)
motor.start_heartbeat()
# motor.set_current(1)
motor2 = dxl_io.new_three_mxl_motor(107)
motor2.set_velocity_mode()
motor2.set_acceleration(1500)
motor2.start_heartbeat()
# motor2.set_current(1)


def get_state():
    motor_status = {}
    for motor_ in [motor, motor2]:
        id_ = motor_.dxl_id
        motor_status[id_] = {
            'voltage': motor_.get_voltage(),
            'current': motor_.get_current(),
            'p current': motor_.get_p_current(),
            'i current': motor_.get_i_current(),
            'd current': motor_.get_d_current(),
            'il current': motor_.get_il_current(),
            'torque': motor_.get_torque(),
            'angle': motor_.get_angle(),
            'angular_rate': motor_.get_angular_rate(),
            'position': motor_.get_position(),
            'velocity': motor_.get_velocity(),
        }

    return motor_status


x = 0
while True:

    if x == 11:
        x = 0

    command = input("> ")
    if not command:
        state = get_state()
        for el in state:
            print(f"-- Motor {el} --")
            for key, value in state[el].items():
                print(f"{key}: {value}")
    else:
        motor.set_velocity(int(command))
        motor2.set_velocity(int(command))

    # motor.set_velocity(x)
    # motor2.set_velocity(x)
    # time.sleep(2)

    # status = get_status()
    # for motor_ in status:
    #     print(f"-- Motor {motor_} --")
    #    for key, value in status[motor_].items():
    #        print(f"{key}: {value}")
    #    print()

    # x += 1
