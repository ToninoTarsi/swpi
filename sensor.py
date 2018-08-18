
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
from BME280 import *
import re
import rf95

current_milli_time = lambda: int(round(time.time() * 1000))


def log(message) :
	print datetime.datetime.now().strftime("[%d/%m/%Y-%H:%M:%S]") , message

class Sensor(threading.Thread):
	
	def __init__(self ,cfg):
		self.cfg = cfg
		self.implementedStations = ["WH1080-RFM01","WH1080_RTL-SDR","WH3080_RTL-SDR"]
		#self.implementedStations = ["SIMULATE","PCE-FWS20","NEVIO8","NEVIO16","PCE-SENSOR","DAVIS-SENSOR","LACROSS-TX23","WMR100","WMR200","WMR918","WM918","WH1080-RFM01"]
		
#		if ( self.cfg.sensor_type not in self.implementedStations  ):
#			log("Unknown sensor type %s can not continue" % self.cfg.sensor_type)
#			log("Implemented sensors are :")
#			print self.implementedStations
			

		
		if ( self.cfg.use_bmp085 ):
			self.bmp085 = BMP085(0x77,3)  
		else:
			self.bmp085 = None

		if (self.cfg.use_LoRa):
			self.init_LoRa()
		else:
			self.lora = None		
					
		object.__init__(self)
	
	def init_LoRa(self):
		
		self.sending_to_lora = False
		
		self.lora = rf95.RF95(self.cfg.LoRa_spiDev,0, int_pin=None,reset_pin=5)
		if not self.lora.init(): # returns True if found
			log("RF95 not found")
			self.lora = None
			return 
		self.lora.set_frequency(self.cfg.LoRa_frequency)
		self.lora.set_tx_power(self.cfg.LoRa_power)
		self.lora.set_modem_config_simple(getLoRaBWCode(self.cfg.LoRa_BW),
										getLoRaCRCode(self.cfg.LoRa_CR), 
										getLoRaSFCode(self.cfg.LoRa_SF))
		self.lora.sleep()
		log("LoRa 0K (" +str(self.cfg.LoRa_frequency)+ "," + self.cfg.LoRa_BW+","+self.cfg.LoRa_CR+","+self.cfg.LoRa_SF+ "," +self.cfg.LoRa_mode +")" )
	
		
		
	def GetData(self):
		#print "GetData"
		if ( self.cfg.use_bmp085 and self.bmp085 != None ):
			self.ReadBMP085()
			#print "bmp read"
		if ( self.cfg.use_dht ):
			self.ReadDHT()
			#print "dht read"
		if ( self.cfg.use_bme280):
			self.ReadBME280()
		
		globalvars.meteo_data.CalcStatistics()
		globalvars.meteo_data.LogDataToDB()
		
		
		if ( self.cfg.logdata and  globalvars.meteo_data.last_measure_time != None and  globalvars.meteo_data.status == 0 ) :
			log("Logging data ...")
			logData(self.cfg.serverfile,self.cfg.SMSPwd)
			
		if ( self.cfg.WeatherUnderground_logdata and  globalvars.meteo_data.last_measure_time != None and  globalvars.meteo_data.status == 0 ) :
			log("Logging data to Wunderground ...")
			logDataToWunderground(self.cfg.WeatherUnderground_ID,self.cfg.WeatherUnderground_password,self.cfg.wind_speed_units)	
			

		if ( self.cfg.upload_data and  globalvars.meteo_data.last_measure_time != None and  globalvars.meteo_data.status == 0 ) :
			log("Uploading data ...")
			UploadData(self.cfg)		
			
		if ( self.cfg.CWOP_logdata and  globalvars.meteo_data.last_measure_time != None and  globalvars.meteo_data.status == 0 ) : 
			logDataToCWOP(self.cfg.CWOP_ID,self.cfg.CWOP_password,self.cfg.location_latitude,self.cfg.location_longitude)
	
		if ( self.cfg.PWS_logdata and  globalvars.meteo_data.last_measure_time != None and  globalvars.meteo_data.status == 0 ) :
			log("Logging data to PWS ...")
			logDataToPWS(self.cfg.PWS_ID,self.cfg.PWS_password,self.cfg.wind_speed_units)	
			
		if ( self.cfg.WindFinder_logdata and  globalvars.meteo_data.last_measure_time != None and  globalvars.meteo_data.status == 0 ) : 
			sentToWindFinder(self.cfg.WindFinder_ID,self.cfg.WindFinder_password)
		
		
		if (self.cfg.use_LoRa and self.lora != None ):
			thread.start_new_thread(self.SendToLoRaThread,())
	
	def SendToLoRaThread(self):
		self.lora.set_mode_idle()
		if ( self.lora == None):
			log("LoRa : ERROR in initilization ")
			return 
		sended = False
		jstr = CreateLoRaJson(self.cfg)
		start = current_milli_time()
		while ( ( not sended ) and ( current_milli_time()-start) < 40000) :
			sended = self.SendToLoRa(jstr)
			time.sleep(10)
			
		self.lora.sleep()
			
	def checkSendedThread(self):
		start_send = current_milli_time()
		while ( self.sending_to_lora and current_milli_time()-start_send < 2000 ):
			time.sleep(0.1)
		if ( self.sending_to_lora  ):
			log("Lora ERROR: Sending toke more than 2 seconds .. try to reset")
			self.lora.reset()
			time.sleep(0.1)
			self.init_LoRa()
			
	def SendToLoRa(self,jstr):
		try:
			self.sending_to_lora = True
			thread.start_new_thread(self.checkSendedThread,())
			log("LoRa : Sending ... ")
			start_send = current_milli_time()
			self.lora.send(self.lora.str_to_data(jstr))
			self.lora.wait_packet_sent()
			self.sending_to_lora = False
			sent_time = current_milli_time()-start_send
			log("SendToLoRa(" + str(sent_time) + "ms) : "  + str(jstr))
			
			if ( self.cfg.LoRa_mode.upper()[0]  != "B"):
				return True;
			else:						# BIDIRECTIONAL
				count = 0
				while ( count < 20  and not self.lora.available()):
					time.sleep(0.1)
					count = count + 1
				if (self.lora.available() ): 
					data = self.lora.recv()
					rec_str = ""
					for ch in data:
						rec_str = rec_str + chr(ch)
					log ('LoRa ACT (' + str(self.lora.last_rssi) + 'dBm) :' + rec_str)
					str_act = ",".join(("$SWACT",self.cfg.LoRa_ID))
					if ( rec_str == str_act):
						return True
					else:
						return False
				else:
					log ("LoRa : ACT Timeout")
					return False
				
			
			self.lora.set_mode_idle()
			
			
				

		except:
			log("ERROR sending to LoRA")
			return False

		
	def ReadDHT(self):
		
		if ( self.cfg.sensor_type not in self.implementedStations):				
			globalvars.meteo_data.hum_out = None
		else:
			globalvars.meteo_data.hum_in = None	
			
		try:
			if ( self.cfg.dht_type == "DHT11" ) :
				if ( self.cfg.sensor_type not in self.implementedStations):
					output = subprocess.check_output(["./DHT/DHT"])
				else:
					output = subprocess.check_output(["./DHT/DHT_rf","11","18"])
			else:
				if ( self.cfg.sensor_type not in self.implementedStations):
					output = subprocess.check_output(["./DHT/DHT","22"])
				else:
					output = subprocess.check_output(["./DHT/DHT_rf","22","18"])
			#print output
			matches = re.search("Temp =\s+([0-9.]+)", output) 
			#matches = re.search("Temp\s*=\s*(-?[\d.]+)", output) # Alessandro
			if ( matches):
				dht_temp = float(matches.group(1))
				if ( self.cfg.sensor_type not in self.implementedStations ):
					if ( self.cfg.use_bmp085 ):
						if ( self.cfg.sensor_temp_in == "Default"):
							globalvars.meteo_data.temp_in = dht_temp
					else:
						if ( self.cfg.sensor_temp_out == "Default"):
							globalvars.meteo_data.temp_out = dht_temp
				else:
					if ( not self.cfg.use_bmp085 ):
						if ( self.cfg.sensor_temp_in == "Default"):
							globalvars.meteo_data.temp_in = dht_temp

						
				if ( self.cfg.sensor_temp_out == "DHT"):
						globalvars.meteo_data.temp_out = dht_temp	
				if ( self.cfg.sensor_temp_in == "DHT"):
						globalvars.meteo_data.temp_in = dht_temp				
			
			# search for humidity printout
			matches = re.search("Hum =\s+([0-9.]+)", output)
			if ( matches):
				dht_hum = float(matches.group(1))
				if ( self.cfg.sensor_type not in self.implementedStations):				
					globalvars.meteo_data.hum_out = dht_hum
				else:
					globalvars.meteo_data.hum_in = dht_hum
						
			log("DHT - Temperature: %.1f C Humidity:    %.1f " % (dht_temp, dht_hum) )
		
		except:
			log("ERROR reading DHT sensor")
			
	def ReadBMP085(self):
		try:
			p=0.0
			temp = None
			i = 0
			while ( p==0.0 and i < 10):
				i = i+1
				p,temp = self.bmp085.readPressureTemperature()
				if p == 0.0 :
					time.sleep(0.5)
					
			if ( p != None )  :  
				abs_pressure = float(p / 100.0) 
				globalvars.meteo_data.abs_pressure =  abs_pressure
				
				
				if ( self.cfg.sensor_type in self.implementedStations):
					if ( self.cfg.sensor_temp_in == "Default"):
						globalvars.meteo_data.temp_in = temp
				else:
					if ( self.cfg.sensor_temp_out == "Default"):
						globalvars.meteo_data.temp_out = temp

				if ( self.cfg.sensor_temp_out == "BMP085"):
						globalvars.meteo_data.temp_out = temp	
				if ( self.cfg.sensor_temp_in == "BMP085"):
						globalvars.meteo_data.temp_in = temp	
				
				log("BMP085 - Temperature: %.1f C Pressure:    %.1f " % (temp, abs_pressure) )
				
			else:
				globalvars.meteo_data.abs_pressure = None
				
				if ( self.cfg.sensor_type in self.implementedStations):
					globalvars.meteo_data.temp_in = None
				else:
					globalvars.meteo_data.temp_out = None		
				return
			


		except:
			globalvars.meteo_data.abs_pressure = None
			if ( self.cfg.sensor_type in self.implementedStations):
				globalvars.meteo_data.temp_in = None
			else:
				globalvars.meteo_data.temp_out = None
			log("ERROR reading BMP085 sensor")

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
				
	def ReadBME280(self):
		try:
			p=0.0
			temp = None
			i = 0
			sensor = BME280()
			while ( p==0.0 and i < 10):
				i = i+1
				temp = sensor.read_temperature()
				p = sensor.read_pressure()
				#p = pascals / 100
				humidity = sensor.read_humidity()
				#globalvars.meteo_data.hum_out = humidity
				if (self.cfg.sensor_type not in self.implementedStations):
					globalvars.meteo_data.hum_out = humidity
				else:
					globalvars.meteo_data.hum_in = humidity
				
				#p,temp = self.bmp085.readPressureTemperature()
				if p == 0.0 :
					time.sleep(0.5)
					
			if ( p != None )  :  
				abs_pressure = float(p / 100.0) 
				globalvars.meteo_data.abs_pressure =  abs_pressure
				
				
				if ( self.cfg.sensor_type in self.implementedStations):
					if ( self.cfg.sensor_temp_in == "Default"):
						globalvars.meteo_data.temp_in = temp
				else:
					if ( self.cfg.sensor_temp_out == "Default"):
						globalvars.meteo_data.temp_out = temp

				if ( self.cfg.sensor_temp_out == "BMP085"):
						globalvars.meteo_data.temp_out = temp	
				if ( self.cfg.sensor_temp_in == "BMP085"):
						globalvars.meteo_data.temp_in = temp	
				
				log("BME280 - Temperature: %.1f C Pressure:    %.1f humidity %.0f" % (temp, abs_pressure,humidity) )
				
			else:
				globalvars.meteo_data.abs_pressure = None
				
				if ( self.cfg.sensor_type in self.implementedStations):
					globalvars.meteo_data.temp_in = None
				else:
					globalvars.meteo_data.temp_out = None		
				return
			


		except:
			globalvars.meteo_data.abs_pressure = None
			if ( self.cfg.sensor_type in self.implementedStations):
				globalvars.meteo_data.temp_in = None
			else:
				globalvars.meteo_data.temp_out = None
			log("ERROR reading BMP280 sensor")

	def ReadBME280_temp_in(self):
		p=0.0
		temp = None
		i = 0
		sensor = BME280()
		while ( p==0.0 and i < 10):
			temp = sensor.read_temperature()
			p = sensor.read_pressure()
			#p = pascals / 100
			humidity = sensor.read_humidity()
			globalvars.meteo_data.hum_out = humidity
			#p,temp = self.bmp085.readPressureTemperature()
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
 
