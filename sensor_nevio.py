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
from BMP085 import BMP085



def get_wind_dir_code8():
    return [ 'N','NW','NE', 'E', 'SW' , 'W',  'S' , 'SE' ]

def get_wind_dir_code16():
    return [ 'N','NNE','NNW','NW','ENE','NE','E','ESE','WSW','SW','W','WNW','S','SSW','SSE','SE' ]


def get_wind_dir8():
    return [ 0,315,45,90,225,270,180,135 ]

def get_wind_dir16():
    return [ 0,22.5,337.5,315,67.5,45,90,112.5,247.5,225,270,292.5,180,202.5,157.5,135 ]


class Sensor_Nevio(sensor.Sensor):
    
    __MEASURETIME = 2
    
    # Connections PIN - USING BMC numbering convention !!!!!!
    
    __PIN_A = 23  #Anemometer
    __PIN_B1 = 17 
    __PIN_B2 = 21
    __PIN_B3 = 22
    __PIN_B0 = 4
    
    def __init__(self,cfg ):
        
        sensor.Sensor.__init__(self,cfg )        
        
        self.cfg = cfg
        self.bTimerRun = 0
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.__PIN_A, GPIO.IN)   # wind Speed
        GPIO.setup(self.__PIN_B1, GPIO.IN)  # B1
        GPIO.setup(self.__PIN_B2, GPIO.IN)  # B2
        GPIO.setup(self.__PIN_B3, GPIO.IN)  # B3
        if ( self.cfg.sensor_type == "NEVIO16 ") : GPIO.setup(self.__PIN_B0, GPIO.IN)  # B-1
                
        if ( self.cfg.use_bmp085 ):
            self.bmp085 = BMP085(0x77,3)  
        else:
            self.bmp085 = None
                     
    def Detect(self):
        return True,"","",""
    
    def SetTimer(self):
        self.bTimerRun = 0
    
    def GetCurretWindDir(self):
        """Get wind direction decoding Nevio table."""
        b1 = GPIO.input(self.__PIN_B1)
        b2 = GPIO.input(self.__PIN_B2)
        b3 = GPIO.input(self.__PIN_B3)
        if ( self.cfg.sensor_type == "NEVIO16"): b0 = GPIO.input(self.__PIN_B0)
        
        if ( self.cfg.sensor_type != "NEVIO16"):
            wind_dir8  =   b1 + b2*2 + b3*4 
            wind_dir = get_wind_dir8()[wind_dir8]
            wind_dir_code = get_wind_dir_code8()[wind_dir8]   
        else:
            wind_dir16  =   b0 + b1*2 + b2*4 + b3*16
            wind_dir = get_wind_dir16()[wind_dir16]
            wind_dir_code = get_wind_dir_code16()[wind_dir16]                   
        
        return wind_dir, wind_dir_code
    
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
        return ( ( i * self.cfg.windspeed_gain ) / self.__MEASURETIME)  + self.cfg.windspeed_offset
    
    
    def live_data(self):
        """Get data every minutes @ 30."""
        rb = TTLib.RingBuffer(self.cfg.number_of_measure_for_wind_average_gust_calculation)
        
        while 1:    
                 
            currentWind = self.GetCurretWindSpeed()
            rb.append(currentWind)
            
            seconds = datetime.datetime.now().second
            #print   seconds,   currentWind
            if (seconds > 30-self.__MEASURETIME and seconds < 30+self.__MEASURETIME ):
                wind_dir, wind_dir_code =  self.GetCurretWindDir() 
                wind_ave,wind_gust = rb.getMeanMax()
                yield wind_dir, wind_dir_code,wind_ave,wind_gust
            else :
                seconds = datetime.datetime.now().second
                if ( seconds < 30 ):
                    secondsleft = 30-seconds
                else:
                    secondsleft = 90-seconds
                if ( secondsleft > self.cfg.windmeasureinterval+self.__MEASURETIME  ):
                    time.sleep(self.cfg.windmeasureinterval)
            
    def GetData(self):     
        
        for wind_dir, wind_dir_code,wind_ave,wind_gust in self.live_data():
                    
            if ( self.bmp085 != None ):
                globalvars.meteo_data.temp_out = self.bmp085.readTemperature()
                globalvars.meteo_data.abs_pressure = self.bmp085.readPressure() / 100
                
            globalvars.meteo_data.status = 0
                        
            globalvars.meteo_data.last_measure_time = datetime.datetime.now()
            globalvars.meteo_data.idx = globalvars.meteo_data.last_measure_time
            
            globalvars.meteo_data.wind_ave     = wind_ave
            globalvars.meteo_data.wind_gust    = wind_gust
            globalvars.meteo_data.wind_dir = wind_dir
            globalvars.meteo_data.wind_dir_code = wind_dir_code
             
            globalvars.meteo_data.CalcStatistics()
            
            globalvars.meteo_data.LogDataToDB()
            



if __name__ == '__main__':

    configfile = 'swpi.cfg'
    
   
    cfg = config.config(configfile)
    
    globalvars.meteo_data = meteodata.MeteoData(cfg)

    ss = Sensor_Nevio(cfg)
    
    while ( 1 ) :
        print ss.GetCurretWindSpeed()
        
        
#        ss.GetData()
#        log( "Meteo Data -  D : " + globalvars.meteo_data.wind_dir_code + " S : " + str(globalvars.meteo_data.wind_ave) +   + " G : " + str(globalvars.meteo_data.wind_gust) )
#        #print logData("http://localhost/swpi_logger.php")
        time.sleep(0.5)
    
    