###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""This module defines the base sensors none ."""


import threading
import time
import config
import random
import datetime
import sqlite3
from TTLib import  *
import sys
import subprocess
import globalvars
import meteodata
import sensor_thread
import sensor 

class Sensor_None(sensor.Sensor):
    
    def __init__(self,cfg ):
        sensor.Sensor.__init__(self,cfg )
        
    def Detect(self):
        return True,"","",""
    
    def GetData(self):
             
        seconds = datetime.datetime.now().second
        if ( seconds < 30 ):
            time.sleep(30-seconds)
        else:
            time.sleep(90-seconds)  
        globalvars.meteo_data.last_measure_time = datetime.datetime.now()
        globalvars.meteo_data.idx = datetime.datetime.now()
        globalvars.meteo_data.status  = 0
        globalvars.meteo_data.delay = 0       
        globalvars.meteo_data.hum_in  = None     
        globalvars.meteo_data.temp_in  = None    
        globalvars.meteo_data.hum_out  = None    
        globalvars.meteo_data.temp_out   =None  
        globalvars.meteo_data.abs_pressure = None
        globalvars.meteo_data.wind_ave     = None
        globalvars.meteo_data.wind_gust    = None
        globalvars.meteo_data.wind_dir     = None
        globalvars.meteo_data.wind_dir_code = None
        globalvars.meteo_data.rain  = None      
        globalvars.meteo_data.illuminance = None
        globalvars.meteo_data.uv = None
        
            
     
        sensor.Sensor.GetData(self)

            


if __name__ == '__main__':

   
    configfile = 'swpi.cfg'
    
   
    cfg = config.config(configfile)
    
    ss = Sensor_None(cfg)
    
    while ( 1 ) :
        ss.GetData()
        
        print logData("http://localhost/swpi_logger.php")
        time.sleep(0.2)
    
    