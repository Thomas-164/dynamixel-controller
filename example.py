import time
from dynio.dynamixel_controller import DynamixelIO

dxl_io = DynamixelIO('COM9', 921600)

motor = dxl_io.new_three_mxl_motor(106)

motor.set_speed_mode()

motor.set_speed(100)

prev = motor.get_pos()

while True:
    time.sleep(1)
    pos = motor.get_pos()
    print(f'Pos: {pos}')
    print(f'Speed: {pos - prev}')
    prev = pos
