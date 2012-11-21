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
                    listOfMessages.append("./audio/mp3/" + str(globalvars.meteo_data.wind_dir_code) + ".mp3")        
                    listOfMessages.append("./audio/mp3/from_short.mp3")   
                    listOfMessages.append("./audio/mp3/" + str(int(globalvars.meteo_data.wind_ave)) + ".mp3")
                    listOfMessages.append("./audio/mp3/to.mp3")   
                    listOfMessages.append("./audio/mp3/" + str(int(globalvars.meteo_data.wind_gust)) + ".mp3")
                
                
                    playsounds(listOfMessages)
                 
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