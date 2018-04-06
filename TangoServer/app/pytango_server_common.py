__author__="Konstantin Glazyrin"
import PyTango
from PyTango import AttrQuality, AttrWriteType, DispLevel, DevFailed, DevState
from PyTango.server import Device, DeviceMeta, attribute, command, server_run
from PyTango.server import device_property

class CommonDevice(Device):

    PRINT_ENABLE = False

    def __init__(self, *args, **kwargs):
        Device.__init__(self, *args, **kwargs)

    def enable_print(self, value=True):
        self.PRINT_ENABLE = value

    def reprint(self, header="", msg=""):
        if self.PRINT_ENABLE:
            print("{} : {}".format(header, msg))

    def info(self, msg):
        self.info_stream(msg)
        self.reprint("INFO", msg)

    def error(self, msg):
        self.error_stream(msg)
        self.reprint("ERROR", msg)

    def warning(self, msg):
        self.warn_stream(msg)
        self.reprint("WARNING", msg)

    def debug(self, msg):
        self.debug_stream(msg)
        self.reprint("DEBUG", msg)