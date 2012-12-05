###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""This module defines the base sensor Nevio ."""

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
import RPi.GPIO as GPIO
import TTLib
import thread
from ctypes import *
import intervalmap

def get_wind_dir_text():
    """Return an array to convert wind direction integer to a string."""

    return ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW']


class Sensor_LacrossTX23(sensor.Sensor):
    # Connections PIN - USING BCM numbering convention !!!!!!
    
    def __init__(self,cfg ):
        
        threading.Thread.__init__(self)

        sensor.Sensor.__init__(self,cfg )        
        
        
        self.libTX23 = cdll.LoadLibrary('./TX23/libTX23.so')
        if ( self.libTX23.init() != 1 ):
            log("Error initializing TX23 library.Try to continue")
        
        self.cfg = cfg
        self.bTimerRun = 0

        
        self.rb_WindSpeed = TTLib.RingBuffer(self.cfg.number_of_measure_for_wind_average_gust_calculation)            
        
        self.currentiDir = None
        
        self.active = True
        self.start()

    
    def run(self):
        sleeptime = self.cfg.windmeasureinterval - self.__MEASURETIME
        if sleeptime < 0 : sleeptime = 0
        
        iDir = c_int()
        iSpeed = c_int()
        while self.active :
            self.libTX23.getData(byref(iDir), byref(iSpeed),0)
            self.currentiDir = iDir 
            #TTLib.log( "currentWind : " +  str(currentWind))
            currentSpeed = iSpeed * self.cfg.windspeed_gain + self.cfg.windspeed_offset
            self.rb_WindSpeed.append(currentSpeed)
            time.sleep(sleeptime)
            
                     
    def Detect(self):
        return True
    
    def SetTimer(self):
        self.bTimerRun = 0
    
    
    def GetCurretWindSpeedAndDir(self):
        """Get wind speed pooling __PIN_A ( may be an interrupt version later )."""
        iDir = c_int()
        iSpeed = c_int()
        while self.active :
            self.libTX23.getData(byref(iDir), byref(iSpeed),0)
            self.currentiDir = iDir 
            #TTLib.log( "currentWind : " +  str(currentWind))
            currentSpeed = iSpeed * self.cfg.windspeed_gain + self.cfg.windspeed_offset
            self.rb_WindSpeed.append(currentSpeed)
            
        return currentSpeed,self.currentiDir
    

    def GetData(self):
        
        seconds = datetime.datetime.now().second
        if ( seconds < 30 ):
            time.sleep(30-seconds)
        else:
            time.sleep(90-seconds)  
            
        wind_ave,wind_gust = self.rb_WindSpeed.getMeanMax()
        if ( wind_ave != None) :

            wind_dir = self.currentiDir * 22.5 
            wind_dir_code =  get_wind_dir_text()[self.currentiDir]
            
            globalvars.meteo_data.status = 0
                        
            globalvars.meteo_data.last_measure_time = datetime.datetime.now()
            globalvars.meteo_data.idx = globalvars.meteo_data.last_measure_time
            
            globalvars.meteo_data.wind_ave     = wind_ave
            globalvars.meteo_data.wind_gust    = wind_gust
            globalvars.meteo_data.wind_dir = wind_dir
            globalvars.meteo_data.wind_dir_code = wind_dir_code
             
            
        if ( self.cfg.use_tmp36 ):
            ch1 = self.libMCP.read_channel(1)
            v1 = ch1 * (3300.0/1024.0)
            temp = (v1 - 500.0) / 10.0
            globalvars.meteo_data.temp_out = temp
                
        sensor.Sensor.GetData(self)
                


if __name__ == '__main__':

    configfile = 'swpi.cfg'
    
   
    cfg = config.config(configfile)
    

    ss = Sensor_LacrossTX23(cfg)
    ss.active = False
    
    
    while ( 1 ) :
        speed, dir  =  ss.GetCurretWindSpeedAndDir()
        temp = None
        if ( cfg.use_tmp36 ):
            ch1 = ss.libMCP.read_channel(1)
            v1 = ch1 * (3300.0/1024.0)
            temp = (v1 - 500.0) / 10.0
           
        print "Speed:",speed,"Dir:",dir,"Temp;",temp
#        ss.GetData()
#        log( "Meteo Data -  D : " + globalvars.meteo_data.wind_dir_code + " S : " + str(globalvars.meteo_data.wind_ave) +   + " G : " + str(globalvars.meteo_data.wind_gust) )
#        #print logData("http://localhost/swpi_logger.php")
     
    
    