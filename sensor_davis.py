###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""This module defines the base sensor Davis 7911, 7913, 7914,  6410 ."""

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
import spidev

def get_wind_dir_text():
    """Return an array to convert wind direction integer to a string."""

    return ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW','N']


class Sensor_Davis(sensor.Sensor):
    
    __MEASURETIME = 2 # Number of seconds for pulse recording
    
    # Connections PIN - USING BCM numbering convention !!!!!!
    
    __PIN_A = 23  #Anemometer
   
    
    def __init__(self,cfg ):
        
        self.cfg = cfg

        threading.Thread.__init__(self)

        sensor.Sensor.__init__(self,cfg )        
        
        myrevision = getrevision()
        
        if ( myrevision == "a21041" or myrevision == "a01041"  ):
            self.model = 2
        else:
            self.model = 1
            
        self.model = 2 # ALWAYS USE SPI  
        
        if ( self.model == 2 ) :
            # Open SPI bus
            log("Initializing SPI un device : /dev/spidev%d.0" % (cfg.mcp3002_spiDev) )
            self.spi  = spidev.SpiDev()
            self.spi.open(cfg.mcp3002_spiDev,0)
        else: 
            log("Initializing libMCP")
            self.libMCP = cdll.LoadLibrary('./mcp3002/libMCP3002.so')
            if ( self.libMCP.init() != 0 ):
                log("Error initializing mcp3002 library.Try to continue")
        
        self.bTimerRun = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.__PIN_A, GPIO.IN)   # wind Speed
 
        
        self.rb_WindSpeed = TTLib.RingBuffer(self.cfg.number_of_measure_for_wind_average_gust_calculation)            
    
                
        self.active = True
        self.start()

    
    def run(self):
        sleeptime = self.cfg.windmeasureinterval - self.__MEASURETIME
        if sleeptime < 0 : sleeptime = 0
        while self.active :
            currentWind = self.GetCurretWindSpeed()
            #TTLib.log( "currentWind : " +  str(currentWind))
            self.rb_WindSpeed.append(currentWind)
            time.sleep(sleeptime)
            
                     
    def Detect(self):
        return True
    
    def SetTimer(self):
        self.bTimerRun = 0
    
    def ReadChannel(self,channel):
        data           = 0
        #adc          = self.spi.xfer2([104,0])
        adc         = self.spi.xfer2([1,(2+channel)<<6,0])
        #data         += int(((adc[0]&3) << 8) + adc[1])
        data        += ((adc[1]&31) << 6) + (adc[2] >> 2)
        return data
    
    def GetCurretWindDir(self):
        """Get wind direction reading MCP3002 channel 0."""
        
        ch0 = -1
        while ch0 == -1 :
            if ( self.model == 1 ) :
                ch0 = self.libMCP.read_channel(0)
            else:
                ch0 = self.ReadChannel(0)
            if  ( ch0 == -1 ) :
                log("Error reading mcp3002 channel 0. Retrying ")
                time.sleep(0.1) 

        wind_dir = ((350.0/1023.0)*ch0+5)-self.cfg.davis_error

        #log(self.cfg.davis_error)
        if wind_dir<0:
            wind_dir=359+wind_dir
        val=int((wind_dir/22.5)+.5)
        winddir_code = get_wind_dir_text()[val]


        return wind_dir, winddir_code
    
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
                time.sleep(0.005)
            time.sleep(0.0005)
        return ( ( i  / ( self.__MEASURETIME * 2 ))  * 2.25 * 1.609344 )  * self.cfg.windspeed_gain    + self.cfg.windspeed_offset
    

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
             
            
        if ( self.cfg.use_tmp36 ):
            ch1 = self.libMCP.read_channel(1)
            v1 = ch1 * (3300.0/1024.0)
            temp = (v1 - 500.0) / 10.0
            globalvars.meteo_data.temp_out = temp
                
        sensor.Sensor.GetData(self)
                


if __name__ == '__main__':

    configfile = 'swpi.cfg'
    
   
    cfg = config.config(configfile)
    

    ss = Sensor_Davis(cfg)
    ss.active = False
    
    
    while ( 1 ) :
        speed =  ss.GetCurretWindSpeed() 
        dir =   ss.GetCurretWindDir()
        temp = None
        if ( cfg.use_tmp36 ):
            ch1 = ss.libMCP.read_channel(1)
            v1 = ch1 * (3300.0/1024.0)
            temp = (v1 - 500.0) / 10.0
           
        print "Speed:",speed,"Dir:",dir,"Temp;",temp
#        ss.GetData()
#        log( "Meteo Data -  D : " + globalvars.meteo_data.wind_dir_code + " S : " + str(globalvars.meteo_data.wind_ave) +   + " G : " + str(globalvars.meteo_data.wind_gust) )
#        #print logData("http://localhost/swpi_logger.php")
     
    
    