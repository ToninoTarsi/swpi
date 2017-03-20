###########################################################################
# Sint Wind PI
# Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#
# Please refer to the LICENSE file for conditions
# Visit http://www.vololiberomontecucco.it
#
##########################################################################


A Sint Wind is a wind condition ( and other meteo data ) telephone answering machine. 
This implementation uses a Raspberry PI with an Huawei 3G dongle. The Sint Wind is compatible with different kind of Meteo Sensors (WH1080, WH3080, Davis, TX32, BMP085...).

Complete documentation on www.vololiberomontecucco.it

**Requirements :**

sudo apt-get -y install python-dev

sudo apt-get -y install python-imaging

sudo apt-get -y install python-serial

sudo apt-get -y install uvccapture

sudo apt-get -y install wvdial

sudo apt-get -y install python-rpi.gpio

sudo apt-get -y install python-smbus

sudo apt-get -y install i2c-tools

sudo apt-get -y remove ntp

sudo apt-get -y install gphoto2  python-piggyphoto dcraw libgphoto2-port10

sudo apt-get -y install python-requests python-spidev python-pygame python-setuptools libusb-1.0-0-dev cmake 

 
  

**USB library:**
- hidapi
- cython-hidapi
- cython


**RTL-SDR libraries** (included)**:**
- cd rtl-sdr
- mkdir build
- cd build
- cmake ../  -DDETACH_KERNEL_DRIVER=ON -DINSTALL_UDEV_RULES=ON
- make
- sudo make install 
 

**RTL_433** (included - just a little modified, see /rtl_433/README-SWPI.md)**:**
- cd rtl_433
- mkdir build
- cd build
- cmake ../
- make
- sudo make install


**Main program start:** sudo python swpi.py


