###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""This module defines the base sensorssimulator ."""


import threading
import time
import config
import random
import datetime
import _strptime
import sqlite3
from TTLib import  *
import sys
import subprocess
import globalvars
import meteodata
import sensor_thread
import sensor 

class Sensor_External(sensor.Sensor):
    
    def __init__(self,cfg ):
        sensor.Sensor.__init__(self,cfg )
        self.last_time = None;
        
    def Detect(self):
        return True,"","",""
    
    def GetData(self):
             
        #print "GetData"
            
        mydata = getCurrentMeteoDataFromUrl(self.cfg.external_sensor_path)
        
        thetime = mydata["last_measure_time"]
        
        if ( self.last_time == None or self.last_time != thetime):
        
            self.last_time = thetime
        
            log( "Newdata from External meteo.txt %s" % mydata["last_measure_time"] )
        
            if (mydata["offline"] == 1):
                self.offline = True
                if ( self.cfg.offline == "False" ):
                    self.cfg.setOffline("1")
            else:
                self.offline = False
                if ( self.cfg.offline == "True" ):
                    self.cfg.setOffline("0")
                
            
            
            globalvars.meteo_data.last_measure_time = datetime.datetime.strptime(mydata["last_measure_time"],"[%d/%m/%Y-%H:%M:%S]")
            globalvars.meteo_data.idx = datetime.datetime.strptime(mydata["idx"],"[%d/%m/%Y-%H:%M:%S]")
            globalvars.meteo_data.status = 0
            
            
            globalvars.meteo_data.hum_out  = mydata["hum_out"]
            globalvars.meteo_data.temp_out  = mydata["temp_out"]  
            globalvars.meteo_data.abs_pressure = mydata["abs_pressure"]
            globalvars.meteo_data.wind_ave     = mydata["wind_ave"]
            globalvars.meteo_data.wind_gust    = mydata["wind_gust"]
            globalvars.meteo_data.wind_dir     = mydata["wind_dir"]
            globalvars.meteo_data.wind_dir_code = mydata["wind_dir_code"]
            globalvars.meteo_data.battery = mydata["battery"]
            globalvars.meteo_data.rssi = mydata["rssi"]         
            
            if ( self.cfg.sensor_type.upper()  == "EXTERNAL"):
                globalvars.meteo_data.hum_out  = mydata["hum_out"]    
                globalvars.meteo_data.temp_out   = mydata["temp_out"]  
                globalvars.meteo_data.rain  = mydata["rain"]      
                globalvars.meteo_data.illuminance = mydata["illuminance"]
                globalvars.meteo_data.uv = mydata["uv"]
                globalvars.meteo_data.wind_dir_ave = mydata["wind_dir_ave"]
                globalvars.meteo_data.rel_pressure = mydata["rel_pressure"]
                globalvars.meteo_data.rain = mydata["rain"]         
                globalvars.meteo_data.rain_rate = mydata["rain_rate"]         
                globalvars.meteo_data.wind_chill = mydata["wind_chill"]         
                globalvars.meteo_data.temp_apparent = mydata["temp_apparent"]         
                globalvars.meteo_data.dew_point = mydata["dew_point"]         
                globalvars.meteo_data.cloud_base_altitude = mydata["cloud_base_altitude"]         
                globalvars.meteo_data.uv = mydata["uv"]         
                globalvars.meteo_data.illuminance = mydata["illuminance"]         
                globalvars.meteo_data.winDayMin = mydata["winDayMin"]         
                globalvars.meteo_data.winDayMax = mydata["winDayMax"]         
                globalvars.meteo_data.winDayGustMin = mydata["winDayGustMin"]         
                globalvars.meteo_data.winDayGustMax = mydata["winDayGustMax"]         
                globalvars.meteo_data.TempOutMin = mydata["TempOutMin"]         
                globalvars.meteo_data.TempOutMax = mydata["TempOutMax"]         
                globalvars.meteo_data.TempInMin = mydata["TempInMin"]         
                globalvars.meteo_data.TempInMax = mydata["TempInMax"]         
                globalvars.meteo_data.UmOutMin = mydata["UmOutMin"]         
                globalvars.meteo_data.UmOutMax = mydata["UmOutMax"]         
                globalvars.meteo_data.UmInMin = mydata["UmInMin"]         
                globalvars.meteo_data.UmInMax = mydata["UmInMax"]         
                globalvars.meteo_data.PressureMin = mydata["PressureMin"]         
                globalvars.meteo_data.PressureMax = mydata["PressureMax"]         
                globalvars.meteo_data.rain_rate_24h = mydata["rain_rate_24h"]         
                globalvars.meteo_data.rain_rate_1h = mydata["rain_rate_1h"]         
                globalvars.meteo_data.wind_trend = mydata["wind_trend"]         


            sensor.Sensor.GetData(self)
                        
            seconds = datetime.datetime.now().second
            if ( seconds < 30 ):
                time.sleep(30-seconds)
            else:
                time.sleep(90-seconds)
            time.sleep(10)


        else:
            time.sleep(20)

if __name__ == '__main__':

   
    configfile = 'swpi.cfg'
    
   
    cfg = config.config(configfile)
    
    ss = Sensor_External(cfg)
    
    while ( 1 ) :
        ss.GetData()
        
        
    
    