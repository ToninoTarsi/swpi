
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
from TTLib import  *
import WeatherStation
import sys
import subprocess
import globalvars
import meteodata


class Sensor(threading.Thread):
    
    def __init__(self ,cfg):
        self.cfg = cfg
        self.implementedStations = ["SIMULATE","PCE-FWS20","NEVIO8","NEVIO16"]
        
        if ( self.cfg.sensor_type not in self.implementedStations  ):
            log("Unknown sensor type %s can not continue" % self.cfg.sensor_type)
            log("Implemented sensors are :")
            print self.implementedStations


        object.__init__(self)
        
 