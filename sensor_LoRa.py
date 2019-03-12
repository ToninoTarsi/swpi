###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""This module defines the LoRa receiver sensor ."""


import threading
import time
import config
import random
import datetime
import sqlite3
from TTLib import  *
import sys
import subprocess
import globalvars
import meteodata
import sensor_thread
import sensor 
import rf95


# BW                    CODE
# 
# BW_7K8HZ=0x00           7.8            
# BW_10K4HZ=0x10         10.4        
# BW_15K6HZ=0x20         15.6        
# BW_20K8HZ=0x30         20.8        
# BW_31K25HZ=0x40        31.25        
# BW_41K7HZ=0x50         41.7        
# BW_62K5HZ=0x60         62.5        
# BW_125KHZ=0x70        125            
# BW_250KHZ=0x80        250            
# BW_500KHZ=0x90        500            
# 
# 
# CR                        CODE
# 
# CODING_RATE_4_5=0x02    4/5
# CODING_RATE_4_6=0x04    4/6
# CODING_RATE_4_7=0x06    4/7
# CODING_RATE_4_8=0x08    4/8
# 
# 
# SF                                    CODE
# 
# 
# SPREADING_FACTOR_64CPS=0x60             6
# SPREADING_FACTOR_128CPS=0x70            7
# SPREADING_FACTOR_256CPS=0x80            8
# SPREADING_FACTOR_512CPS=0x90            9
# SPREADING_FACTOR_1024CPS=0xa0          10
# SPREADING_FACTOR_2048CPS=0xb0          11
# SPREADING_FACTOR_4096CPS=0xc0          12


class Sensor_LoRa(sensor.Sensor):
    
    def __init__(self,cfg ):
        self.cfg = cfg
        
        threading.Thread.__init__(self)

        sensor.Sensor.__init__(self,cfg )        
        
        self.lora = rf95.RF95(self.cfg.LoRa_spiDev,0, None,None)
        if self.lora.init(): 
            self.lora.set_frequency(self.cfg.LoRa_frequency)
            self.lora.set_tx_power(self.cfg.LoRa_power)
            self.lora.set_modem_config_simple(getLoRaBWCode(cfg.LoRa_BW),
                                            getLoRaCRCode(self.cfg.LoRa_CR), 
                                            getLoRaSFCode(self.cfg.LoRa_SF))     
                   
            log("LoRa 0K (" +str(cfg.LoRa_frequency)+ "," + cfg.LoRa_BW+","+self.cfg.LoRa_CR+","+self.cfg.LoRa_SF+ "," +cfg.LoRa_mode +")" )
        else:
            log("ERROR RF95 not found")
            self.lora = None
            
    def Detect(self):
        return True,"","",""
        #return self.lora.init()
    
    def GetData(self):
#    SWPI
#     ['StationID'] =    1        
#     ['wind_dir'] =     2
#     ['wind_ave'] =     3
#     ['wind_gust'] =    4
#     ['temp_out'] =     5
#     ['hum_out'] =      6
#     ['abs_pressure'] = 7
#     ['offiline'] =     8 
#     ['battery'] =      9  optiona
     
        if ( self.lora == None ):
            log("LoRA - Wrong Initialization")
            time.sleep(60)
            return
        
        try:
            str_received = self.receive_data()
            str_json,cksum,calc_cksum = checksum(str_received)
            #print "cksum",cksum,"calc_cksum",calc_cksum
            if cksum != calc_cksum:
                log("LoRA - Wrong checksum")
                return
    
            nfields = len(str_json.split(','))
            code = str_json.split(',')[0]
            StationID = str_json.split(',')[1]
            if ( code == "$SW" and StationID == self.cfg.LoRa_ID):
                wind_dir =  None if (str_json.split(',')[2] == "" ) else float(str_json.split(',')[2])
                wind_ave =  None if (str_json.split(',')[3] == "" ) else int(str_json.split(',')[3])
                wind_gust = None if (str_json.split(',')[4] == "" ) else int(str_json.split(',')[4])
                temp_out =  None if (str_json.split(',')[5] == "" ) else float(str_json.split(',')[5])
                hum_out =   None if (str_json.split(',')[6] == "" ) else int(str_json.split(',')[6])
                abs_pressure = None if (str_json.split(',')[7] == "" ) else  int(str_json.split(',')[7])
    
                setOffline = 0
                if ( globalvars.offline and  str_json.split(',')[8] == "0"):
                    setOffline = 1
                if ( not globalvars.offline and  str_json.split(',')[8] == "1"):
                    setOffline = 2
    
    
                if ( nfields > 9 ):
                    battery = None if (str_json.split(',')[9] == "" ) else  float(str_json.split(',')[9])
                else:
                    battery = None
                    
                if (wind_dir!=None): wind_dir_code = degToCompass(wind_dir)
            
                time.sleep(0.100)
                if ( self.cfg.LoRa_mode.upper()[0]  == "B"):
                    str_act = ",".join(("$SWACT",self.cfg.LoRa_ID))
                    self.lora.send(self.lora.str_to_data(str_act))
                    self.lora.wait_packet_sent()
            
            
                globalvars.meteo_data.last_measure_time = datetime.datetime.now()
                globalvars.meteo_data.idx = globalvars.meteo_data.last_measure_time
                globalvars.meteo_data.status  = 0
            
                globalvars.meteo_data.wind_dir = wind_dir
                globalvars.meteo_data.wind_ave = wind_ave
                globalvars.meteo_data.wind_gust = wind_gust
                globalvars.meteo_data.temp_out = temp_out
                globalvars.meteo_data.temp_in = None
                globalvars.meteo_data.hum_out = hum_out
                globalvars.meteo_data.hum_in = None
                globalvars.meteo_data.abs_pressure   = abs_pressure
                globalvars.meteo_data.battery   = battery
                globalvars.meteo_data.rssi = self.lora.last_rssi
                
                globalvars.meteo_data.wind_dir_code = wind_dir_code
                if ( setOffline == 1 ):
                    self.cfg.setOffline("0")
                if ( setOffline == 2 ):
                    self.cfg.setOffline("1")
                    
                sensor.Sensor.GetData(self)               
    
        except:
            log("ERROR in getting LoRa data")
            

            
    def receive_data(self):
        log("Waiting for LoRa data...")
        while not self.lora.available():
            time.sleep(0.1)
        data = self.lora.recv()
        str_packet = ""
        for ch in data:
            if (ch<256):
                str_packet = str_packet + chr(ch)
        log("LoRa Received (" +str(self.lora.last_rssi) + "dBm): " + str_packet)
        
        #StationID = data[0]
        #str_json =  data[1:]   
        #str_json = '{"winDayGustMin": 52.8, "uv": null, "TempInMin": null, "cloud_base_altitude": 1205.0, "PressureMax": 1021.9012464011463, "last_capture": "None", "UmOutMin": 73.65052578363542, "wind_dir_ave": 42.04914984740202, "hum_in": null, "temp_out": 0.3121126046637073, "location_altitude": 1205.0, "station_name": "Monte Cucco", "winDayMin": 46.879999999999995, "wind_chill": -8.235812387173818, "UmOutMax": 100.0, "location_longitude": 12.773246, "wind_trend_limit": 7.0, "temp_in": null, "illuminance": null, "abs_pressure": 883.812076676576, "version": "01.25.33", "rain_rate_24h": null, "offline": 0, "winDayGustMax": 67.2, "dew_point": 0.3121126046637073, "TempOutMin": 0.3121126046637073, "UmInMin": null, "winDayMax": 61.20000000000002, "UmInMax": null, "rain_rate": null, "wind_ave": 58.239999999999995, "rain": null, "TempCPU": 29.3, "freedisk": 1345634304, "wind_trend": -1.8428458498025186, "rel_pressure": 1021.561423449382, "pressure_trend": 0.7979010247961469, "last_measure_time": "[23/01/2018-15:30:30]", "wind_dir": 45.0, "wind_dir_code": "NE", "hum_out": 100.0, "wind_gust": 62.4, "idx": "[23/01/2018-15:30:30]", "location_latitude": 43.349704, "temp_apparent": -12.951536150249714, "rain_rate_1h": null, "PressureMin": 1019.9918652703557, "TempInMax": null, "wind_speed_units": "kmh", "TempOutMax": 0.9665458917617797}'
        return  str_packet
    
if __name__ == '__main__':

   
    configfile = 'swpi.cfg'
    
   
    cfg = config.config(configfile)
    
    ss = Sensor_LoRa(cfg)
    
    while ( 1 ) :
        ss.GetData()
        
        #print logData("http://localhost/swpi_logger.php")
        time.sleep(0.2)
    
    