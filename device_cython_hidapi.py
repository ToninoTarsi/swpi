# pywws - Python software for USB Wireless Weather Stations
# http://github.com/jim-easterbrook/pywws
# Copyright (C) 2008-12  Jim Easterbrook  jim@jim-easterbrook.me.uk

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""Low level USB interface to weather station, using cython-hidapi.

Introduction
============

This module handles low level communication with the weather station
via the `cython-hidapi <https://github.com/gbishop/cython-hidapi>`_
library. An alternative module, :doc:`pywws.device_pyusb`, uses the
`PyUSB <http://sourceforge.net/apps/trac/pyusb/>`_ library. The choice
of which module to use depends on which libraries are available for
you computer.

Users of recent versions of Mac OS have no choice. The operating
system makes it very difficult to access HID devices (such as the
weather station) directly, so the ``hidapi`` library has to be used.
``cython-hidapi`` is a Python interface to that library.

Users of OpenWRT and similar embedded Linux platforms will probably
not be able to install ``cython-hidapi``, so are constrained to use
``libusb`` and its ``PyUSB`` Python interface.

Installation
============

Some of this software may already be installed on your machine, so do
check before downloading sources and compiling them yourself.

#.  Install hidapi.

    Create a local copy of the git repository, change to the new
    directory and then follow the instructions in ``README.txt``::

        git clone https://github.com/signal11/hidapi.git
        cd hidapi
        more README.txt

#.  Install cython.

    This should be available as a package for your operating system.
    For example::
        sudo apt-get install cython

#.  Install cython-hidapi.

    This also needs to be downloaded and built::

        git clone https://github.com/gbishop/cython-hidapi.git
        cd cython-hidapi
        python setup.py build
        sudo python setup.py install

    Replace ``setup.py`` with ``setup-mac.py`` or ``setup-windows.py``
    if you are using Mac OS or Windows.

Testing
=======

Run ``TestWeatherStation.py`` with increased verbosity so it reports
which USB device access module is being used::

    python TestWeatherStation.py -vv
    18:10:27:pywws.WeatherStation.CUSBDrive:using pywws.device_cython_hidapi
    0000 55 aa ff ff ff ff ff ff ff ff ff ff ff ff ff ff 05 20 01 51 11 00 00 00 81 00 00 07 01 00 d0 56
    0020 61 1c 61 1c 00 00 00 00 00 00 00 12 02 14 18 09 41 23 c8 00 32 80 47 2d 2c 01 2c 81 5e 01 1e 80
    0040 a0 00 c8 80 a0 28 80 25 a0 28 80 25 03 36 00 05 6b 00 00 0a 00 f4 01 18 00 00 00 00 00 00 00 00
    0060 00 00 54 1c 63 0a 2f 01 71 00 7a 01 59 80 7a 01 59 80 e4 00 f5 ff 69 54 00 00 fe ff 00 00 b3 01
    0080 0c 02 d0 ff d3 ff 5a 24 d2 24 dc 17 00 11 09 06 15 40 10 03 07 22 18 10 08 11 08 30 11 03 07 12
    00a0 36 08 07 24 17 17 11 02 28 10 10 09 06 30 14 29 12 02 11 06 57 09 06 30 14 29 12 02 11 06 57 08
    00c0 08 31 14 30 12 02 14 18 04 12 02 01 10 12 11 09 13 17 19 11 08 21 16 53 11 09 13 17 19 12 01 18
    00e0 07 17 10 02 22 11 06 11 11 06 13 12 11 11 06 13 12 11 11 10 11 38 11 11 10 11 38 10 02 22 14 43

API
===

"""

__docformat__ = "restructuredtext en"

import hid

class USBDevice(object):
    def __init__(self, idVendor, idProduct):
        """Low level USB device access via cython-hidapi library.

        :param idVendor: the USB ``vendor ID` number, for example 0x1941.

        :type idVendor: int

        :param idProduct: the USB ``product ID` number, for example 0x8021.

        :type idProduct: int

        """
        self.hid = hid.device(idVendor, idProduct)
        if not self.hid:
            raise IOError("Weather station device not found")

    def read_data(self, size):
        """Receive data from the device.

        If the read fails for any reason, an :obj:`IOError` exception
        is raised.

        :param size: the number of bytes to read.

        :type size: int

        :return: the data received.

        :rtype: list(int)

        """
        result = list()
        while size > 0:
            count = min(size, 8)
            buf = self.hid.read(count)
            if len(buf) < count:
                raise IOError('pywws.device_cython_hidapi.USBDevice.read_data failed')
            result += buf
            size -= count
        return result

    def write_data(self, buf):
        """Send data to the device.

        :param buf: the data to send.

        :type buf: list(int)

        :return: success status.

        :rtype: bool

        """
        return self.hid.write(buf)
