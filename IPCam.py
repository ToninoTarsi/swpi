###########################################################################
#     Sint Wind PI
# 	  Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
##########################################################################
# 	  IPCam.py 
#     moves the ipcams to the wind or upwind direction and capture snapshot
#     by Vittorio Godio	info@praiadofrances.net.br
##########################################################################
"""Classes and methods for handling IPCam commands."""

import sqlite3
import Image
import ImageFont
import ImageDraw
import time,datetime
import os
from TTLib import *
import re
import subprocess
import config
import humod
import RPi.GPIO as GPIO
import threading
import sun
import math
import globalvars


class IPCam(object):
	"""Class defining generic IPcams."""

	def __init__(self, deviceNumber,cfg):
		if(deviceNumber == 1):
			self.device = cfg.IPCamIP1
			self.captureresolution = cfg.webcamdevice1captureresolution 
			self.finalresolution = cfg.webcamdevice1finalresolution
			self.caprureresolutionX = cfg.webcamdevice1captureresolutionX
			self.caprureresolutionY = cfg.webcamdevice1captureresolutionY
			self.finalresolutionX = cfg.webcamdevice1finalresolutionX
			self.finalresolutionY = cfg.webcamdevice1finalresolutionY
		elif(deviceNumber == 2):
			self.device = cfg.IPCamIP2
			self.captureresolution = cfg.webcamdevice2captureresolution 
			self.finalresolution = cfg.webcamdevice2finalresolution
			self.caprureresolutionX = cfg.webcamdevice2captureresolutionX
			self.caprureresolutionY = cfg.webcamdevice2captureresolutionY
			self.finalresolutionX = cfg.webcamdevice2finalresolutionX
			self.finalresolutionY = cfg.webcamdevice2finalresolutionY
		else:
			log( "ERROR Only 2 IPCams are allowed in this version of the software"	)
			
		self.cfg = cfg


	def IPCamCapture(self,filename,deviceNumber):

		try:
			#log("Posizione IPcam " + globalvars.meteo_data.wind_dir_code)
			if(self.cfg.IPCamCfg.upper() != "NONE"):
				IP_IPCam1 = "http://" + self.cfg.IPCamIP1
				IP_IPCam2 = "http://" + self.cfg.IPCamIP2

				posCommand = ""
				#log("PASSAGGIO  " + str(deviceNumber))
				if(self.cfg.IPCamCfg.upper() == "IPCAM1" or self.cfg.IPCamCfg.upper() == "IPCAM2"):
					if(globalvars.meteo_data.wind_dir_code == "N" and self.cfg.IPCamPosN != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user=" + self.cfg.IPCamUS1 + " --http-passwd=" + self.cfg.IPCamPW1 +" "+ IP_IPCam1 + self.cfg.IPCamPosN
					if((globalvars.meteo_data.wind_dir_code) == "NE" and self.cfg.IPCamPosNE != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user=" + self.cfg.IPCamUS1 + " --http-passwd=" + self.cfg.IPCamPW1 +" "+ IP_IPCam1 + self.cfg.IPCamPosNE
					if(globalvars.meteo_data.wind_dir_code == "E" and self.cfg.IPCamPosE != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user="  + self.cfg.IPCamUS1 + " --http-passwd=" + self.cfg.IPCamPW1 +" "+ IP_IPCam1 + self.cfg.IPCamPosE
					if(globalvars.meteo_data.wind_dir_code == "SE" and self.cfg.IPCamPosSE != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user=" + self.cfg.IPCamUS1 + " --http-passwd=" + self.cfg.IPCamPW1 +" "+ IP_IPCam1 + self.cfg.IPCamPosSE				
					if(globalvars.meteo_data.wind_dir_code == "S" and self.cfg.IPCamPosS != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user=" + self.cfg.IPCamUS1 + " --http-passwd=" + self.cfg.IPCamPW1 + " " + IP_IPCam1 + self.cfg.IPCamPosS
					if(globalvars.meteo_data.wind_dir_code == "SW" and self.cfg.IPCamPosSW != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user=" + self.cfg.IPCamUS1 + " --http-passwd=" + self.cfg.IPCamPW1 + " " + IP_IPCam1 + self.cfg.IPCamPosSW
					if(globalvars.meteo_data.wind_dir_code == "W" and self.cfg.IPCamPosW != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user=" + self.cfg.IPCamUS1 + " --http-passwd=" + self.cfg.IPCamPW1 + " " + IP_IPCam1 + self.cfg.IPCamPosW
					if(globalvars.meteo_data.wind_dir_code == "NW" and self.cfg.IPCamPosNW != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user=" + self.cfg.IPCamUS1 + " --http-passwd=" + self.cfg.IPCamPW1 + " " + IP_IPCam1 + self.cfg.IPCamPosNW
	
				else: #(self.cfg.IPCamCfg.upper() == "COMBINED"):
					if(globalvars.meteo_data.wind_dir_code == "N" and self.cfg.IPCamPosN != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user=" + self.cfg.IPCamUS1 + " --http-passwd=" + self.cfg.IPCamPW1 +" "+ IP_IPCam1 + self.cfg.IPCamPosN
					if((globalvars.meteo_data.wind_dir_code) == "NE" and self.cfg.IPCamPosNE != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user=" + self.cfg.IPCamUS1 + " --http-passwd=" + self.cfg.IPCamPW1 +" "+ IP_IPCam1 + self.cfg.IPCamPosNE
					if(globalvars.meteo_data.wind_dir_code == "E" and self.cfg.IPCamPosE != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user="  + self.cfg.IPCamUS1 + " --http-passwd=" + self.cfg.IPCamPW1 +" "+ IP_IPCam1 + self.cfg.IPCamPosE
					if(globalvars.meteo_data.wind_dir_code == "SE" and self.cfg.IPCamPosSE != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user=" + self.cfg.IPCamUS1 + " --http-passwd=" + self.cfg.IPCamPW1 +" "+ IP_IPCam1 + self.cfg.IPCamPosSE				
					if(globalvars.meteo_data.wind_dir_code == "S" and self.cfg.IPCamPosS != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user=" + self.cfg.IPCamUS2 + " --http-passwd=" + self.cfg.IPCamPW2 + " " + IP_IPCam2 + self.cfg.IPCamPosS
					if(globalvars.meteo_data.wind_dir_code == "SW" and self.cfg.IPCamPosSW != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user=" + self.cfg.IPCamUS2 + " --http-passwd=" + self.cfg.IPCamPW2 + " " + IP_IPCam2 + self.cfg.IPCamPosSW
					if(globalvars.meteo_data.wind_dir_code == "W" and self.cfg.IPCamPosW != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user=" + self.cfg.IPCamUS2 + " --http-passwd=" + self.cfg.IPCamPW2 + " " + IP_IPCam2 + self.cfg.IPCamPosW
					if(globalvars.meteo_data.wind_dir_code == "NW" and self.cfg.IPCamPosNW != "" and self.cfg.IPCamPosN.upper() != "NONE"):
						posCommand = "sudo wget -q --output-document=webcamtmp --http-user=" + self.cfg.IPCamUS2 + " --http-passwd=" + self.cfg.IPCamPW2 + " " + IP_IPCam2 + self.cfg.IPCamPosNW

				#log(posCommand)
				
				#Posiziona IPCam
				#log("Posiziono CAM " + posCommand)
				if ( posCommand != "" ):
					os.system(posCommand)
				time.sleep(self.cfg.IPCamZZZ)
				
				if(os.path.isfile("webcamtmp")): 
						os.remove("webcamtmp")

				#Snapshot	
				if(deviceNumber == 1):
					snapCommand ="sudo wget -O " + filename + " --http-user=" + self.cfg.IPCamUS1 + " --http-passwd="+ self.cfg.IPCamPW1 + " " + IP_IPCam1 + self.cfg.IPCamSN1
					log( "Getting images with command : " + snapCommand)	
					os.system(snapCommand )
					if(not os.path.isfile(filename)):
						log( "ERROR in capturing webcam image on : " + filename + " "+ self.device )
						return False
							
				if(deviceNumber == 2):
					snapCommand ="sudo wget -O " + filename + " --http-user=" + self.cfg.IPCamUS2 + " --http-passwd="+ self.cfg.IPCamPW2 + " " + IP_IPCam2 + self.cfg.IPCamSN2
					log( "Getting images with command : " + snapCommand)	
					os.system(snapCommand )


					if(not os.path.isfile(filename)):
						log( "ERROR in capturing webcam image on : " + filename + " "+ self.device )
						return False

				#log( "Getting images with command : " + snapCommand)
					
				return True

			else:
				return False

		except ValueError:
				log( " ERROR in capturing webcam image on : " + self.device )
				return False

