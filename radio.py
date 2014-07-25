###########################################################################
#     Sint Wind PI
#       Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################
"""Classes and methods for handling Radio  commands."""

import threading
import time
import config
import random
import datetime
import sqlite3
from TTLib import  *
import pygame
import sys
import globalvars
import RPi.GPIO as GPIO

def playsound(soundfile):
    pygame.mixer.init()
    pygame.mixer.music.load(soundfile)
    #pygame.mixer.music.play()
    pygame.mixer.music.set_volume(1.0)
    time.sleep(1)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        print "Playing", pygame.mixer.music.get_pos()
        time.sleep(0.020)


def playsounds(listofsoundfile):
    
    
    pygame.mixer.init()
    #pygame.mixer.music.play()
    pygame.mixer.music.set_volume(1.0)
    time.sleep(1)
    for soundfile in listofsoundfile:
        if ( not os.path.exists(soundfile)):
            log( "ERROR : File not found : " + soundfile)
            continue
        pygame.mixer.music.load(soundfile)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            #print "Playing", pygame.mixer.music.get_pos()
            time.sleep(0.020)

class RadioThread(threading.Thread):

    def __init__(self,  cfg ):
        self.cfg = cfg
        self._stop = threading.Event()
        
        if ( self.cfg.use_ptt ):
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)   
            GPIO.setup(25, GPIO.OUT)   # PTT PIN
            GPIO.output(25, False)
            
        threading.Thread.__init__(self)

    def stop(self):
        self._stop.set()
    
    def stopped(self):
        return self._stop.isSet()
     
    
    def run(self):
        while not self._stop.isSet():
            time.sleep(self.cfg.radiointerval/2)
            waitForHandUP()
            
            if (  globalvars.meteo_data.last_measure_time != None and  globalvars.meteo_data.status == 0 ):
                log("Radio")

                delay = (datetime.datetime.now() - globalvars.meteo_data.last_measure_time)
                delay_seconds = int(delay.total_seconds())
                
                if (delay_seconds < 350 ):    
                    
                    #prepare list of messages
                    listOfMessages = []
                    listOfMessages.append("./audio/mp3/Beep.mp3")   

                    if ( self.cfg.radio_verbosity == "only_wind") :
                        listOfMessages.append("./audio/mp3/" + str(globalvars.meteo_data.wind_dir_code) + ".mp3")        
                        listOfMessages.append("./audio/mp3/from_short.mp3")   
                        listOfMessages.append("./audio/mp3/" + str(int(globalvars.meteo_data.wind_ave)) + ".mp3")
                        listOfMessages.append("./audio/mp3/to.mp3")   
                        listOfMessages.append("./audio/mp3/" + str(int(globalvars.meteo_data.wind_gust)) + ".mp3")
                    
                    elif ( self.cfg.radio_verbosity == "all") :
                        listOfMessages = []
                        
                        
                        listOfMessages.append("./audio/mp3/hello.mp3")
                        # Message
                        listOfMessages.append("./audio/mp3/message.mp3")
                        
                        if ( self.cfg.sensor_type.upper() == "SIMULATE" ):
                            listOfMessages.append("./audio/mp3/simulate.mp3")
                            
                        if (delay_seconds > 600 ):
                            listOfMessages.append("./audio/mp3/some_problem.mp3") 
                
                        if( globalvars.meteo_data.rain_rate_1h != None and globalvars.meteo_data.rain_rate_1h >= 0.001 ):
                            listOfMessages.append("./audio/mp3/raining.mp3")
                        
                        # Wind Speed and Direction
                        listOfMessages.append("./audio/mp3/winddirection.mp3")
                        listOfMessages.append("./audio/mp3/" + str(globalvars.meteo_data.wind_dir_code) + ".mp3")        
                        listOfMessages.append("./audio/mp3/from.mp3")
                        listOfMessages.append("./audio/mp3/" + str(int(globalvars.meteo_data.wind_ave)) + ".mp3")
                        listOfMessages.append("./audio/mp3/to.mp3")
                        
                        listOfMessages.append("./audio/mp3/" + str(int(globalvars.meteo_data.wind_gust)) + ".mp3")
                        listOfMessages.append("./audio/mp3/km.mp3")
                    
                        if ( globalvars.meteo_data.wind_trend != None ):
                            if ( globalvars.meteo_data.wind_trend < - self.cfg.wind_trend_limit) :
                                listOfMessages.append("./audio/mp3/winddown.mp3")
                            if ( globalvars.meteo_data.wind_trend >  self.cfg.wind_trend_limit) :
                                listOfMessages.append("./audio/mp3/windup.mp3")    
                        # Temperature
                        if ( globalvars.meteo_data.temp_out != None ):
                            listOfMessages.append("./audio/mp3/silence05s.mp3") 
                            listOfMessages.append("./audio/mp3/temperature.mp3")
                            if ( globalvars.meteo_data.temp_out < 0) :
                                listOfMessages.append("./audio/mp3/minus.mp3") 
                                 
                            intera = int(round( abs(globalvars.meteo_data.temp_out) ))
                            listOfMessages.append("./audio/mp3/" + str(intera) + ".mp3")
                            listOfMessages.append("./audio/mp3/degree.mp3")

                        # Dew point
                        if ( globalvars.meteo_data.dew_point != None ):
                            listOfMessages.append("./audio/mp3/silence05s.mp3")
                            listOfMessages.append("./audio/mp3/dewpoint.mp3")
                            if ( globalvars.meteo_data.dew_point < 0) :
                                listOfMessages.append("./audio/mp3/minus.mp3")
                            intera = int(round( abs(globalvars.meteo_data.dew_point) ))
                            listOfMessages.append("./audio/mp3/" + str(intera) + ".mp3")
                            listOfMessages.append("./audio/mp3/degree.mp3")

                        # Pressure
                        if ( globalvars.meteo_data.rel_pressure != None ):
                            thousands, rem = divmod(round(globalvars.meteo_data.rel_pressure), 1000) 
                            thousands = int(thousands * 1000)
                            hundreds, tens = divmod(rem, 100)
                            hundreds = int(hundreds * 100)
                            tens = int(round(tens))    
                            listOfMessages.append("./audio/mp3/silence05s.mp3") 
                            listOfMessages.append("./audio/mp3/pressure.mp3")
                            if ( thousands != 0):
                                listOfMessages.append("./audio/mp3/" + str(thousands) + ".mp3")
                            if ( hundreds != 0):
                                listOfMessages.append("./audio/mp3/" + str(hundreds) + ".mp3")
                            if ( tens != 0 ):
                                listOfMessages.append("./audio/mp3/" + str(tens) + ".mp3")
                            listOfMessages.append("./audio/mp3/hpa.mp3")    
                
                        # Humidity
                        if ( globalvars.meteo_data.hum_out != None ):
                            listOfMessages.append("./audio/mp3/silence05s.mp3") 
                            intera =  int( globalvars.meteo_data.hum_out) 
                            listOfMessages.append("./audio/mp3/umidity.mp3")
                            listOfMessages.append("./audio/mp3/" + str(intera) + ".mp3")
                            listOfMessages.append("./audio/mp3/percent.mp3")
                
                        #Cloud base
                        if (globalvars.meteo_data.cloud_base_altitude != None ) : 
                            if ( globalvars.meteo_data.cloud_base_altitude != -1 ) :
                                thousands, rem = divmod(round(globalvars.meteo_data.cloud_base_altitude), 1000) 
                                thousands = int(thousands * 1000)
                                hundreds, tens = divmod(rem, 100)
                                hundreds = int(hundreds * 100)
                                tens = int(round(tens))    
                                listOfMessages.append("./audio/mp3/silence05s.mp3") 
                                listOfMessages.append("./audio/mp3/cloudbase.mp3")
                                if ( thousands != 0):
                                    listOfMessages.append("./audio/mp3/" + str(thousands) + ".mp3")
                                if ( hundreds != 0):
                                    listOfMessages.append("./audio/mp3/" + str(hundreds) + ".mp3")
                                if ( tens != 0 ):
                                    listOfMessages.append("./audio/mp3/" + str(tens) + ".mp3")
                                listOfMessages.append("./audio/mp3/meters.mp3")
                            else:
                                listOfMessages.append("./audio/mp3/incloud.mp3")
            
            
                        elif ( self.cfg.radio_verbosity == "motor") :
                            listOfMessages = []
                            
                            #listOfMessages.append("./audio/mp3/hello.mp3")
                            # Message
                            listOfMessages.append("./audio/mp3/message.mp3")
                            
                            if ( self.cfg.sensor_type.upper() == "SIMULATE" ):
                                listOfMessages.append("./audio/mp3/simulate.mp3")
                                
                            if (delay_seconds > 600 ):
                                listOfMessages.append("./audio/mp3/some_problem.mp3") 
                    
                            if( globalvars.meteo_data.rain_rate_1h != None and globalvars.meteo_data.rain_rate_1h >= 0.001 ):
                                listOfMessages.append("./audio/mp3/raining.mp3")
                                #listOfMessages.append("./audio/mp3/pioggiainatto.mp3")
                            
                            # Temperature
                            if ( globalvars.meteo_data.temp_out != None ):
                                listOfMessages.append("./audio/mp3/silence05s.mp3") 
                                listOfMessages.append("./audio/mp3/temperature.mp3")
                                if ( globalvars.meteo_data.temp_out < 0) :
                                    listOfMessages.append("./audio/mp3/minus.mp3") 
                                     
                                intera = int(round( abs(globalvars.meteo_data.temp_out) ))
                                listOfMessages.append("./audio/mp3/" + str(intera) + ".mp3")
                                listOfMessages.append("./audio/mp3/degree.mp3")
                    
                                                        
                            # QNH
                            if ( globalvars.meteo_data.rel_pressure != None ):
                                thousands, rem = divmod(round(globalvars.meteo_data.rel_pressure), 1000) 
                                thousands = int(thousands * 1000)
                                hundreds, tens = divmod(rem, 100)
                                hundreds = int(hundreds * 100)
                                tens = int(round(tens))    
                                listOfMessages.append("./audio/mp3/qnh.mp3")
                                if ( thousands != 0):
                                    listOfMessages.append("./audio/mp3/" + str(thousands) + ".mp3")
                                if ( hundreds != 0):
                                    listOfMessages.append("./audio/mp3/" + str(hundreds) + ".mp3")
                                if ( tens != 0 ):
                                    listOfMessages.append("./audio/mp3/" + str(tens) + ".mp3")
 
                            # QFE
                            if ( globalvars.meteo_data.abs_pressure != None ):
                                thousands, rem = divmod(round(globalvars.meteo_data.abs_pressure), 1000) 
                                thousands = int(thousands * 1000)
                                hundreds, tens = divmod(rem, 100)
                                hundreds = int(hundreds * 100)
                                tens = int(round(tens))    
                                listOfMessages.append("./audio/mp3/qfe.mp3")
                                if ( thousands != 0):
                                    listOfMessages.append("./audio/mp3/" + str(thousands) + ".mp3")
                                if ( hundreds != 0):
                                    listOfMessages.append("./audio/mp3/" + str(hundreds) + ".mp3")
                                if ( tens != 0 ):
                                    listOfMessages.append("./audio/mp3/" + str(tens) + ".mp3")
                            
                            # Wind Speed and Direction
                            listOfMessages.append("./audio/mp3/winddirection.mp3")
                            listOfMessages.append("./audio/mp3/" + str(globalvars.meteo_data.wind_dir_code) + ".mp3")        
                            listOfMessages.append("./audio/mp3/from.mp3")
                            listOfMessages.append("./audio/mp3/" + str(int(globalvars.meteo_data.wind_ave)) + ".mp3")
                            listOfMessages.append("./audio/mp3/to.mp3")
                            
                            listOfMessages.append("./audio/mp3/" + str(int(globalvars.meteo_data.wind_gust)) + ".mp3")
                            listOfMessages.append("./audio/mp3/km.mp3")
                        
                            if ( globalvars.meteo_data.wind_trend != None ):
                                if ( globalvars.meteo_data.wind_trend < - self.cfg.wind_trend_limit) :
                                    listOfMessages.append("./audio/mp3/winddown.mp3")
                                if ( globalvars.meteo_data.wind_trend >  self.cfg.wind_trend_limit) :
                                    listOfMessages.append("./audio/mp3/windup.mp3")
                             
                     

    
                    if ( self.cfg.use_ptt ):
                        GPIO.output(25, True)
                        
                    playsounds(listOfMessages)
                    
                    if ( self.cfg.use_ptt ):
                        GPIO.output(25, False)
                 
            time.sleep(self.cfg.radiointerval/2)


if __name__ == '__main__':
    """Main only for testing"""
    
    if os.name == 'nt':
        configfile = 'swpi_w.cfg'
    else:
        configfile = 'swpi_pi.cfg'
    
    if not os.path.isfile(configfile):
        "Configuration file not found"
        exit(1)    
    cfg = config.config(configfile)
  

    radio = RadioThread(cfg)
    radio.start()

          
    print "Done"