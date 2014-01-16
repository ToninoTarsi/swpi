###########################################################################
#	 Sint Wind PI
#	 Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#	 Please refer to the LICENSE file for conditions 
#	 Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""This module defines the base sensor Nevio ."""

import threading
import time
import config
import random
import datetime
import sqlite3
from TTLib import *
import TTLib
import sys
import subprocess
import globalvars
import meteodata
import sensor_thread
import sensor 
import RPi.GPIO as GPIO
import TTLib
import thread
import os

DEBUG = False



def log(message) :
	print datetime.datetime.now().strftime("[%d/%m/%Y-%H:%M:%S]") , message

def modification_date(filename):
	try:
		t = os.path.getmtime(filename)
		return datetime.datetime.fromtimestamp(t)
	except:
		return None

def getrevision():
	# Extract board revision from cpuinfo file
	myrevision = "0000"
	try:
		f = open('/proc/cpuinfo','r')
		for line in f:
			if line[0:8]=='Revision':
				myrevision = line[11:-1]
		f.close()
	except:
		myrevision = "0000"
	
	return myrevision

def get_wind_dir_code8():
	return [ 'N','NW','NE', 'E', 'SW' , 'W',  'S' , 'SE' ]

def get_wind_dir8():
	return [ 0,315,45,90,225,270,180,135 ]


def get_wind_dir_code16():
	return [ 'N','NNE','NNW','NW','ENE','NE','E','ESE','WSW','SW','W','WNW','S','SSW','SSE','SE' ]


def get_wind_dir16():
	return [ 0,22.5,337.5,315,67.5,45,90,112.5,247.5,225,270,292.5,180,202.5,157.5,135 ]


class Sensor_WH1080RF(sensor.Sensor):
	

	
	def __init__(self,cfg ):
		
		threading.Thread.__init__(self)

		sensor.Sensor.__init__(self,cfg )		
		
		self.cfg = cfg
		
		try:
			os.remove('./wh1080_rf.txt')			
		except:
			log("Warning could not delete wh1080_rf.txt file")

		self.active = True
		self.start()
	
	def startRFListenig(self):
		cmd = "./wh1080_rf/wh1080_rf -f %d -r %d -l %d -b %d > /dev/null" % (self.cfg.rfm01_frequenzy,self.cfg.rfm01_rssi,self.cfg.rfm01_lna,self.cfg.rfm01_band)
		os.system(cmd)
	
	def run(self):
		myrevision = getrevision()
		if myrevision == "0002" or myrevision == "0003" :
			s = 1
		else:
			s = 2
		log("Starting RF listening")
		cmd = "./wh1080_rf/wh1080_rf -f %d -r %d -l %d -b %d -s %d > /dev/null" % (self.cfg.rfm01_frequenzy,self.cfg.rfm01_rssi,self.cfg.rfm01_lna,self.cfg.rfm01_band,s)
		#print cmd
		os.system(cmd)
		log("Something wrong with  RF ... restarting")


	def Detect(self):
		return True
	
	def ReadData(self):
		try:
#			in_file = open("./wh1080_rf.txt","r")
#			text = in_file.read().splitlines()
#			in_file.close()

			text = os.popen("cat ./wh1080_rf.txt").read().splitlines()
			#print text
			station_id = text[0].split(",")[1]
			#print "station_id ",station_id
			if ( station_id  == "None" ):
				return "None",0,0,0,0,"",0,0
			temp = float(text[1].split(",")[1])
			hum = float(text[1].split(",")[3])
			Wind_speed = float(text[2].split(",")[1])*self.cfg.windspeed_gain + self.cfg.windspeed_offset
			Gust_Speed = float(text[2].split(",")[3])*self.cfg.windspeed_gain + self.cfg.windspeed_offset
			dir_code = (text[2].split(",")[4])
			dire = int(text[2].split(",")[5])
			rain = float(text[3].split(",")[1])
			return station_id,temp,hum,Wind_speed,Gust_Speed,dir_code,dire,rain
		except:
			if DEBUG: print "DEBUG - Error in ReadData"
			return "None",0,0,0,0,"",0,0

	def GetData(self):
		
		# get first good data
		good_data = False
		while ( not os.path.exists('./wh1080_rf.txt')  ):
			if DEBUG: print "DEBUG - not exist ./wh1080_rf.txt "
			time.sleep(5)
		while ( not good_data ):
			station_id,temp,hum,Wind_speed,Gust_Speed,dir_code,dire,rain =  self.ReadData()
			if ( station_id != "None"):
				good_data = True
			else:
				log("Bad data received from RFM01 ")
				time.sleep(48)
		log("First data received from RFM01 station %s .. processing" % station_id)
		last_data_time = modification_date('./wh1080_rf.txt')
		
		
		
		while 1:
			if ( station_id != "None" ):
				globalvars.meteo_data.status = 0
				globalvars.meteo_data.last_measure_time = last_data_time
				globalvars.meteo_data.idx = globalvars.meteo_data.last_measure_time
				globalvars.meteo_data.hum_out = hum
				globalvars.meteo_data.temp_out = temp
				globalvars.meteo_data.wind_ave	 = Wind_speed
				globalvars.meteo_data.wind_gust	= Gust_Speed
				globalvars.meteo_data.wind_dir = dire*22.5
				globalvars.meteo_data.wind_dir_code = dir_code
				globalvars.meteo_data.rain = rain
	
				sensor.Sensor.GetData(self)
			
			
			tosleep = 50-(datetime.datetime.now()-last_data_time).seconds
			if DEBUG: print "Sleeping  ", tosleep
			if (tosleep > 0 and tosleep < 50 ):	
				time.sleep(tosleep)
			else:
				time.sleep(50)
			
			new_last_data_time = modification_date('./wh1080_rf.txt')
			while ( new_last_data_time == None or new_last_data_time == last_data_time):
				time.sleep(10)
				new_last_data_time = modification_date('./wh1080_rf.txt')
				
				
			log("New data received from RFM01 station %s .. processing" % station_id)
			last_data_time = new_last_data_time
						
			station_id,temp,hum,Wind_speed,Gust_Speed,dir_code,dire,rain =  self.ReadData()
			
			if ( station_id == "None"):
				log("Bad data received from RFM01 ")



if __name__ == '__main__':

	configfile = 'swpi.cfg'
	
	cfg = config.config(configfile)
	
	globalvars.meteo_data = meteodata.MeteoData(cfg)

	ss = Sensor_WH1080RF(cfg)
	
	while 1:
		ss.GetData()
	