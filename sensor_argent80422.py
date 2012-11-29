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
    """Return an array to convert wind direction integer to a string.

    """
    ##_ = Localisation.translation.gettext
    return ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW']



class Sensor_Argent80422(sensor.Sensor):
    
    __MEASURETIME = 2 # Number of seconds for pulse recording
    
    # Connections PIN - USING BCM numbering convention !!!!!!
    
    __PIN_A = 23  #Anemometer
   
    
    def __init__(self,cfg ):
        
        threading.Thread.__init__(self)

        sensor.Sensor.__init__(self,cfg )        
        
        self.cfg = cfg
        self.bTimerRun = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.__PIN_A, GPIO.IN)   # wind Speed
 
        
        self.rb_WindSpeed = TTLib.RingBuffer(self.cfg.number_of_measure_for_wind_average_gust_calculation)            
        
        self.libMCP = cdll.LoadLibrary('./mcp3002/libMCP3002.so')

        self.map = intervalmap.intervalmap()
        self.map[0:68]    = 5
        self.map[68:80]   = 3
        self.map[80:100]  = 4
        self.map[100:141] = 7
        self.map[141:195] = 6
        self.map[195:242] = 9
        self.map[242:315] = 8
        self.map[315:394] = 1
        self.map[394:482] = 2
        self.map[482:559] = 11
        self.map[559:606] = 10
        self.map[606:677] = 15
        self.map[677:733] = 0
        self.map[733:779] = 13
        self.map[779:833] = 14
        self.map[833:1024]= 12
        
        self.start()

    
    def run(self):
        sleeptime = self.cfg.windmeasureinterval - self.__MEASURETIME
        if sleeptime < 0 : sleeptime = 1
        while 1:
            currentWind = self.GetCurretWindSpeed()
            #TTLib.log( "currentWind : " +  str(currentWind))
            self.rb_WindSpeed.append(currentWind)
            time.sleep(sleeptime)
            
                     
    def Detect(self):
        return True,"","",""
    
    def SetTimer(self):
        self.bTimerRun = 0
    
    def GetCurretWindDir(self):
        """Get wind direction reading MCP3002 channel 0."""
        
        ch0 = self.libMCP.read_channel(0)    
        
        wind_dir = self.map[ch0]
        winddir_code = get_wind_dir_text()[wind_dir]
        
        return wind_dir*22.5, winddir_code
    
    def GetCurretWindSpeed(self):
        """Get wind speed pooling __PIN_A ( may be an interrupt version later )."""
        self.bTimerRun = 1
        t = threading.Timer(self.__MEASURETIME, self.SetTimer)
        t.start()
        i = 0
        o = GPIO.input(self.__PIN_A)
        while self.bTimerRun:
            #time.sleep(0.010)
            n = GPIO.input(self.__PIN_A)
            if ( n != o):
                i = i+1
                o = n
        return ( i  / ( self.__MEASURETIME * 2 )) * 2.4 * self.cfg.windspeed_gain    + self.cfg.windspeed_offset
    

    def GetData(self):
        
        seconds = datetime.datetime.now().second
        if ( seconds < 30 ):
            time.sleep(30-seconds)
        else:
            time.sleep(90-seconds)  
            
        wind_ave,wind_gust = self.rb_WindSpeed.getMeanMax()
        if ( wind_ave != None) :

            wind_dir, wind_dir_code =  self.GetCurretWindDir()
            
            globalvars.meteo_data.status = 0
                        
            globalvars.meteo_data.last_measure_time = datetime.datetime.now()
            globalvars.meteo_data.idx = globalvars.meteo_data.last_measure_time
            
            globalvars.meteo_data.wind_ave     = wind_ave
            globalvars.meteo_data.wind_gust    = wind_gust
            globalvars.meteo_data.wind_dir = wind_dir
            globalvars.meteo_data.wind_dir_code = wind_dir_code
             
            
        sensor.Sensor.GetData(self)
                


if __name__ == '__main__':

    configfile = 'swpi.cfg'
    
   
    cfg = config.config(configfile)
    
    globalvars.meteo_data = meteodata.MeteoData(cfg)

    ss = Sensor_Argent80422(cfg)
    
    while ( 1 ) :
        print ss.GetCurretWindSpeed() , ss.GetCurretWindDir()
        
        
#        ss.GetData()
#        log( "Meteo Data -  D : " + globalvars.meteo_data.wind_dir_code + " S : " + str(globalvars.meteo_data.wind_ave) +   + " G : " + str(globalvars.meteo_data.wind_gust) )
#        #print logData("http://localhost/swpi_logger.php")
        time.sleep(0.5)
    
    