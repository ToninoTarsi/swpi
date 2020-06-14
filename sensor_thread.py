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
from TTLib import *
import WeatherStation
import sys
import subprocess
import globalvars
import meteodata
import sensor
import sensor_simulator
import sensor_wh1080
import sensor_wh1080rf
import sensor_wh1080rtlsdr
import sensor_wh3080rtlsdr
import sensor_nevio
import sensor_argent80422
import sensor_davis
import sensor_lacrossTX23
import sensor_wmr100
import sensor_wmr200
import sensor_wmr918
import sensor_wm918
import sensor_ws2300
import sensor_none
import sensor_vantage_pro2
import sensor_W831
import sensor_LoRa
import sensor_external






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
            
        elif ( self.cfg.sensor_type.upper() == "NEVIO8" or self.cfg.sensor_type.upper() == "NEVIO16" or self.cfg.sensor_type.upper() == "NEVIO16S"  or self.cfg.sensor_type.upper() == "NEVIO4" or self.cfg.sensor_type.upper() == "NEVIO2" or self.cfg.sensor_type.upper() == "NEVIO16W" or self.cfg.sensor_type.upper() == "NEVIO16TT"  ):
            sensor = sensor_nevio.Sensor_Nevio(self.cfg)
            
        elif ( self.cfg.sensor_type.upper()  == "PCE-FWS20"):
            sensor = sensor_wh1080.Sensor_WH1080(self.cfg)
            if self.cfg.set_system_time_from_WeatherStation :
                sensor.SetTimeFromWeatherStation()
                
        elif ( self.cfg.sensor_type.upper()  == "PCE-SENSOR" or self.cfg.sensor_type.upper()  == "PCE-SENSOR-C" or self.cfg.sensor_type.upper()  == "PCE-SENSOR-A" or self.cfg.sensor_type.upper()  == "PCE-SENSOR-AA"):
            sensor = sensor_argent80422.Sensor_Argent80422(self.cfg)
            
        elif ( self.cfg.sensor_type.upper()  == "DAVIS-SENSOR" ):
            sensor = sensor_davis.Sensor_Davis(self.cfg)           
             
        elif ( self.cfg.sensor_type.upper()  == "LACROSS-TX23" ):
            sensor = sensor_lacrossTX23.Sensor_LacrossTX23(self.cfg)     
                              
        elif ( self.cfg.sensor_type.upper()  == "WMR100" ):
            sensor = sensor_wmr100.Sensor_WMR100(self.cfg)       
            
        elif ( self.cfg.sensor_type.upper()  == "WMR200" ):
            sensor = sensor_wmr200.Sensor_WMR200(self.cfg)             
                        
        elif ( self.cfg.sensor_type.upper()  == "WMR918" ):
            sensor = sensor_wmr918.Sensor_WMR918(self.cfg)     
                               
        elif ( self.cfg.sensor_type.upper()  == "WM918" ):
            sensor = sensor_wm918.Sensor_WM918(self.cfg)   
            
        elif ( self.cfg.sensor_type.upper()  == "WH1080-RFM01" ):
            sensor = sensor_wh1080rf.Sensor_WH1080RF(self.cfg)
            
        elif ( self.cfg.sensor_type.upper()  == "WH1080_RTL-SDR" ):
                sensor = sensor_wh1080rtlsdr.Sensor_WH1080RTLSDR(self.cfg)
            
        elif ( self.cfg.sensor_type.upper()  == "WH3080_RTL-SDR" ):
                sensor = sensor_wh3080rtlsdr.Sensor_WH3080RTLSDR(self.cfg)

        elif ( self.cfg.sensor_type.upper()  == "WS23XX" ):
            sensor = sensor_ws2300.Sensor_WS2300(self.cfg)     
            
        elif ( self.cfg.sensor_type.upper()  == "W831" ):
            sensor = sensor_W831.Sensor_W831(self.cfg)                                         
                       
        elif ( self.cfg.sensor_type.upper()  == "DAVIS-VANTAGE-PRO2" ):
            sensor = sensor_vantage_pro2.Sensor_VantagePro2(self.cfg)  
                
        elif ( self.cfg.sensor_type.upper()  == "NONE" ):
            sensor = sensor_none.Sensor_None(self.cfg)           

        elif ( self.cfg.sensor_type.upper()  == "LORA" ):
            sensor = sensor_LoRa.Sensor_LoRa(self.cfg)       
            
        elif ( self.cfg.sensor_type.upper()  == "EXTERNAL" or self.cfg.sensor_type.upper() == "SINTWINDTT"):
            sensor = sensor_external.Sensor_External(self.cfg)                                                 
        else:
            log("Sensor type not implemented. Exiting ...")
            os.system("sudo ./killswpi.sh")
            
            
        # mail loop    
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
    

    
  
    
    
    
               