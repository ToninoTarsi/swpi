###########################################################################
#     Sint Wind PI
# 	  Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################
"""Classes and methods for handling Web and Cam commands."""

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
workaround = False


class PhotoCamera(object):
	"""Class defining generic web and cam s."""

	def __init__(self, cfg):
		self.finalresolution = cfg.cameradivicefinalresolution
		self.finalresolutionX = cfg.cameradivicefinalresolutionX
		self.finalresolutionY = cfg.cameradivicefinalresolutionY
		self.cfg = cfg
		


		#self.reset_nikon()
		

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
		
		#print stdout
		for line in stdout.split('\n') :
			if not line : continue
			
			if line[0] == '#' :
				files.append((folder, line.split()[0][1:], line.split()[1]))
			else :
				#print line
				folder = line.split(" ")[-1][1:-2]
#				m = re.match(".*'(.*)'", line)
#				if m :
#					folder = m.group(1)
#					if folder[-1] != '/' :
#						folder += '/'
#				else :
#					log('warning, unkown output of --list-files: ' + line)
		
		return files
	
	
	def take_pictures(self) :

		logFile = datetime.datetime.now().strftime("log/gphoto2_%d%m%Y.log")

		globalvars.bCapturingCamera = True
		pictureTaken = []
		camerasInfo = self.detectCameras()
		#print camerasInfo
		nCameras = len(camerasInfo)
		#print nCameras
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
				
		if ( self.cfg.reset_usb ):
			for i in range(0,nCameras):
	
				usbcamera = "/dev/bus/usb/%s/%s" % (camerasInfo[i][1] , camerasInfo[i][2] )
				#print usbcamera
				os.system( "./usbreset %s" % (usbcamera) )
				
				for i in range(1,100):
					time.sleep(0.1)
					camerasInfo = self.detectCameras()
					if ( len(camerasInfo) == nCameras):
						break
				#print "Resetted after" + str(i)
				
			camerasInfo = self.detectCameras()
			nCameras = len(camerasInfo)
		
		
		#for i in range(0,nCameras,):
		#	log("Camera " + str(i+1) + " : "  + camerasInfo[i][0] + "USB : " + camerasInfo[i][1]  + " " + camerasInfo[i][2]  )

		for i in range(0,nCameras):
			log("Capturing from Camera : %d = %s" %( i+1,camerasInfo[i][0] ) )
			usbcamera = "usb:%s,%s" % (camerasInfo[i][1] , camerasInfo[i][2] )
			filename = "./img/camera" + str(i+1) + "_" + datetime.datetime.now().strftime("%d%m%Y-%H%M%S.jpg") 

			if workaround :
				# this works around --capture-image-and-download not working
				# get rid of any existing files on the card
				for folder, number, _ in self.list_files(usbcamera) :
					self.delete_picture(from_folder = folder)
				
	
				os.system("gphoto2 --port "+ usbcamera + " --capture-image" +  " 1>> " + logFile + " 2>> " + logFile)
	
				os.system("gphoto2 --port " + usbcamera + "  --get-file=1 --filename=%s" % ( filename) +  " 1>> " + logFile + " 2>> " + logFile )
	
			else :
				#print "gphoto2 --port " + usbcamera + "  --capture-image-and-download " + self.cfg.gphoto2options + " --filename %s" % (filename)
				
				os.system("gphoto2 --port " + usbcamera + "  --capture-image-and-download " + gphoto2options[i] + " --filename %s" % (filename) +  " 1>> " + logFile + " 2>> " + logFile )
				#if (  gphoto2options[i]  == "" ):
				#	subprocess.Popen(["/usr/local/bin/gphoto2","--port",usbcamera,"--capture-image-and-download" , "--filename", filename],stdout=file("gphoto2.log","a"),stderr=file("gphoto2.log","a"))
				#else:
				#	subprocess.Popen(["/usr/local/bin/gphoto2","--port",usbcamera,gphoto2options[i] ,"--capture-image-and-download" , "--filename", filename],stdout=file("gphoto2.log","a"),stderr=file("gphoto2.log","a"))

			if ( os.path.isfile(filename)):	
				pictureTaken.append(filename)
				
		globalvars.bCapturingCamera = False
		return pictureTaken
	
	
	def delete_picture(self,usbcamera,from_folder ) :
		
		if from_folder :
			#log(  'from_folder ' + from_folder )
			os.system("gphoto2 --port " + usbcamera + " -D --folder=%s" % from_folder)
			
			return
		return
		# try deleting from all 3 known folders, in the order of most likely
		ret, stdout, stderr = os.system("gphoto2 --port " + usbcamera + " --delete-file=1 --folder=/store_00010001")
		if 'There are no files in folder' in stderr :
			ret, stdout, stderr = os.system("gphoto2 --port " + usbcamera + "  --delete-file=1 --folder=/store_00010001/DCIM/100NIKON")
			if 'There are no files in folder' in stderr :
				ret, stdout, stderr = os.system("gphoto2 --port " + usbcamera + "  --delete-file=1 --folder=/")
		
		return ret
	


def ClearAllCameraSDCards(cfg):
	camera = PhotoCamera(cfg)
	camerasInfo = camera.detectCameras()
	#print "camerasInfo" , camerasInfo
	nCameras = len(camerasInfo)
	
	for i in range(0,nCameras):
		log("Deleting file from " + camerasInfo[i][0] )
		usbcamera = "usb:%s,%s" % (camerasInfo[i][1] , camerasInfo[i][2] )
		
		for folder, number, _ in camera.list_files(usbcamera) :
			#print folder,number
			os.system("gphoto2 --port " + usbcamera + " -D --folder=%s" % folder)
				


if __name__ == '__main__':

	configfile = 'swpi.cfg'
	

	cfg = config.config(configfile)
	
	
	ClearAllCameraSDCards(cfg)
	
	exit(0)

	camera = PhotoCamera(cfg)
	
	camerasInfo = camera.detectCameras()
	#print "camerasInfo" , camerasInfo
	nCameras = len(camerasInfo)
	
	for i in range(0,nCameras):
		log("Deleting file from " + camerasInfo[i][0] )
		usbcamera = "usb:%s,%s" % (camerasInfo[i][1] , camerasInfo[i][2] )
		
		for folder, number, _ in camera.list_files(usbcamera) :
			#print folder,number
			camera.delete_picture(usbcamera,from_folder = folder)
			
		#print usbcamera,camera.list_files(usbcamera)

	
	
	
	
	
	
