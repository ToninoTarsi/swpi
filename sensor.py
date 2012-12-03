
###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""This module defines the base sensors wh1080 ."""


import threading
import time
import config
import random
import datetime
import sqlite3
from TTLib import  *
import WeatherStation
import sys
import subprocess
import globalvars
import meteodata
from BMP085 import BMP085


class Sensor(threading.Thread):
    
    def __init__(self ,cfg):
        self.cfg = cfg
        self.implementedStations = ["SIMULATE","PCE-FWS20","NEVIO8","NEVIO16","PCE-SENSOR","DAVIS-SENSOR"]
        
        if ( self.cfg.sensor_type not in self.implementedStations  ):
            log("Unknown sensor type %s can not continue" % self.cfg.sensor_type)
            log("Implemented sensors are :")
            print self.implementedStations
            
        if ( self.cfg.use_bmp085 ):
            self.bmp085 = BMP085(0x77,3)  
        else:
            self.bmp085 = None

        object.__init__(self)
        
    def GetData(self):
           
            if ( self.bmp085 != None ):
                self.ReadBMP085()
             
                
            globalvars.meteo_data.CalcStatistics()
            globalvars.meteo_data.LogDataToDB()
      
    def ReadBMP085(self):
                p=0.0
                temp = None
                i = 0
                while ( p==0.0 and i < 10):
                    p,temp = self.bmp085.readPressureTemperature()
                    i = i+1
                    time.sleep(0.02)
                    
                if ( p != 0.0): 
                    if ( self.cfg.location_altitude != 0 ):
                        p0 = p / pow( 1 - (0.225577000e-4*self.cfg.location_altitude ),5.25588 )
                    else:
                        p0 = p
                    globalvars.meteo_data.temp_out = temp
                    globalvars.meteo_data.abs_pressure = float(p0 / 100.0) 
                
                
                
 