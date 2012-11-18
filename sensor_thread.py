###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""This module defines the base sensors Thread class."""


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
import sensor
import sensor_simulator
import sensor_wh1080
import sensor_nevio



def detectWH1080():

    p = subprocess.Popen("lsusb",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    ret = []
    for line in stdout.split('\n') :
        if not line : continue
        if  ( line.find(' WH1080') != -1  ) :
            model = line.split(':')[2][5:]
            idd = line.split(' ')[1]
            bus = line.split(' ')[3][0:3]
            return True,model,idd,bus
    return False,"","",""


def log(message) :
     print datetime.datetime.now().strftime("[%d/%m/%Y-%H:%M:%S]") , message



class WindSensorThread(threading.Thread):
    """WindSensors thread."""
    def __init__(self,  cfg ):
        
        self.cfg = cfg
                
        self.date = datetime.datetime.now()
        self.day = datetime.datetime.now().strftime("%d%m%Y")
        
        self._stop = threading.Event()
        threading.Thread.__init__(self)

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()



    def run(self):

        log ("Starting sensor reading - Sensor type is : " + self.cfg.sensor_type)
        
        sensor = None
        
        if ( self.cfg.sensor_type.upper() == "SIMULATE"):             
            sensor = sensor_simulator.Sensor_Simulator(self.cfg)
            
        elif ( self.cfg.sensor_type.upper() == "NEVIO8" or self.cfg.sensor_type.upper() == "NEVIO16"):
            sensor = sensor_nevio.Sensor_Nevio(self.cfg)
            
        elif ( self.cfg.sensor_type.upper()  == "PCE-FWS20"):
            sensor = sensor_wh1080.Sensor_WH1080(self.cfg)
            if self.cfg.set_system_time_from_WeatherStation :
                sensor.SetTimeFromWeatherStation()
            
        else:
            log("Sensor type not implemented. Exiting")
            os.system("sudo ./killswpi.sh")
            
        while not self._stop.isSet():

            sensor.GetData()
                
            
            
if __name__ == '__main__':

    configfile = 'swpi.cfg'
        
    
    if not os.path.isfile(configfile):
        "Configuration file not found"
        exit(1)    
    cfg = config.config(configfile)
    
    wind_sensor_thread = WindSensorThread(cfg)
    wind_sensor_thread.start()
    

    
  
    
    
    
               