import time
from dynio.dynamixel_controller import DynamixelIO

dxl_io = DynamixelIO('COM3', 921600)

motor = dxl_io.new_three_mxl_motor(106)
motor.set_mode_speed()
motor.set_acceleration(1000)

motor2 = dxl_io.new_three_mxl_motor(107)
motor2.set_mode_speed()
motor2.set_acceleration(1000)

while True:
    command = input("> ")
    motor.set_speed(int(command))
    motor2.set_speed(int(command))


# motor.set_speed_mode()

# motor.set_speed(1)

# prev = motor.get_pos()

# while True:
#    time.sleep(1)
#    pos = motor.get_pos()
#    print(f'Pos: {pos}')
#    print(f'Speed: {pos - prev}')
#    prev = pos
