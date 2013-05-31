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

class cameraPI(object):
	"""Class defining generic webcams."""

	def __init__(self, cfg):
		self.cfg = cfg
		self.god=sun.sun(lat=cfg.location_latitude,long=cfg.location_longitude)
	
	def capture(self,filename):
		if ( self.god.daylight() ):
			options = self.cfg.cameraPI_day_settings
			log("CameraPI - Using Dayligth settings" + options)
		else:
			options = self.cfg.cameraPI_night_settings
			log("CameraPI - Using Nigth settings" + options)
		try:
			snapCommand = "raspistill -hf %s -o %s" %  (options,filename)
			#log( "Getting images with command : " + snapCommand)
			os.system(snapCommand )

			if ( not os.path.isfile(filename)):
				log( "ERROR in capturing webcam image on : " + self.device )
				return False
					
			return True
		except ValueError:
			log( " ERROR in capturing cameraPI image on : " + self.device )
			return False

