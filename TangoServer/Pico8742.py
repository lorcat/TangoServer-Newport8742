__author__ = "Konstantin Glazyrin"

"""
Tango Server for Newport PicoMotor 8742 Open Loop controller (single controller, no master/slave relations)
Code based on https://github.com/bdhammel/python_newport_controller
Code exploits libusb capability for direct communication with the device.

All positions are considered to be relative, raw (steps). Calibration can implemented separately.

Code exports Pico8742Ctrl (controller), Pico8742Channel (individual channel)

License: LGPL v.3 for the code of Tango Server itself, for  licenses of the libraries:
please see the corresponding references
"""

import re
import time

from app import *

# global variables
PCTRL = None

class Pico8742Ctrl(CommonDevice):
    __metaclass__ = DeviceMeta

    ErrorCode = attribute(label="Error Code", dtype=str,
                       fget="get_errcode",
                       doc="")

    ResponseTime = attribute(label="Response Time", dtype=str,
                             fget="get_response_time", unit="ms",
                             doc="")

    VersionInformation = attribute(label="Version Information", dtype=str,
                    fget="get_ve",
                    doc="Information string of the device")

    # Class Specific Info - could go to Class or Device property
    ID_PRODUCT = '0x4000'
    ID_VENDOR = '0x104d'

    def __init__(self, *args, **kwargs):
        """
        Initialization of the device. Creating global controller handle
        :param args:
        :param kwargs:
        """
        CommonDevice.__init__(self, *args, **kwargs)

        global PCTRL
        PCTRL = self

    # COMMANDs
    # firmware
    VE = "VE"
    # error code
    TB = "TB"

    def init_device(self, *args, **kwargs):
        """
        Initialization of intrinsic variables
        :param args:
        :param kwargs:
        :return:
        """
        # statistics - average command execution time
        self.total_commands = 0
        self.total_time = 0

        # initialization of the controller
        self.ctrl = None
        try:
            self.init_usb_controller()
        except ValueError:
            # device does not exist - return default values
            pass

        self.set_state(DevState.ON)

    def get_ve(self):
        return self.get_cmd(cmd=self.VE)

    def get_errcode(self):
        return self.get_cmd(cmd=self.TB)

    def get_response_time(self):
        """
        Returns average time for the individual command execution
        :return:
        """
        res = -1.
        if self.total_commands > 0:
            res = float(self.total_time)/self.total_commands

        res = "{:4.2f}".format(res)
        return res

    @PyTango.DebugIt()
    @PyTango.ErrorIt()
    def get_cmd(self, cmd="PA", ch=None, cmd_type=float):
        """
        Basic function processing data polling and device response
        :param ch:
        :return:
        """
        base_cmd = "{}{}?".format(ch, cmd)
        if ch is None:
            base_cmd = "{}?".format(cmd)

        self.debug("\nBase Command is: ({})".format(base_cmd))

        base_cmd += '\r'

        # default value handling
        value = None
        if cmd_type is float:
            value = -1.
        elif cmd_type is int:
            value = -1
        elif cmd_type is str or cmd_type is unicode:
            value = "Error - controller is offline"

        # getting raw response
        if self.test_controller() and self.test_connection():
            # work with a timestamp
            time_start = time.time()

            response = self.ctrl.command(base_cmd).strip()

            # timestamp
            time_stop = time.time()

            dt = (time_stop-time_start)*1000.
            self.total_commands += 1
            self.total_time += dt

            self.debug("Response took ({}ms, average time {}ms): ({}/{})".format(dt,
                                                                                   float(self.total_time)/self.total_commands,
                                                                                   response,
                                                                                   type(response)))
            # response contains channel number
            patt = re.compile("([0-9])>([^>\r\n]*)")

            match_ch = patt.match(response)
            if match_ch:
                ch, response = match_ch.groups()
                self.debug("Channel {}: {}".format(ch, response))

                try:
                    value = cmd_type(response)
                except ValueError:
                    # using default values
                    pass

                self.debug("Value is: ({}/{})".format(value, type(value)))

            elif isinstance(response, str) or isinstance(response, unicode):
                value = response.strip()
            else:
                msg = "Could not parse value ({}/{})".format(response, cmd_type)
                self.error(msg)
                raise DevFailed, msg

        self.debug("Final value: ({})".format(value))
        return value

    def init_usb_controller(self):
        if self.ctrl is not None:
            ctrl = self.ctrl
            del ctrl
            self.ctrl = None
        self.ctrl = Controller(idProduct=int(self.ID_PRODUCT, 16), idVendor=int(self.ID_VENDOR, 16), logger=self)

    @PyTango.ErrorIt()
    @PyTango.DebugIt()
    def set_cmd(self, value, cmd="PA", ch=None):
        """
        Basic function processing data polling and device response
        :param ch:
        :return:
        """
        if not self.test_controller():
            self.error("Controller is offline")
            return

        base_cmd = "{}{}{}".format(ch, cmd, int(value))
        self.debug("\n\nBase Set Command is: ({})".format(base_cmd))
        base_cmd += '\r'

        # getting raw response
        self.ctrl.command(base_cmd)

    def test_controller(self):
        res = True
        if self.ctrl is None:
            res = False
        return res

    @PyTango.DebugIt()
    def test_connection(self):
        """
        Tests connection if not, then returs false
        :return:
        """
        res = True

        cfg = str(self.ctrl.dev.get_active_configuration())
        p = re.compile("(iInterface.*[^0-9\n]*)", re.IGNORECASE | re.MULTILINE)

        test_conn = "".join(p.findall(cfg)).lower()

        self.debug("Testing error state: \n{}\n{}".format(test_conn, "error" in test_conn))

        if "error" in test_conn:
            self.set_state(DevState.FAULT)
            self.ctrl = None
        else:
            self.set_state(DevState.ON)

        return res

    @command(dtype_out=str, dtype_in=str)
    def CommandWriteRead(self, value):
        """
        Function responsible for raw command exchange with the device
        :param value:
        :return:
        """
        value = value.replace("?", "")
        return '{}'.format(self.get_cmd(cmd=value))

    @command(dtype_out=str)
    def GetIDN(self):
        """
        Command responsible for IDN enquiry
        :param value:
        :return:
        """
        return '{}'.format(self.get_cmd(cmd="*IDN"))

    @command(dtype_out=str)
    def GetIPAddress(self):
        """
        Command responsible for IP address enquiry
        :param value:
        :return:
        """
        return 'IPADDRESS: {}'.format(self.get_cmd(cmd="IPADDR"))

    @command(dtype_out=str)
    def GetMACAddress(self):
        """
        Command responsible for MAC address enquiry
        :param value:
        :return:
        """
        return 'MACADDRESS: {}'.format(self.get_cmd(cmd="MACADDR"))

    @command(dtype_out=str)
    def GedUSBParams(self):
        """
        Returns average time for the individual command execution
        :return:
        """
        return "Product ID {}; Vendor ID {};".format(self.ID_PRODUCT, self.ID_VENDOR)

    @command()
    def Reinitialize(self):
        """
        An attempt to reinitialize controller
        :param value:
        :return:
        """
        self.init_usb_controller()
        self.test_connection()

class Pico8742Channel(CommonDevice):
    __metaclass__ = DeviceMeta

    # Attributes
    # raw position of the piezo drive
    Position = attribute(label="Position", dtype=float,
                    fget="get_position", fset="set_position",
                    doc="Raw position of the piezo drive")

    # Acceleration of the piezo drive
    Acceleration = attribute(label="Acceleration", dtype=float,
                         fget="get_acceleration", fset="set_acceleration",
                         doc="Acceleration value of the piezo drive", unit="steps/sec^2")

    # Acceleration of the piezo drive
    Velocity = attribute(label="Velocity", dtype=float,
                             fget="get_velocity", fset="set_velocity",
                             doc="Velocity value of the piezo drive", unit="steps/sec")

    # Channel address of the current device
    ChannelAddress = attribute(label="Channel Address", dtype=int,
                         fget="get_chaddr",
                         doc="Channel address of the current device")

    # Motor type of the connected device
    MotorType = attribute(label="Motor Type", dtype=int,
                               fget="get_motor_type",
                               doc="Returns motor type (0 - no motor, 1 - type unknown, 2 - 'tiny' motor, 3 - 'standard motor')")

    # average response time of command execution
    AxisName = attribute(label="Axis Name", dtype=str,
                             fget="get_axis_name",
                             doc="Axis name indicating purpose of the axis")

    # average response time of command execution
    ResponseTime = attribute(label="Response Time", dtype=str,
                          fget="get_response_time", unit="ms",
                          doc="Average response time of command execution")

    # average response time of command execution
    UnitLimitMin = attribute(label="Position minimum (dummy)", dtype=float,
                             fget="get_userlim_min",
                             doc="Minimal position limit (user level)")

    UnitLimitMax = attribute(label="Position maximum (dummy)", dtype=float,
                             fget="get_userlim_max",
                             doc="Maximal position limit (user level)")

    # device property - channel number
    channel = device_property(dtype=int, default_value=1,  update_db=True)
    axisname = device_property(dtype=str, default_value="channel0", update_db=True)

    # COMMANDs
    # get position
    TP = "TP"
    # set position
    PA = "PA"
    # acceleration
    AC = "AC"
    # velocity
    VA = "VA"
    # motor type
    QM = "QM"
    # Motor state
    MD = "MD"

    def __init__(self, *args, **kwargs):
        CommonDevice.__init__(self, *args, **kwargs)

    def init_device(self, *args, **kwargs):
        """
        Initializes device, sets device channel from device property
        """
        self.get_device_properties()
        self.chnum = self.channel
        self.axsname = self.axisname

        self.total_commands = 0
        self.total_time = 0

    def get_chaddr(self):
        """
            Returns address of the channel as given by property
            :return:
        """
        return self.chnum

    def get_position(self):
        """
            Returns position for a given channel
            :return:
        """
        return self.get_cmd(ch=self.chnum, cmd=self.TP)

    def set_position(self, value):
        """
            Sets position for a given channel
            :return:
        """
        self.set_cmd(value, cmd=self.PA)

    def get_acceleration(self):
        """
            Returns position for a given channel
            :return:
        """
        return self.get_cmd(ch=self.chnum, cmd=self.AC)

    def set_acceleration(self, value):
        """
            Sets acceleration for a given channel
            :return:
        """
        self.set_cmd(value, cmd=self.AC)

    def get_velocity(self):
        """
            Returns position for a given channel
            :return:
        """
        return self.get_cmd(ch=self.chnum, cmd=self.VA)

    def set_velocity(self, value):
        """
            Sets acceleration for a given channel
            :return:
        """
        self.set_cmd(value, cmd=self.VA)

    def set_cmd(self, value, cmd=None):
        """
            Sets value for a given channel and a command
            :return:
        """
        if cmd is None:
            self.error("Command is not defined")
            return

        global PCTRL

        self.debug("Controller is ({})".format(PCTRL))

        if PCTRL is not None and PCTRL.test_controller():
            time_start = time.time()

            PCTRL.set_cmd(value, ch=self.chnum, cmd=cmd)

            time_stop = time.time()

            dt = (time_stop - time_start) * 1000.
            self.total_commands += 1
            self.total_time += dt

            # self.set_state(DevState.ON)
        else:
            self.set_state(DevState.FAULT)

    def get_motor_type(self):
        """
            Returns position for a given channel
            :return:
        """
        return self.get_cmd(ch=self.chnum, cmd=self.QM)

    def get_cmd(self, cmd=None, ch=None, cmd_type=float):
        """
        General function obtaining values for different commands
        :param cmd:
        :param ch:
        :param cmd_type:
        :return:
        """
        if cmd is None:
            self.error("Command is not defined")
            return

        global PCTRL

        # default values
        value = None
        if cmd_type is float:
            value = -1.
        elif cmd_type is int:
            value = -1
        else:
            value = "Error - controller is offline"

        self.debug("Default value is ({})".format(value))
        self.debug("Controller is ({})".format(PCTRL))

        if PCTRL is not None and PCTRL.test_controller():
            time_start = time.time()

            value = PCTRL.get_cmd(ch=ch, cmd=cmd, cmd_type=cmd_type)

            time_stop = time.time()

            dt = (time_stop - time_start) * 1000.
            self.total_commands += 1
            self.total_time += dt

            # self.set_state(DevState.ON)
        else:
            self.set_state(DevState.FAULT)

        return value

    def get_response_time(self):
        """
        Returns average time for the individual command execution
        :return:
        """
        res = -1.
        if self.total_commands > 0:
            res = float(self.total_time)/self.total_commands

        res = "{:4.2f}".format(res)
        return res

    def get_axis_name(self):
        """
        Returns axis name indicating purpose of the channel - value corresponds to the axis name property
        In a case no property was set - value is set to empty string
        :return:
        """
        res = ""
        if self.axsname is not None:
            res = "{}".format(self.axsname)
        return res

    def get_userlim_min(self):
        """
        DUMMY
        :return:
        """
        res = float(-10E6)
        return res

    def get_userlim_max(self):
        """
        DUMMY
        :return:
        """
        res = float(10E6)
        return res

    def dev_state(self):
        """
        Obtains state of the motor and returns it
        :return:
        """
        res = DevState.ON
        temp = self.get_cmd(ch=self.chnum, cmd=self.MD)
        if temp == 0:
            res = DevState.MOVING
        return res

if __name__ == "__main__":
        server_run((Pico8742Ctrl, Pico8742Channel))
