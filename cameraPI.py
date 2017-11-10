###########################################################################
#     Sint Wind PI
# 	  Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################
"""Classes and methods for handling cameraPI commands."""

import sqlite3
import Image
import ImageFont
import ImageDraw
import time
import os
from TTLib  import *
import sun
import math
import subprocess

class cameraPI(object):
	"""Class defining generic webcams."""

	def __init__(self, cfg):
		self.cfg = cfg
		self.god=sun.sun(lat=cfg.location_latitude,long=cfg.location_longitude)
	
	def detect_cameraPI(self):
		cmd = ['vcgencmd', 'get_camera']
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.PIPE)
		out, err = p.communicate('foo\nfoofoo\n')
		if ( out.find("detected=1") == -1  ) :
			return False
		else:
			return True
		
	def capture(self,filename):
		if ( not self.detect_cameraPI() ) :
			log("ERROR CameraPI not detected")
			return False
		if ( self.god.daylight() ):
			options = self.cfg.cameraPI_day_settings
			log("CameraPI - Using Dayligth settings" + options)
		else:
			options = self.cfg.cameraPI_night_settings
			log("CameraPI - Using Nigth settings" + options)
		try:
			if options.upper() == "NONE":
				log("CameraPI not active")
				return False
			snapCommand = "raspistill  %s -o %s" %  (options,filename)
			#log( "Getting images with command : " + snapCommand)
			os.system(snapCommand )

			if ( not os.path.isfile(filename)):
				log( "ERROR in capturing cameraPI "  )
				return False
					
			return True
		except ValueError:
			log( " ERROR in capturing cameraPI  " + e )
			return False

