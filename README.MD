# TangoServer for direct communication with Newport Corporation [Picomotor Controller 8742](https://www.newport.com/p/8742)

# Description/purpose
Operation with 8742 open loop controller via USB interface (**libusb+python**). The hardware is used to drive piezo-electrical actuators, mechanical and opto-mechanical components.
I have implemented a simple 1x controller (**Pico8742Ctrl**) - many channel scheme (**Pico8742Channel**).
The 8742 controllers can be stacked into a master/slave configurations. There is no support for slave configurations in this server for now.

This controller supports communication via TCP/IP protocol, however, we experienced issues in a network of complex topology which resulted in an unexpected termination of TCP/IP socket connections.
This Tango Server is installed on a [Raspberry PI](https://www.raspberrypi.org/) and talks directly to the device, thus, is less affected by the network issues.

Typical response times - 1-2ms for a direct USB command at a Windows 7 Core i5 PC. RPi+Tango combination results in 6-20ms response time per a command.

# File structure
**Pico8742.py** - implements the Tango Server and the corresponding Tango Devices **Pico8742Ctrl** and **Pico8742Channel**
**Pico8742.sh** - is a basic bash shell wrapper implementing device connectivity test, Tango Server start-up and it's restart in case of a bug caused failures

# Detailed information on Tango
## Pre-Configuration

## Tango configuration - Pico8742Ctrl
The following commands are implemented:
1. *CommandWriteRead* - transfers raw commands to the device and returns the response
2. *GetIDN* - returns identification string of the device
3. *GetIPAddress* - returns currently assigned IP address
4. *GetMACAddress* - returns MAC address
5. *GetUSBParams* - returns USB parameters - product ID and vendor ID in a human readable form
6. *Reinitialize* - performs an attempt to reinitialize the connection to the device (device reboot and etc.)

The following attributes are implemented:
1. **VersionInformation** - information about firmware version and etc.
2. **ErrorCode** - error code returned by the device (string form)
3. **ResponseTime** - average time of command execution on the device as seen from the Tango Server

## Tango configuration - Pico8742Channel
Individual Tango Devices - channels are configurable via device-class properties.
The following device-class properties are implemented.
- channel (int) - Channel Number
- axisname (str) - Axis Name
Channel Number is used for communication purposes, while the Axis Name is copied as an Tango Attribute for simplicity while working with ATK panels and [jive](http://www.esrf.eu/computing/cs/tango/tango_doc/tools_doc/jive_doc/index.html).

The following attributes are implemented:
1. **Position** - Raw position of the motor at a given channel as is (in steps)
2. **Acceleration** - Acceleration value of the piezo drive (steps/sec^2)
3. **Velocity** - Velocity value of the piezo drive (steps/sec)
4. **MotorType** - Type of the piezo motor as recognized by the controller (0 - no motor, 1 - type unknown, 2 - 'tiny' motor, 3 - 'standard motor')
5. **AxisName** - Axis name indicating purpose of the piezo motor (copy of the corresponding axisname property)
3. **ResponseTime** - Average response time of command execution as seen by Pico8742Channel instance (ms)

# Raspberry Pi and communication via USB
There are many recipes out [there](https://stackoverflow.com/questions/13419691/accessing-a-usb-device-with-libusb-1-0-as-a-non-root-user) explaining configuration.
Long story short - one needs to modify the **udev** rules under linux, create a special user group or use an existing group, assign this group to a user running Tango Server.
```
root# **echo 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="104d", ATTRS{idProduct}=="4000", SYMLINK+="newport", GROUP="usb", MODE="0660"' > /etc/udev/rules.d/99-my-device.rules**
root# **addgroup usb**
root# **usermod -a -G usb username_running_tango**
root# **/sbin/reboot**
```

# Python Dependencies
The following modules have been used:
[PyTango](https://pypi.python.org/pypi/PyTango), [python-libusb1](https://github.com/vpelletier/python-libusb1/tree/master/examples), modded backend of [Ben Hammel](https://github.com/bdhammel/python_newport_controller)

# Licenses
The code of the server and supporting code are distributed under [LGPL v.3](https://www.gnu.org/licenses/lgpl-3.0.de.html).
License [Ben Hammel's](https://github.com/bdhammel/python_newport_controller) should be provided at his page.