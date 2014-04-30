###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""This module defines the base sensor Ventus W831 """

import threading
import time
import config
import random
import datetime
import sqlite3
from TTLib import *
import sys
import subprocess
import globalvars
import meteodata
import sensor_thread
import sensor 
import TTLib
import thread
from ctypes import *

def get_wind_dir_text():
    """Return an array to convert wind direction integer to a string."""
    return ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW']


forecastMap = { 0:'Grande Nevicata', 1:'Neve Leggera ', 2:'Temporale', 3:'Pioggia Leggera', 4:'Nuvoloso', 5:'Qualche Nuvola', 6:'Soleggiato' }


class Sensor_W831(sensor.Sensor):
    
   
    def __init__(self,cfg ):
        
        threading.Thread.__init__(self)
        sensor.Sensor.__init__(self,cfg )        
                        

    
    def run(self):
        pass
            
                     
    def Detect(self):
        return True
    

    

    def GetData(self):
        
        seconds = datetime.datetime.now().second
        if ( seconds < 30 ):
            time.sleep(30-seconds)
        else:
            time.sleep(90-seconds)  
        
        try:
            output = subprocess.check_output(["./te923tool-0.6.1/te923con"]);
            data = output.split(":")
            #print data
            
            globalvars.meteo_data.status = 0
            
            globalvars.meteo_data.last_measure_time = datetime.datetime.now()
            globalvars.meteo_data.idx = globalvars.meteo_data.last_measure_time 
            
            
            globalvars.meteo_data.temp_in = float(data[1])
            globalvars.meteo_data.hum_in = int(data[2])
            globalvars.meteo_data.temp_out = float(data[3])
            globalvars.meteo_data.hum_out = int(data[4])
            globalvars.meteo_data.abs_pressure = float(data[13])
            globalvars.meteo_data.wind_ave = (float(data[18])*3.6)*self.cfg.windspeed_gain + self.cfg.windspeed_offset
            globalvars.meteo_data.wind_gust = (float(data[19])*3.6)*self.cfg.windspeed_gain + self.cfg.windspeed_offset
            globalvars.meteo_data.rain = int(data[21])
            globalvars.meteo_data.delay = 0
            wind_dir = int(data[17])
            if ( wind_dir < 16 ):
                globalvars.meteo_data.wind_dir = wind_dir * 22.5
                globalvars.meteo_data.wind_dir_code = get_wind_dir_text()[wind_dir]
            else:
                globalvars.meteo_data.wind_dir_code = None
                globalvars.meteo_data.wind_dir_code = None
                
            globalvars.meteo_data.illuminance = None
            globalvars.meteo_data.uv = None
        except:
            log("Error reading station data")
        
	# unused variables
        #uv = int(data[14])
        #forecast = int(data[15])
        #stormwarning = int(data[16])
        #forecastTxt = forecastMap.get(forecast, str(forecast))
        #print "VENTUS-W831 Barometer Forecast: " , forecastTxt

        # TO REMOVE
        if ( globalvars.meteo_data.abs_pressure == 0 ) : 
            globalvars.meteo_data.abs_pressure = None
                
        sensor.Sensor.GetData(self)
                


if __name__ == '__main__':

    configfile = 'swpi.cfg'
    
   
    cfg = config.config(configfile)
    

    ss = Sensor_W831(cfg)
    ss.active = False
    
    
    while ( 1 ) :
        
        pass
    
    
    
