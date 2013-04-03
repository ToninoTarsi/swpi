
###########################################################################
#	 Sint Wind PI
#	 Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#
#	 Please refer to the LICENSE file for conditions 
#	 Visit http://www.vololiberomontecucco.it
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
from BMP085 import BMP085
import re



class Sensor(threading.Thread):
	
	def __init__(self ,cfg):
		self.cfg = cfg
		#self.implementedStations = ["SIMULATE","PCE-FWS20","NEVIO8","NEVIO16","PCE-SENSOR","DAVIS-SENSOR","LACROSS-TX23","WMR100","WMR200","WMR918","WM918","WH1080-RFM01"]
		
#		if ( self.cfg.sensor_type not in self.implementedStations  ):
#			log("Unknown sensor type %s can not continue" % self.cfg.sensor_type)
#			log("Implemented sensors are :")
#			print self.implementedStations
			
		if ( self.cfg.use_bmp085 ):
			self.bmp085 = BMP085(0x77,3)  
		else:
			self.bmp085 = None

		object.__init__(self)
		
	def GetData(self):
		#print "GetData"
		if ( self.cfg.use_bmp085 and self.bmp085 != None ):
			self.ReadBMP085()
			
		if ( self.cfg.use_dht ):
			self.ReadDHT()

		globalvars.meteo_data.CalcStatistics()
		globalvars.meteo_data.LogDataToDB()
		
		
	def ReadDHT(self):
		try:
			if ( self.cfg.dht_type == "DHT11" ) :
				output = subprocess.check_output(["./DHT/DHT"]);
			else:
				output = subprocess.check_output(["./DHT/DHT","22"]);
			#print output
			matches = re.search("Temp =\s+([0-9.]+)", output)
			if ( matches):
				if ( self.cfg.use_bmp085 ):
					globalvars.meteo_data.temp_in = float(matches.group(1))
				else:
					globalvars.meteo_data.temp_out = float(matches.group(1))
			
			# search for humidity printout
			matches = re.search("Hum =\s+([0-9.]+)", output)
			if ( matches):
				globalvars.meteo_data.hum_out = float(matches.group(1))

			#print "Temperature: %.1f C Humidity:    %.1f " % (globalvars.meteo_data.temp_in , globalvars.meteo_data.hum_out)
		except:
			log("Error reading DHT sensor")
		
	def ReadBMP085(self):
		p=0.0
		temp = None
		i = 0
		while ( p==0.0 and i < 10):
			p,temp = self.bmp085.readPressureTemperature()
			i = i+1
			if p == 0.0 :
				time.sleep(0.5)
				
		if ( p != None )  :  
			globalvars.meteo_data.abs_pressure =  float(p / 100.0) 
		else:
			globalvars.meteo_data.abs_pressure = None
		
		if ( self.cfg.sensor_type == "WH1080-RFM01"):
			globalvars.meteo_data.temp_in = temp
		else:
			globalvars.meteo_data.temp_out = temp


#		if ( p == None):
#			globalvars.meteo_data.temp_out = None
#			globalvars.meteo_data.abs_pressure = None
#		elif ( p != 0.0): 
#			if ( self.cfg.location_altitude != 0 ):
#				p0 = p / pow( 1 - (0.225577000e-4*self.cfg.location_altitude ),5.25588 )
#			else:
#				p0 = p
#			globalvars.meteo_data.rel_pressure = float(p0 / 100.0)
				
	def ReadBMP085_temp_in(self):
		p=0.0
		temp = None
		i = 0
		while ( p==0.0 and i < 10):
			p,temp = self.bmp085.readPressureTemperature()
			i = i+1
			time.sleep(0.02)
			
		if ( p != None )  :  
			globalvars.meteo_data.abs_pressure =  float(p / 100.0) 
		else:
			globalvars.meteo_data.abs_pressure = None 
		
		
		globalvars.meteo_data.temp_in = temp

#		if ( p == None):
#			globalvars.meteo_data.temp_out = None
#			globalvars.meteo_data.abs_pressure = None
#		elif ( p != 0.0): 
#			if ( self.cfg.location_altitude != 0 ):
#				p0 = p / pow( 1 - (0.225577000e-4*self.cfg.location_altitude ),5.25588 )
#			else:
#				p0 = p
#			globalvars.meteo_data.rel_pressure = float(p0 / 100.0)
				
			
	def _report_rain(self,total, rate):
		#print "report_rain",total, rate
		globalvars.meteo_data.rain = total
 
			
			
	def _report_wind(self,dir, dirDeg, dirStr, gustSpeed, avgSpeed):
		#print "report_wind",dirDeg, avgSpeed, gustSpeed	  
		globalvars.meteo_data.wind_ave	 = avgSpeed
		globalvars.meteo_data.wind_gust	= gustSpeed
		globalvars.meteo_data.wind_dir	 = dirDeg
		globalvars.meteo_data.wind_dir_code = dirStr
		
#		globalvars.meteo_data.CalcStatistics()
#		globalvars.meteo_data.LogDataToDB()

	def _report_barometer_absolute(self,pressure):
		globalvars.meteo_data.abs_pressure = pressure

	def _report_temperature(self,temp, humidity, sensor):
		if ( sensor == 1 ) :
			globalvars.meteo_data.hum_out  = humidity   
			globalvars.meteo_data.temp_out   = temp	  
		elif( sensor == 0 ):
			globalvars.meteo_data.hum_in  = humidity   
			globalvars.meteo_data.temp_in   = temp	 

	def _report_temperature_inout(self,temp_in, temp_out):
		globalvars.meteo_data.temp_out   = temp_out	  
		globalvars.meteo_data.temp_in   = temp_in	

	def _report_humidity(self, hum_in, hum_out):
		globalvars.meteo_data.hum_out  = hum_out   
		globalvars.meteo_data.hum_in  = hum_in   
  
								
	def _report_uv(self,uv):
		globalvars.meteo_data.uv = uv	
		
		
	def _logData(self):
		#print "_logData" 
#		if ( globalvars.meteo_data.last_measure_time != None):
#			print (datetime.datetime.now()-globalvars.meteo_data.last_measure_time).seconds
		if ( globalvars.meteo_data.last_measure_time == None or (datetime.datetime.now()-globalvars.meteo_data.last_measure_time).seconds >= 60 ) :   
			globalvars.meteo_data.status = 0
			globalvars.meteo_data.last_measure_time = datetime.datetime.now()
			globalvars.meteo_data.idx = globalvars.meteo_data.last_measure_time 
			print "_logData1"
			super().GetData()				  
 