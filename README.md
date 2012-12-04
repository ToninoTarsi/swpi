###########################################################################
# Sint Wind PI
# Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#
# Please refer to the LICENSE file for conditions
# Visit http://www.vololiberomontecucco.it
#
##########################################################################


A Sint Wind is a wind condition ( and other meteo data ) telephone answering machine. 
This implementation uses a Raspberry PI with an Huawei 3G dongle. The Sint Wind is compatible from different kind of Meteo Sensors ( WH1080,Davis,TX32,BMP085 .. ).

Complete documentation on www.vololiberomontecucco.it

Requirements :

sudo apt-get -y install python-dev

sudo apt-get -y install python-imaging

sudo apt-get -y install python-serial

sudo apt-get -y install uvccapture

sudo apt-get -y install wvdial

sudo apt-get -y install python-rpi.gpio

sudo apt-get -y install python-smbus

sudo apt-get -y install i2c-tools

sudo apt-get -y remove ntp

sudo apt-get -y install gphoto2

USB library: 
•	hidapi
•	cython-hidapi
•	cython


Main program : sudo python swpi.py