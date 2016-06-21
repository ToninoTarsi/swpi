###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""This module defines the base sensor PCE ."""

# sudo pip install spidev --upgrade 
# sudo apt-get clean


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
import spidev



class Sensor_Argent80422(sensor.Sensor):
    
    __MEASURETIME = 2 # Number of seconds for pulse recording
    
    # Connections PIN - USING BCM numbering convention !!!!!!
    
    __PIN_A = 23  #Anemometer
   
    
    def __init__(self,cfg ):
        
        threading.Thread.__init__(self)

        sensor.Sensor.__init__(self,cfg )        
        
        myrevision = getrevision()
        
        if ( myrevision == "a21041" or myrevision == "a01041"  ):
            self.model = 2
        else:
            self.model = 1
            
        #print myrevision 
        
        if ( self.model == 2 ) :
            # Open SPI bus
            log("Initializing SPI")
            self.spi  = spidev.SpiDev()
            self.spi.open(0,0)
        else: 
            log("Initializing libMCP")
            self.libMCP = cdll.LoadLibrary('./mcp3002/libMCP3002.so')
            if ( self.libMCP.init() != 0 ):
                log("Error initializing mcp3002 library.Try to continue")
        
        self.cfg = cfg
        self.bTimerRun = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.__PIN_A, GPIO.IN)   # wind Speed
 
        
        self.rb_WindSpeed = TTLib.RingBuffer(self.cfg.number_of_measure_for_wind_average_gust_calculation)            
        

        self.map = intervalmap.intervalmap()
        
        #PCE-SENSOR-C Cucco per oriantare correttamente i sensori
        if ( self.cfg.sensor_type.upper()  == "PCE-SENSOR-C" ):
            self.map[0:75]    = 7
            self.map[75:89]   = 5
            self.map[89:111]  = 6
            self.map[111:156] = 9
            self.map[156:214] = 8
            self.map[214:264] = 11
            self.map[264:342] = 10
            self.map[342:424] = 3
            self.map[424:514] = 4
            self.map[514:593] = 13
            self.map[593:640] = 12
            self.map[640:712] = 1
            self.map[712:769] = 2
            self.map[769:815] = 15
            self.map[815:870] = 0
            self.map[870:1024]= 14
        else:
            self.map[0:75]    = 5
            self.map[75:89]   = 3
            self.map[89:111]  = 4
            self.map[111:156] = 7
            self.map[156:214] = 6
            self.map[214:264] = 9
            self.map[264:342] = 8
            self.map[342:424] = 1
            self.map[424:514] = 2
            self.map[514:593] = 11
            self.map[593:640] = 10
            self.map[640:712] = 15
            self.map[712:785] = 0
            self.map[785:815] = 13
            self.map[815:870] = 14
            self.map[870:1024]= 12
                            
        self.active = True
        self.start()


    def get_wind_dir_text(self):
        """Return an array to convert wind direction integer to a string."""
        return ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW']
    
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
        
        #print "ch0",ch0
        wind_dir = self.map[ch0]
        winddir_code = self.get_wind_dir_text()[wind_dir]
        
        return wind_dir*22.5, winddir_code 
    
    def GetCurretWindSpeed(self):
        """Get wind speed pooling __PIN_A ( may be an interrupt version later )."""
        self.bTimerRun = 1
        t = threading.Timer(self.__MEASURETIME, self.SetTimer)
        t.start()
        i = 0
        o = GPIO.input(self.__PIN_A)
        while self.bTimerRun:
            n = GPIO.input(self.__PIN_A)
            if ( n != o):
                i = i+1
                o = n
                time.sleep(0.005)
            time.sleep(0.0005)
        return (( i  / ( self.__MEASURETIME * 2 )) * 2.4 )  * self.cfg.windspeed_gain    + self.cfg.windspeed_offset
    





    def GetCurretWindSpeedOld(self):
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
        return (( i  / ( self.__MEASURETIME * 2 )) * 2.4 )  * self.cfg.windspeed_gain    + self.cfg.windspeed_offset
    


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
    

    ss = Sensor_Argent80422(cfg)
    ss.active = False
    
    
    while ( 1 ) :
        speed =  ss.GetCurretWindSpeed() 
        dir =   ss.GetCurretWindDir()
        temp = None
 
           
        print "Speed:",speed,"Dir:",dir,"Temp;",temp
#        ss.GetData()
#        log( "Meteo Data -  D : " + globalvars.meteo_data.wind_dir_code + " S : " + str(globalvars.meteo_data.wind_ave) +   + " G : " + str(globalvars.meteo_data.wind_gust) )
#        #print logData("http://localhost/swpi_logger.php")
     
    
    