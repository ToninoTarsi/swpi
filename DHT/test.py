#!/usr/bin/python

import subprocess
import re
import sys
import time
import datetime
from ctypes import *


#libDHT = cdll.LoadLibrary('./libDHT.so')
#
#while 1:
#    print "reading .."
#    Temp = c_float()
#    Hum = c_float()
#
#    print libDHT.read(Temp,Hum)
#    
#    print "Temp" , Temp
#    print "Hum",Hum
#    time.sleep(2)
#    
#
#
#exit(0)


# Continuously append data
while(True):
    # Run the DHT program to get the humidity and temperature readings!
    
    output = subprocess.check_output(["./DHT"]);
    #print output
    matches = re.search("Temp =\s+([0-9.]+)", output)
    if (not matches):
        print "nomatches tep"
        time.sleep(3)
        continue
    temp = float(matches.group(1))
    
    # search for humidity printout
    matches = re.search("Hum =\s+([0-9.]+)", output)
    if (not matches):
        print "nomatches um"
        time.sleep(3)
        continue
    humidity = float(matches.group(1))
    
    print "Temperature: %.1f C Humidity:    %.1f " % (temp , humidity)
    
    time.sleep(1)
