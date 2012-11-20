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

DEBUG = False


class PhotoCamera(object):
	"""Class defining generic cameras."""
	def __init__(self, cfg):
		self.finalresolution = cfg.cameradivicefinalresolution
		self.finalresolutionX = cfg.cameradivicefinalresolutionX
		self.finalresolutionY = cfg.cameradivicefinalresolutionY
		self.cfg = cfg
		
		
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
	
	
	def take_pictures(self) :
		"""Capture from all detected cameras and return a list of stored files"""
		
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
			log("Capturing from Camera : %d = %s" %( i+1,camerasInfo[i][0] ) )
			usbcamera = "usb:%s,%s" % (camerasInfo[i][1] , camerasInfo[i][2] )
			filename = "./img/camera" + str(i+self.cfg.start_camera_number) + "_" + datetime.datetime.now().strftime("%d%m%Y-%H%M%S.jpg") 

			if ( not self.cfg.gphoto2_capture_image_and_download ) :
				# this works around --capture-image-and-download not working
				# get rid of any existing files on the card
				self.ClearSDCard(usbcamera)
				os.system("gphoto2 --port " + usbcamera + " --capture-image  1>> " + logFile + " 2>> " + logFile)
				os.system("gphoto2 --port " + usbcamera + "  --get-file=1 --filename=" + filename +  " 1>> " + logFile + " 2>> " + logFile )
			else :	
				os.system("gphoto2 --port " + usbcamera + "  --capture-image-and-download " + gphoto2options[i] + " --filename=" + filename +  " 1>> " + logFile + " 2>> " + logFile )

			if ( os.path.isfile(filename)):	
				pictureTaken.append(filename)
				
		globalvars.bCapturingCamera = False
		for name in pictureTaken :
			log("Captured : " + name)
		return pictureTaken
	
	
	def ClearSDCard(self,usbcamera):
		logFile = datetime.datetime.now().strftime("log/gphoto2_%d%m%Y.log")
		for folder, number, _ in self.list_files(usbcamera) :
			print folder,number 
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
	




	
	
	
	
	
	
