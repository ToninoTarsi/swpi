###########################################################################
#	 Sint Wind PI
#	 Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#	 Please refer to the LICENSE file for conditions 
#	 Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""This module defines the base sensors Sensor_WS2300 ."""


import threading
import time
import config
import random
import datetime
import sqlite3
import sys
import subprocess
import globalvars
import meteodata
import sensor_thread
import sensor
from TTLib import *
import logging
import platform
import datetime
import serial
import string
import ws2300
import serial


def log(message) :
	print datetime.datetime.now().strftime("[%d/%m/%Y-%H:%M:%S]") , message

windDirMap = { 0:"N", 1:"NNE", 2:"NE", 3:"ENE", 4:"E", 5:"ESE", 6:"SE", 7:"SSE",
			  8:"S", 9:"SSW", 10:"SW", 11:"WSW", 12:"W", 13:"WNW", 14:"NW", 15:"NWN" }

def get_wind_dir_text():
	"""Return an array to convert wind direction integer to a string."""
	return ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW','N']


class Sensor_WS2300(sensor.Sensor):
	'''
	Station driver for the Oregon Scientific WS2300.
	'''
	def __init__(self,cfg ):
		self.cfg = cfg

	def GetData(self):	 
		log("Thread started")
		
		#print "GetData"
		serialPort = ws2300.LinuxSerialPort(self.cfg.sensor_serial_port)
		#print serialPort
		#print "opened"
		
		ws = ws2300.Ws2300(serialPort)
		
		measures = [
			ws2300.Measure.IDS["pa"],  # pressure absolute
			ws2300.Measure.IDS["it"],  # in temp
			ws2300.Measure.IDS["ih"],  # in humidity
			ws2300.Measure.IDS["ot"],  # out temp"
			ws2300.Measure.IDS["oh"],  # out humidity"
			ws2300.Measure.IDS["rt"],  # rain total 
			ws2300.Measure.IDS["ws"],  # "wind speed"
			ws2300.Measure.IDS["w0"],  # "wind direction"
			ws2300.Measure.IDS["ws"],  # "wind speed gust ???"
			ws2300.Measure.IDS["wsu"],  # wind speed units
			#ws2300.Measure.IDS["rh"],  # rain 1h
			#ws2300.Measure.IDS["wsh"], # "wind speed max ??????????????"
			]		
		
		
		while True:
			
			seconds = datetime.datetime.now().second
			if ( seconds < 30 ):
				time.sleep(30-seconds)
			else:
				time.sleep(90-seconds)
		
			try:

				raw_data = ws2300.read_measurements(ws, measures)
				
				data = [ m.conv.binary2value(d) for m, d in zip(measures, raw_data)]
	
				print "***************DUBUG********************"
				print data
				print "***************DUBUG********************"

				globalvars.meteo_data.status = 0
				globalvars.meteo_data.last_measure_time = datetime.datetime.now()
				globalvars.meteo_data.idx = globalvars.meteo_data.last_measure_time
				
				globalvars.meteo_data.abs_pressure = float(data[0])
				globalvars.meteo_data.temp_in = float(data[1])
				globalvars.meteo_data.hum_in = float(data[2])
				globalvars.meteo_data.temp_out = float(data[3])
				globalvars.meteo_data.hum_out = float(data[4])
				globalvars.meteo_data.rain = float(data[5])
				globalvars.meteo_data.wind_ave = (float(data[6])*1.609344)*self.cfg.windspeed_gain + self.cfg.windspeed_offset
				globalvars.meteo_data.wind_gust = (float(data[8])*1.609344)*self.cfg.windspeed_gain + self.cfg.windspeed_offset
				
				wind_dir = data[7]
				globalvars.meteo_data.wind_dir = wind_dir
				
				val=int((wind_dir/22.5)+.5)
				globalvars.meteo_data.wind_dir_code = get_wind_dir_text()[val]
				
				
				globalvars.meteo_data.illuminance = None
				globalvars.meteo_data.uv = None			   
					
				sensor.Sensor.GetData(self)				 

					
			except Exception, err:
				print sys.exc_info()[0]
				log("ERROR with WS2300  %s "  % err)
				
		serialPort.close()
				
				
	
if __name__ == '__main__':
	"""Main only for testing"""
	configfile = 'swpi.cfg'
	
	cfg = config.config(configfile)	
	
	globalvars.meteo_data = meteodata.MeteoData(cfg)
	ws = Sensor_WS2300(cfg)
	ws.GetData()
	
