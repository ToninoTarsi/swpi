###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     USB comunication based pywws by 'Jim Easterbrook' <jim@jim-easterbrook.me.uk>
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""example plugin."""

import threading
import random
import datetime
import sqlite3
import sys
import subprocess
import sys 
import os
import thread
import time

import globalvars
import meteodata
from TTLib import  *
import RPi.GPIO as GPIO



class swpi_plugin(threading.Thread):  #  do not change the name of the class
    
    def __init__(self,cfg):
        self.cfg = cfg
        threading.Thread.__init__(self)
        

        ###################### Plugin Initialization ################
        log("Intitializing plug-in %s" % sys.modules[__name__])
#        GPIO.setmode(GPIO.BCM)
#        GPIO.setwarnings(False)
#        GPIO.setup(4, GPIO.OUT)   
#        GPIO.output(4, 0)
        ###################### End Initialization ##################
        
        
    def run(self):
        log("Starting plugin : %s" % sys.modules[__name__])
   
        while 1:
            ###################### Plugin run
            log("Running plug-in %s" % sys.modules[__name__])
#            if globalvars.meteo_data.wind_ave > 15: 
#                GPIO.output(4, 1)
#            else:
#                GPIO.output(4, 0)
            ###################### end of Plugin run
            
            time.sleep(300)


