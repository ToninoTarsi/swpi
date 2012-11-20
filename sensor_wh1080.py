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
import WeatherStation
import sys
import subprocess
import globalvars
import meteodata
import sensor_thread
import sensor
from TTLib import *

def log(message) :
    print datetime.datetime.now().strftime("[%d/%m/%Y-%H:%M:%S]") , message

class Sensor_WH1080(sensor.Sensor):
    
    def __init__(self,cfg ):
        
        self.error = False
        sensor.Sensor.__init__(self,cfg )
        
        ret,self.model,self.idd,self.bus = self.Detect()
        if ( not ret ):
            log("ERROR - No PCE-FWS20 station found. ")
            os.system("sudo ./killswpi.sh")
        else:
            log("Detected : %s" % self.model)
            
        try:    
            self.ws = WeatherStation.weather_station()
        except IOError,e:
            log("Error initializining ws")       


    def SetTimeFromWeatherStation(self):
        log("Trying to get time from WH1080. Please wait  ...")
        read_period = self.ws.get_fixed_block(['read_period'],True)
        if ( read_period != 1) :
            self.ws._write_byte(self.ws.fixed_format['read_period'][0],1)
            
            self.ws._write_byte(self.ws.fixed_format['data_changed'][0], 0xAA)
            # wait for station to clear 'data changed'
            while True:
                ack = WeatherStation._decode(
                    self.ws._read_fixed_block(0x0020), self.ws.fixed_format['data_changed'])
                if ack == 0:
                    break
                log('Write_data waiting for ack')
                time.sleep(6)

        oldpos = self.ws.current_pos()
        found = False
        while ( not found ):
            time.sleep(0.1)
            newpos = self.ws.current_pos()
            if ( newpos != oldpos): found = True
            
        thetime =  self.ws.get_fixed_block(['date_time'],True)
        #print thetime
        os.system("sudo date -s '%s'" %  thetime)   
        log("System time adjusted from WH1080")

         
    def Detect(self):
        p = subprocess.Popen("lsusb",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout, stderr) = p.communicate()
        for line in stdout.split('\n') :
            if not line : continue
            if  ( line.find(' WH1080') != -1  ) :
                model = line.split(':')[2][5:]
                idd = line.split(' ')[1]
                bus = line.split(' ')[3][0:3]
                return True,model,idd,bus
        return False,"","",""
    
    # nead to be rewriten
#    def live_data(self,error):
#        self.ws.live_dataNew(self.error)
    
    
    def GetData(self):
        try:
            for data, ptr, ret  in self.ws.live_dataNew(self.error):            
                if ret :
             
                    globalvars.meteo_data.last_measure_time = datetime.datetime.now()
        
                    globalvars.meteo_data.wind_dir = data["wind_dir"]                    
                    globalvars.meteo_data.idx = data[ "idx"]
                    globalvars.meteo_data.status = data[ "status"]
                    globalvars.meteo_data.hum_out = data[ "hum_out"]
                    globalvars.meteo_data.wind_gust = (float(data[ "wind_gust"])*3.6)*self.cfg.windspeed_gain + self.cfg.windspeed_offset
                    globalvars.meteo_data.wind_ave = (float(data[ "wind_ave"])*3.6)*self.cfg.windspeed_gain + self.cfg.windspeed_offset
                    globalvars.meteo_data.rain = float(data[ "rain"])
                    globalvars.meteo_data.temp_in = data[ "temp_in"]
                    globalvars.meteo_data.delay = data[ "delay"]
                    globalvars.meteo_data.abs_pressure = data[ "abs_pressure"]
                    globalvars.meteo_data.hum_in = data[ "hum_in"]
                    globalvars.meteo_data.temp_out = data[ "temp_out"]
                    wind_dir = data[ "wind_dir"]
                    globalvars.meteo_data.wind_dir = wind_dir * 22.5
                    if (wind_dir <  16) :
                        globalvars.meteo_data.wind_dir_code = WeatherStation.get_wind_dir_text()[wind_dir]
                    else:
                        globalvars.meteo_data.wind_dir_code = "ERROR"
                    globalvars.meteo_data.illuminance = None
                    globalvars.meteo_data.uv = None
         
                    globalvars.meteo_data.CalcStatistics()
                    globalvars.meteo_data.LogDataToDB()
                    
                    self.error = False
                
        
        except IOError,e:
            #raise
            log("ERROR with PCE-FWS20  %s . Will retry ..."  % e)
            ret,self.model,self.idd,self.bus = self.Detect()
#            usbdevice = "/dev/bus/usb/%s/%s" % (self.idd , self.bus )
#            os.system( "./usbreset %s" % (usbdevice) )
            self.__init__(self.cfg)
            self.error = True


if __name__ == '__main__':

    configfile = 'swpi.cfg'
        
    
    if not os.path.isfile(configfile):
        "Configuration file not found"
        exit(1)    
    cfg = config.config(configfile)
    
    
    
