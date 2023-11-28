# dynamixel-controller

This is a fork of [dynamixel-controller](https://github.com/UGA-BSAIL/dynamixel-controller). It is modified to be able to work with the 3MxlMotor controller.

## Usage
### Example:
```python
from dynio.dynamixel_controller import DynamixelIO

dxl_io = DynamixelIO('portname', 921600) # your port name for the usb

motor = dxl_io.new_three_mxl_motor(id) # id of the motor

motor.set_speed_mode()

motor.set_speed(100)
```

## License
[Apache 2.0](https://choosealicense.com/licenses/apache-2.0/)
