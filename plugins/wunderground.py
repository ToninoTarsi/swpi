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
        
        ###################### End Initialization ##################
        
        
    def run(self):
        log("Starting plugin : %s" % sys.modules[__name__])
        i=0
        while 1:
        ###################### Plugin run
            time.sleep(60-datetime.datetime.now().second)
            if ( globalvars.meteo_data.status == 0 ):
                logDataToWunderground(self.cfg.WeatherUnderground_ID,self.cfg.WeatherUnderground_password,self.cfg.wind_speed_units)	
                UploadData(self.cfg)
                if ( i % 5 == 0):
                    logData(self.cfg.serverfile,self.cfg.SMSPwd)
            i = i +  1
        ###################### end of Plugin run

