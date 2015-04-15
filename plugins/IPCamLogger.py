###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     USB comunication based pywws by 'Jim Easterbrook' <jim@jim-easterbrook.me.uk>
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""example plugin."""

import threading
import random
import datetime
import sqlite3
import sys
import subprocess
import sys 
import os
import thread
import time,datetime

import globalvars
import meteodata
from TTLib import  *
import RPi.GPIO as GPIO
import config

class swpi_plugin(threading.Thread):  #  do not change the name of the class
    
	def __init__(self,cfg):
		self.cfg = cfg
		threading.Thread.__init__(self)
        
        ###################### Plugin Initialization ################
        
        ###################### End Initialization ##################
        
        
	def run(self):
		log("Starting plugin : %s" % sys.modules[__name__])
		while 1:
        ###################### Plugin run
			time.sleep(120-datetime.datetime.now().second)
			if ( globalvars.meteo_data.status == 0 ):
				logData(self.cfg.serverfile,self.cfg.SMSPwd)
				log("Posizione IPcam " + globalvars.meteo_data.wind_dir_code)
				if (globalvars.meteo_data.wind_dir_code == "N"):
					posCommand = (self.cfg.webcamPosN) 
				if (str(globalvars.meteo_data.wind_dir_code) == "NE"):
					posCommand = (self.cfg.webcamPosNE)
				if (globalvars.meteo_data.wind_dir_code == "E"):
					posCommand = (self.cfg.webcamPosE)
				if (globalvars.meteo_data.wind_dir_code == "SE"):
					posCommand = (self.cfg.webcamPosSE)
				if (globalvars.meteo_data.wind_dir_code == "S"):
					posCommand = (self.cfg.webcamPosS)
				if (globalvars.meteo_data.wind_dir_code == "SW"):
					posCommand = (self.cfg.webcamPosSW)
				if (globalvars.meteo_data.wind_dir_code == "W"):
					posCommand = (self.cfg.webcamPosW)
				if (globalvars.meteo_data.wind_dir_code == "NW"):
					posCommand = (self.cfg.webcamPosNW)
				#log("wget -q " + posCommand)
				os.system("wget -q --output-document=webcamtmp " + posCommand )
				if (os.path.isfile(posCommand)): 
					os.remove("webcamtmp")
        ###################### end of Plugin run
		
