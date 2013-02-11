###########################################################################
#     Sint Wind PI
# 	  Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################
"""Classes and methods for handling  Cameras commands."""

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

class CameraWatchDogClass(threading.Thread):

	def __init__(self,cfg):
		self.cfg = cfg
		self.resetted = False
		self.bCacturing = 1
		threading.Thread.__init__(self)
		
	def run(self):
		while (1) :
			time.sleep(self.cfg.WebCamInterval * 3 )
			if ( not self.resetted ) :            
				log("CameraWatchDog: System will Reboot " )
				systemRestart()
			else:
				print "self.resetted = False"
				self.resetted = False
				
	def reset(self):
		self.resetted = True

class PhotoCamera(object):
	"""Class defining generic cameras."""
	
	__PIN_RESET = 24

	
	def __init__(self, cfg):
		self.finalresolution = cfg.cameradivicefinalresolution
		self.finalresolutionX = cfg.cameradivicefinalresolutionX
		self.finalresolutionY = cfg.cameradivicefinalresolutionY
		self.cfg = cfg
		self.bCaturing = 0
		
#		self.CameraWatchDog = CameraWatchDogClass(cfg)
#		if len(self.detectCameras()) > 0 :
#			log("Starting camera Watch Dog")
#			self.CameraWatchDog.run()
		
		if ( self.cfg.use_camera_resetter ):
			GPIO.setwarnings(False)
			GPIO.setmode(GPIO.BCM)
			GPIO.setup(self.__PIN_RESET, GPIO.OUT) 
			GPIO.output(self.__PIN_RESET, True)
		
	def detectCameras(self):
		p = subprocess.Popen("gphoto2 --auto-detect",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		(stdout, stderr) = p.communicate()
		ret = []
		for line in stdout.split('\n') :
			if not line : continue
			words = line.split('usb:')
			if ( len(words) == 2 ):
				model = words[0]
				idd = words[1].split(',')[0]
				bus = words[1].split(',')[1]
				camera = [model,idd,bus]
				ret.append(camera)
		return ret


	def list_files(self,usbcamera) :
		folder = ''
		files = []
		p = subprocess.Popen("gphoto2 --list-files --port " + usbcamera,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		(stdout, stderr) = p.communicate()
	
		for line in stdout.split('\n') :
			if not line : continue
			
			if line[0] == '#' :
				files.append((folder, line.split()[0][1:], line.split()[1]))
			else :
				#print line
				folder = line.split(" ")[-1][1:-2]		
		return files
	
	def SetTimer(self):
		time.sleep(60)
		if ( self.bCaturing ) :            
			log("CameraWatchDog: System will Reboot " )
			systemRestart()
		else:
			self.bCacturing = 0
	
	
	
	def take_pictures(self) :
		"""Capture from all detected cameras and return a list of stored files"""

		self.bCaturing = 1
		thread.start_new_thread(self.SetTimer,()) 
		
		logFile = datetime.datetime.now().strftime("log/gphoto2_%d%m%Y.log")
		pictureTaken = []
		
		camerasInfo = self.detectCameras()
		nCameras = len(camerasInfo)

		if ( nCameras == 0 ):
			globalvars.bCapturingCamera = False
			log( "No digital cameras found" )
			return pictureTaken
		
		log(str(nCameras) + " Cameras found")
		for i in range(0,nCameras):
			log("Camera " + str(i+1) + " : "  + camerasInfo[i][0] + "USB : " + camerasInfo[i][1]  + " " + camerasInfo[i][2]  )

		gphoto2options = self.cfg.gphoto2options.split(',') 
		if ( len(gphoto2options) < nCameras ):
			log("Problem with configuration file !!!. gphoto2options does not have information for all cameras")
			gphoto2options =[]
			for k in range(0,nCameras):
				gphoto2options.append("")
		
		# Reset usb to make some Nikon model work. Do not use with Canon Cameras		
		if ( self.cfg.reset_usb ):
			for i in range(0,nCameras):
	
				usbcamera = "/dev/bus/usb/%s/%s" % (camerasInfo[i][1] , camerasInfo[i][2] )
				os.system( "./usbreset %s" % (usbcamera) )
				
				# whait for the camera to be detected again 
				for i in range(1,100):
					time.sleep(0.1)
					camerasInfo = self.detectCameras()
					if ( len(camerasInfo) == nCameras):
						break
					
			# Update camerasInfo after reset
			camerasInfo = self.detectCameras()
			nCameras = len(camerasInfo)
		
		# Now Capture and acquire global lock ( to do - replace with thread.lock object )
		globalvars.bCapturingCamera = True
		for i in range(0,nCameras):
			bError = False
			log("Capturing from Camera : %d = %s" %( i+1,camerasInfo[i][0] ) )
			usbcamera = "usb:%s,%s" % (camerasInfo[i][1] , camerasInfo[i][2] )
			filename = "./img/camera" + str(i+self.cfg.start_camera_number) + "_" + datetime.datetime.now().strftime("%d%m%Y-%H%M%S.jpg") 

			if ( not self.cfg.gphoto2_capture_image_and_download ) :
				# this works around --capture-image-and-download not working
				# get rid of any existing files on the card
				self.ClearSDCard(usbcamera)
				os.system("gphoto2 --port " + usbcamera + " --capture-image  1>> " + logFile + " 2>> " + logFile)
				os.system("gphoto2 --port " + usbcamera + "  --get-file=1 --filename=" + filename +  " 1>> " + logFile + " 2>> " + logFile )
			else:
				nTry = 0
				bError = True
				cmd = "gphoto2 --port " + usbcamera + "  --capture-image-and-download " + gphoto2options[i] + " --filename=" + filename 
				while ( nTry < 3 and bError == True):
					bError = False	
					p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
					(stdout, stderr) = p.communicate()
#					for line in stdout.split('\n') :
#						if ( len(line) != 0 ): log("gphoto2-stdout " + line)
#						if (line[:3] == "***"):
#							bError = True
					for line in stderr.split('\n') :
						if ( len(line) != 0 ): log(line)
						if (line[:3] == "***"):
							bError = True	
					nTry = nTry + 1
					if ( bError ):
						log("Error capturing camera .. retrying")
						if ( self.cfg.use_camera_resetter ):
							log("Switching off Camera ... ")
							GPIO.output(self.__PIN_RESET, 0)
							time.sleep(2)
							log("Switching on Camera ... ")
							GPIO.output(self.__PIN_RESET, 1)
							time.sleep(10)
						time.sleep(1)
						
				if ( bError ):		
					log("Error capturing camera .. rebooting") 	
					usbcamera_to_reset = "/dev/bus/usb/%s/%s" % (camerasInfo[i][1] , camerasInfo[i][2] )
					os.system( "./usbreset %s" % (usbcamera_to_reset) )								


			if ( not bError and os.path.isfile(filename)):	
				pictureTaken.append(filename)
				
		globalvars.bCapturingCamera = False
		
		for name in pictureTaken :
			log("Captured : " + name)
		
		self.bCaturing = 0

		return pictureTaken


	def ClearSDCard(self,usbcamera):
		#logFile = datetime.datetime.now().strftime("log/gphoto2_%d%m%Y.log")
		logFile = "/dev/null"
		for folder, number, _ in self.list_files(usbcamera) :
			os.system("gphoto2 --port " + usbcamera + " -D --folder=" + folder + "  1>> " + logFile + " 2>> " + logFile )
		
		

def ClearAllCameraSDCards(cfg):
	camera = PhotoCamera(cfg)
	camerasInfo = camera.detectCameras()
	#print "camerasInfo" , camerasInfo
	nCameras = len(camerasInfo)
	
	for i in range(0,nCameras):
		log("Deleting file from " + camerasInfo[i][0] )
		usbcamera = "usb:%s,%s" % (camerasInfo[i][1] , camerasInfo[i][2] )
		
		camera.ClearSDCard(usbcamera)
				


if __name__ == '__main__':
	"""Main only for testing"""
	
	configfile = 'swpi.cfg'
	
	cfg = config.config(configfile)
	
	
	ClearAllCameraSDCards(cfg)
	




	
	
	
	
	
	
