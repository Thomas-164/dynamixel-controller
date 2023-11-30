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

    def new_motor(self, dxl_id, json_file, protocol=2, control_table_protocol=None):
        """Returns a new DynamixelMotor object of a given protocol with a given control table"""
        return DynamixelMotor(dxl_id, self, json_file, protocol, control_table_protocol)

    def new_3mxl_motor(self, dxl_id):
        """Returns a new ThreeMxlMotor object of a given protocol with a given control table"""
        return ThreeMxlMotor(dxl_id, self,
                             pkg_resources.resource_filename(__name__, "DynamixelJSON/3mxl.json"))

    def new_ax12(self, dxl_id):
        """Returns a new DynamixelMotor object for an AX12"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/AX12.json"))

    def new_mx12(self, dxl_id):
        """Returns a new DynamixelMotor object for an MX12"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/MX12.json"))

    def new_mx28(self, dxl_id, protocol=1, control_table_protocol=None):
        """Returns a new DynamixelMotor object for an MX28"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/MX28.json"),
                              protocol=protocol, control_table_protocol=control_table_protocol)

    def new_mx64(self, dxl_id, protocol=1, control_table_protocol=None):
        """Returns a new DynamixelMotor object for an MX64"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/MX64.json"),
                              protocol=protocol, control_table_protocol=control_table_protocol)

    def new_mx106(self, dxl_id, protocol=1, control_table_protocol=None):
        """Returns a new DynamixelMotor object for an MX106"""
        return DynamixelMotor(dxl_id, self,
                              pkg_resources.resource_filename(__name__, "DynamixelJSON/MX106.json"),
                              protocol=protocol, control_table_protocol=control_table_protocol)


class DynamixelMotor:
    """Creates the basis of individual motor objects"""

    def __init__(self, dxl_id, dxl_io, json_file, protocol=1, control_table_protocol=None):
        """Initializes a new DynamixelMotor object"""

        # protocol 2 series motors can run using protocol 1, but still use the new control table.
        # this sets the control table choice to the default if one is not explicitly requested.
        if protocol == 1 or control_table_protocol is None:
            control_table_protocol = protocol

        # loads the JSON config file and gathers the appropriate control table.
        fd = open(json_file)
        config = json.load(fd)
        fd.close()
        if control_table_protocol == 1:
            config = config.get("Protocol_1")
        else:
            config = config.get("Protocol_2")

        # sets the motor object values based on inputs or JSON options.
        self.CONTROL_TABLE_PROTOCOL = control_table_protocol
        self.dxl_id = dxl_id
        self.dxl_io = dxl_io
        self.PROTOCOL = protocol
        self.CONTROL_TABLE = config.get("Control_Table")
        self.min_position = config.get("Values").get("Min_Position")
        self.max_position = config.get("Values").get("Max_Position")
        self.max_angle = config.get("Values").get("Max_Angle")

    def write_control_table(self, data_name, value):
        """Writes a value to a control table area of a specific name"""
        self.dxl_io.write_control_table(self.PROTOCOL, self.dxl_id, value, self.CONTROL_TABLE.get(data_name)[0],
                                        self.CONTROL_TABLE.get(data_name)[1])

    def read_control_table(self, data_name):
        """Reads the value from a control table area of a specific name"""
        return self.dxl_io.read_control_table(self.PROTOCOL, self.dxl_id, self.CONTROL_TABLE.get(data_name)[0],
                                              self.CONTROL_TABLE.get(data_name)[1])

    def set_velocity_mode(self, goal_current=None):
        """Sets the motor to run in velocity (wheel) mode and sets the goal current if provided"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            # protocol 1 sets velocity mode by setting both angle limits to 0.
            self.write_control_table("CW_Angle_Limit", 0)
            self.write_control_table("CCW_Angle_Limit", 0)
            if goal_current is not None:
                # protocol 1 calls goal current Max Torque rather than Goal Current.
                self.write_control_table("Max_Torque", goal_current)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            # protocol 2 has a specific register for operating mode.
            self.write_control_table("Operating_Mode", 1)
            if goal_current is not None:
                self.write_control_table("Goal_Current", goal_current)

    def set_position_mode(self, min_limit=None, max_limit=None, goal_current=None):
        """Sets the motor to run in position (joint) mode and sets the goal current if provided.
        If position limits are not specified, the full range of motion is used instead"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            # protocol 1 sets position mode by having different values for min and max position.
            if min_limit is None or max_limit is None:
                min_limit = self.min_position
                max_limit = self.max_position
            self.write_control_table("CW_Angle_Limit", min_limit)
            self.write_control_table("CCW_Angle_Limit", max_limit)
            if goal_current is not None:
                # protocol 1 calls goal current Max Torque rather than Goal Current.
                self.write_control_table("Max_Torque", goal_current)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            # protocol 2 has a specific register for operating mode.
            self.write_control_table("Operating_Mode", 3)
            if min_limit is not None:
                self.write_control_table("Min_Position_Limit", min_limit)
            if max_limit is not None:
                self.write_control_table("Max_Position_Limit", max_limit)
            if goal_current is not None:
                self.write_control_table("Goal_Current", goal_current)

    def set_extended_position_mode(self, goal_current=None):
        """Sets the motor to run in extended position (multi-turn) mode"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            # protocol 1 sets multi turn mode by setting both angle limits to max value.
            self.write_control_table("CW_Angle_Limit", self.max_position)
            self.write_control_table("CCW_Angle_Limit", self.max_position)
            if goal_current is not None:
                # protocol 1 calls goal current Max Torque rather than Goal Current.
                self.write_control_table("Max_Torque", goal_current)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            # protocol 2 has a specific register for operating mode.
            self.write_control_table("Operating_Mode", 4)
            if goal_current is not None:
                self.write_control_table("Goal_Current", goal_current)

    def set_velocity(self, velocity):
        """Sets the goal velocity of the motor"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            # protocol 1 uses 1's compliment rather than 2's compliment for negative numbers.
            if velocity < 0:
                velocity = abs(velocity)
                velocity += 1024
            self.write_control_table("Moving_Speed", velocity)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            if self.read_control_table("Operating_Mode") == 1:
                self.write_control_table("Goal_Velocity", velocity)
            else:
                self.write_control_table("Profile_Velocity", velocity)

    def set_acceleration(self, acceleration):
        """Sets the goal acceleration of the motor"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            self.write_control_table("Goal_Acceleration", acceleration)
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            self.write_control_table("Profile_Acceleration", acceleration)

    def set_position(self, position):
        """Sets the goal position of the motor"""
        self.write_control_table("Goal_Position", position)

    def set_angle(self, angle):
        """Sets the goal position of the motor with a given angle in degrees"""
        self.set_position(
            # formula for mapping the range from min to max angle to min to max position.
            int(((angle / self.max_angle) * ((self.max_position + 1) - self.min_position)) + self.min_position))

    def get_position(self):
        """Returns the motor position"""
        return self.read_control_table("Present_Position")

    def get_angle(self):
        """Returns the motor position as an angle in degrees"""
        return ((self.get_position() - self.min_position) / (
                (self.max_position + 1) - self.min_position)) * self.max_angle

    def get_current(self):
        """Returns the current motor load"""
        if self.CONTROL_TABLE_PROTOCOL == 1:
            current = self.read_control_table("Present_Load")
            if current < 0:
                return -1
            if current > 1023:
                # protocol 1 uses 1's compliment rather than 2's compliment for negative numbers.
                current -= 1023
                current *= -1
            return current
        elif self.CONTROL_TABLE_PROTOCOL == 2:
            return self.read_control_table("Present_Current")

    def torque_enable(self):
        """Enables motor torque"""
        self.write_control_table("Torque_Enable", 1)

    def torque_disable(self):
        """Disables motor torque"""
        self.write_control_table("Torque_Enable", 0)


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
