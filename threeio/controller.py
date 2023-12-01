################################################################################
# Copyright 2020 University of Georgia Bio-Sensing and Instrumentation Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

# Author: Hunter Halloran (Jyumpp)

from dynamixel_sdk import *
import json
import pkg_resources
from deprecation import deprecated
import threading


class DynamixelIO:
    """Creates communication handler for Dynamixel motors"""

    def __init__(self,
                 device_name='/dev/ttyUSB0',
                 baud_rate=57600):
        if device_name is None:
            return
        self.port_handler = PortHandler(device_name)
        self.packet_handler = [PacketHandler(1), PacketHandler(2)]
        if not self.port_handler.setBaudRate(baud_rate):
            raise (NameError("BaudChangeError"))

        if not self.port_handler.openPort():
            raise (NameError("PortOpenError"))

    def __check_error(self, protocol, dxl_comm_result, dxl_error):
        """Prints the error message when not successful"""
        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % self.packet_handler[protocol - 1].getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print("%s" % self.packet_handler[protocol - 1].getRxPacketError(dxl_error))

    def write_control_table(self, protocol, dxl_id, value, address, size):
        """Writes a specified value to a given address in the control table"""
        dxl_comm_result = 0
        dxl_error = 0

        # the following has to be done inelegantly due to the dynamixel sdk having separate functions per packet size.
        # future versions of this library may replace usage of the dynamixel sdk to increase efficiency and remove this
        # bulky situation.
        if size == 1:
            dxl_comm_result, dxl_error = self.packet_handler[protocol - 1].write1ByteTxRx(self.port_handler, dxl_id,
                                                                                          address, value)
        elif size == 2:
            dxl_comm_result, dxl_error = self.packet_handler[protocol - 1].write2ByteTxRx(self.port_handler, dxl_id,
                                                                                          address, value)
        elif size == 4:
            dxl_comm_result, dxl_error = self.packet_handler[protocol - 1].write4ByteTxRx(self.port_handler, dxl_id,
                                                                                          address, value)
        self.__check_error(protocol, dxl_comm_result, dxl_error)

    def read_control_table(self, protocol, dxl_id, address, size):
        """Returns the held value from a given address in the control table"""
        ret_val = 0
        dxl_comm_result = 0
        dxl_error = 0

        # the following has to be done inelegantly due to the dynamixel sdk having separate functions per packet size.
        # future versions of this library may replace usage of the dynamixel sdk to increase efficiency and remove this
        # bulky situation.
        if size == 1:
            ret_val, dxl_comm_result, dxl_error = self.packet_handler[protocol - 1].read1ByteTxRx(self.port_handler,
                                                                                                  dxl_id, address)
        elif size == 2:
            ret_val, dxl_comm_result, dxl_error = self.packet_handler[protocol - 1].read2ByteTxRx(self.port_handler,
                                                                                                  dxl_id, address)
        elif size == 4:
            ret_val, dxl_comm_result, dxl_error = self.packet_handler[protocol - 1].read4ByteTxRx(self.port_handler,
                                                                                                  dxl_id, address)
        self.__check_error(protocol, dxl_comm_result, dxl_error)
        return ret_val

    def new_3mxl_motor(self, dxl_id):
        """Returns a new ThreeMxlMotor object of a given protocol with a given control table"""
        return ThreeMxlMotor(dxl_id, self,
                             pkg_resources.resource_filename(__name__, "control_table.json"))

class ThreeMxlMotor:
    """Creates the basis of individual motor objects"""

    def __init__(self, dxl_id, dxl_io, json_file):
        """Initializes a new DynamixelMotor object"""
        # loads the JSON config file and gathers the appropriate control table.
        fd = open(json_file)
        config = json.load(fd)
        fd.close()
        config = config.get("Protocol_1")

        # sets the motor object values based on inputs or JSON options.
        self.CONTROL_TABLE_PROTOCOL = 1
        self.dxl_id = dxl_id
        self.dxl_io = dxl_io
        self.PROTOCOL = 1
        self.CONTROL_TABLE = config.get("Control_Table")

    def write_control_table(self, data_name, value):
        """Writes a value to a control table area of a specific name"""
        self.dxl_io.write_control_table(self.PROTOCOL, self.dxl_id, value, self.CONTROL_TABLE.get(data_name)[0],
                                        self.CONTROL_TABLE.get(data_name)[1])

    def read_control_table(self, data_name):
        """Reads the value from a control table area of a specific name"""
        return self.dxl_io.read_control_table(self.PROTOCOL, self.dxl_id, self.CONTROL_TABLE.get(data_name)[0],
                                              self.CONTROL_TABLE.get(data_name)[1])

    def send_heartbeat(self):
        """Method to send a heartbeat every second."""
        while True:
            self.write_control_table("NO_INSTRUCTION", 1)
            time.sleep(1)

    def start_heartbeat(self):
        """Starts the heartbeat thread."""
        heartbeat_thread = threading.Thread(target=self.send_heartbeat)
        heartbeat_thread.daemon = True  # This ensures that the thread will close when the main program exits
        heartbeat_thread.start()

    # -- SET COMMANDS --

    def set_velocity_mode(self):
        self.write_control_table("M3XL_CONTROL_MODE", 1)

    def set_position_mode(self):
        self.write_control_table("M3XL_CONTROL_MODE", 0)

    def set_current_mode(self):
        self.write_control_table("M3XL_CONTROL_MODE", 2)

    def set_torque_mode(self):
        self.write_control_table("M3XL_CONTROL_MODE", 3)

    def set_sea_mode(self):
        # To be honest, I have no idea what this mode does.
        self.write_control_table("M3XL_CONTROL_MODE", 4)

    def set_stop_mode(self):
        self.write_control_table("M3XL_CONTROL_MODE", 12)

    def set_start_up_mode(self):
        self.write_control_table("M3XL_CONTROL_MODE", 15)

    def set_sinusoidal_position_mode(self):
        self.write_control_table("M3XL_CONTROL_MODE", 16)

    def set_test_mode(self):
        self.write_control_table("M3XL_CONTROL_MODE", 17)

    def set_pwm_mode(self):
        self.write_control_table("M3XL_CONTROL_MODE", 5)

    def set_velocity(self, velocity):
        self.write_control_table("M3XL_DESIRED_SPEED", velocity * 100)

    def set_velocity_linear(self, velocity):
        self.write_control_table("M3XL_DESIRED_LINEAR_SPEED", velocity * 100)

    def set_acceleration(self, acceleration):
        self.write_control_table("M3XL_DESIRED_ACCEL", acceleration)

    def set_acceleration_linear(self, acceleration):
        self.write_control_table("M3XL_DESIRED_LINEAR_ACCEL", acceleration)

    def set_position(self, position):
        self.write_control_table("M3XL_DESIRED_POSITION_32", position)

    def set_angle(self, angle):
        self.write_control_table("M3XL_DESIRED_ANGLE", angle)

    def set_current(self, current):
        self.write_control_table("M3XL_DESIRED_CURRENT", current)

    def set_p_current(self, current):
        self.write_control_table("M3XL_P_CURRENT", current)

    def set_i_current(self, current):
        self.write_control_table("M3XL_I_CURRENT", current)

    def set_d_current(self, current):
        self.write_control_table("M3XL_D_CURRENT", current)

    def set_il_current(self, current):
        self.write_control_table("M3XL_IL_CURRENT", current)

    # -- GET COMMANDS --

    def get_voltage(self):
        return self.read_control_table("M3XL_VOLTAGE")

    def get_current(self):
        return self.read_control_table("M3XL_CURRENT")

    def get_p_current(self):
        return self.read_control_table("M3XL_P_CURRENT")

    def get_i_current(self):
        return self.read_control_table("M3XL_I_CURRENT")

    def get_d_current(self):
        return self.read_control_table("M3XL_D_CURRENT")

    def get_il_current(self):
        return self.read_control_table("M3XL_IL_CURRENT")

    def get_torque(self):
        return self.read_control_table("M3XL_TORQUE")

    def get_angle(self):
        return self.read_control_table("M3XL_ANGLE")

    def get_angular_rate(self):
        return self.read_control_table("M3XL_ANGULAR_RATE")

    def get_position(self):
        return self.read_control_table("M3XL_POSITION_32")

    def get_velocity(self):
        return self.read_control_table("M3XL_SPEED")
