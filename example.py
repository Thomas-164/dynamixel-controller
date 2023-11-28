import time
from dynio.dynamixel_controller import DynamixelIO

dxl_io = DynamixelIO('COM3', 921600)

motor = dxl_io.new_three_mxl_motor(106)

while True:
    command = input("> ")
    # Catch up arrow key
    if command == '':
        continue
    if command == 'quit':
        break
    command, arg = command.split(' ')
    motor.write_control_table(command, int(arg))

# motor.set_speed_mode()

# motor.set_speed(1)

# prev = motor.get_pos()

# while True:
#    time.sleep(1)
#    pos = motor.get_pos()
#    print(f'Pos: {pos}')
#    print(f'Speed: {pos - prev}')
#    prev = pos
