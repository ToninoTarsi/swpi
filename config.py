###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################
"""Classes and methods for handling configurationn file."""

import sys
import struct
import ConfigParser
import sqlite3
import os
import ftplib
import Image
import ImageFont, ImageDraw, ImageOps
import urllib2
import time

def str2bool(v):
	return str(v).lower() in ("yes", "true", "t", "1")

class myConfigParser(ConfigParser.SafeConfigParser):
	"""Class extendig  ConfigParser."""

	def __init__(self,verbose=False):
		self.verbose = verbose
		ConfigParser.SafeConfigParser.__init__(self)


	def setboolean(self,section, option,value):
		if ( not ConfigParser.SafeConfigParser.has_section(self,section) ):
			ConfigParser.SafeConfigParser.add_section(self,section)
		if str2bool(value):
			ConfigParser.SafeConfigParser.set(self,section, option,"True")
		else:
			ConfigParser.SafeConfigParser.set(self,section, option,"False")

	def setstr(self,section, option,value):
		if ( not ConfigParser.SafeConfigParser.has_section(self,section) ):
			ConfigParser.SafeConfigParser.add_section(self,section)
		ConfigParser.SafeConfigParser.set(self,section, option,value)	

	def setint(self,section, option,value):
		if ( not ConfigParser.SafeConfigParser.has_section(self,section) ):
			ConfigParser.SafeConfigParser.add_section(self,section)
		ConfigParser.SafeConfigParser.set(self,section, option,str(value))		

	def setfloat(self,section, option,value):
		if ( not ConfigParser.SafeConfigParser.has_section(self,section) ):
			ConfigParser.SafeConfigParser.add_section(self,section)
		ConfigParser.SafeConfigParser.set(self,section, option,str(value))	

	def get(self,section, option,default="None"):
		if ( not ConfigParser.SafeConfigParser.has_section(self,section) ):
			ConfigParser.SafeConfigParser.add_section(self,section)
		try:
			ret = ConfigParser.SafeConfigParser.get(self,section, option)
			if ( self.verbose ): print "Config : " + section + "-" + option + " : " +  ret
			return ret
		except:
			ConfigParser.SafeConfigParser.set(self,section, option,default)
			if ( self.verbose ): print "Config : " + section + "-" + option + " : " +  default
			return default

	def getboolean(self,section, option,default=False):
		if ( not ConfigParser.SafeConfigParser.has_section(self,section) ):
			ConfigParser.SafeConfigParser.add_section(self,section)
			
		try:
			return ConfigParser.SafeConfigParser.getboolean(self,section, option)
		except:
			ConfigParser.SafeConfigParser.set(self,section, option,str(default))
			return default
		
	def getint(self,section, option,default=0):
		if ( not ConfigParser.SafeConfigParser.has_section(self,section) ):
			ConfigParser.SafeConfigParser.add_section(self,section)
			
		try:
			return ConfigParser.SafeConfigParser.getint(self,section, option)
		except:
			ConfigParser.SafeConfigParser.set(self,section, option,str(default))
			return default
			
	def getfloat(self,section, option,default=0):
		if ( not ConfigParser.SafeConfigParser.has_section(self,section) ):
			ConfigParser.SafeConfigParser.add_section(self,section)
			
		try:
			return ConfigParser.SafeConfigParser.getfloat(self,section, option)
		except:
			ConfigParser.SafeConfigParser.set(self,section, option,str(default))
			return default


class config(object):
	"""Class defining software configuration."""
	def __init__(self, filename,verbose=False):
		
		self.cfgName = filename
		self.readCfg(verbose)
		
	def readCfg(self,verbose=False):
		
		config = myConfigParser(verbose)
		
		if (  os.path.isfile(self.cfgName) ):
			config.read(self.cfgName)

		#[General]
		self.config_web_server = config.getboolean('General', 'config_web_server',True)
		self.config_web_server_port = config.getint('General', 'config_web_server_port',80)
		self.set_system_time_from_ntp_server_at_startup = config.getboolean('General', 'set_sistem_time_from_ntp_server_at_startup',True)
		self.ntp_server = config.get('General', 'ntp_server',"europe.pool.ntp.org")
		self.reboot_at = config.get('General', 'reboot_at',"None")
		self.shutdown_at = config.get('General', 'shutdown_at',"None")
		self.shutdown_hour_before_sunset = config.get('General', 'shutdown_hour_before_sunset',"None")
		self.location_latitude = config.getfloat('General', 'location_latitude',43.351983)
		self.location_longitude = config.getfloat('General', 'location_longitude',12.743187)
		self.location_altitude = config.getfloat('General', 'location_altitude',0)
		self.wifi_reset_if_down = config.getboolean('General', 'wifi_reset_if_down',True)

		# [Dongle]
		self.usedongle = config.getboolean('Dongle', 'usedongle',False)
		self.AlwaysOnInternet = config.getboolean('Dongle', 'alwaysoninternet',True)
		self.dongleCtrlPort = config.get('Dongle', 'dongleCtrlPort',"/dev/ttyUSB2")
		self.dongleAudioPort = config.get('Dongle', 'dongleAudioPort',"/dev/ttyUSB1")
		self.dongleDataPort = config.get('Dongle', 'dongleDataPort',"/dev/ttyUSB0")
		self.UseDongleNet = config.getboolean('Dongle', 'UseDongleNet',False)
		self.operator = config.get('Dongle', 'operator',"tim")
		self.prober_timeout = config.getfloat('Dongle', 'prober_timeout',2)
		self.modem_baudrate = config.getint('Dongle', 'modem_baudrate',460800)
		self.audio_baudrate = config.getint('Dongle', 'audio_baudrate',115200)
		self.ctrl__baudrate = config.getint('Dongle', 'ctrl__baudrate',9600)
		self.dialnum = config.get('Dongle', 'dialnum',"*99#")
		self.pppd_path = config.get('Dongle', 'pppd_path',"/usr/sbin/pppd")

		#[Security]
		self.SMSPwd = config.get('Security', 'SMSPwd',"admin")

		#[DataLogging]
		self.logdata = config.getboolean('DataLogging', 'logdata',False)
		self.serverfile = config.get('DataLogging', 'serverfile',"http://www.yoursite.it/swpi_logger.php")

		#[Upload]
		self.upload_data = config.getboolean('Upload', 'upload_data',False)
		self.upload_folder = config.get('Upload', 'upload_folder',"yoursite.it/folder")

		# [Sensors]
		self.sensor_type = config.get('Sensors', 'sensor_type',"SIMULATE")
		self.use_wind_sensor = config.getboolean('Sensors', 'use_wind_sensor',True)
		self.number_of_measure_for_wind_dir_average =  config.getint('Sensors', 'number_of_measure_for_wind_dir_average',10)
		self.windspeed_offset = config.getfloat('Sensors', 'windspeed_offset',0)
		self.windspeed_gain = config.getfloat('Sensors', 'windspeed_gain',1)
		self.windmeasureinterval = config.getint('Sensors', 'windmeasureinterval',5)
		self.use_bmp085 = config.getboolean('Sensors', 'use_bmp085',False)
		self.use_tmp36 = config.getboolean('Sensors', 'use_tmp36',False)
		self.number_of_measure_for_wind_average_gust_calculation =  config.getint('Sensors', 'number_of_measure_for_wind_average_gust_calculation',10)

		# [Sensor_PCE-FWS20]
		self.set_system_time_from_WeatherStation = config.getboolean('Sensor_PCE-FWS20', 'set_system_time_from_WeatherStation',False)

		# [Sensor_NEVIO8-16]

		#[WebCam]
		self.webcamDevice1 = config.get('WebCam', 'webcamDevice1',"None")
		self.webcamDevice2 = config.get('WebCam', 'webcamDevice2',"None")
		self.webcamLogo = config.get('WebCam', 'webcamLogo',"www.yoursite.com - 333000000")
		self.sendImagesToServer = config.getboolean('WebCam', 'sendImagesToServer',False)
		self.WebCamInterval = config.getint('WebCam', 'WebCamInterval',600)
		self.webcamdevice1captureresolution = config.get('WebCam', 'webcamdevice1captureresolution',"640x480")
		self.webcamdevice2captureresolution = config.get('WebCam', 'webcamdevice2captureresolution',"640x480")
		self.webcamdevice1finalresolution = config.get('WebCam', 'webcamdevice1finalresolution',"640x480")
		self.webcamdevice2finalresolution = config.get('WebCam', 'webcamdevice2finalresolution',"640x480")
		self.capturewithffmpeg = config.getboolean('WebCam', 'capturewithffmpeg',True)
		self.sendallimagestoserver = config.getboolean('WebCam', 'sendallimagestoserver',False)
		self.delete_images_on_sd = config.getboolean('WebCam', 'delete_images_on_sd',False)

		self.webcamdevice1captureresolutionX = int(self.webcamdevice1captureresolution.split('x')[0])
		self.webcamdevice1captureresolutionY = int(self.webcamdevice1captureresolution.split('x')[1])
		self.webcamdevice1finalresolutionX = int(self.webcamdevice1finalresolution.split('x')[0])
		self.webcamdevice1finalresolutionY = int(self.webcamdevice1finalresolution.split('x')[1])		
		self.webcamdevice2captureresolutionX = int(self.webcamdevice2captureresolution.split('x')[0])
		self.webcamdevice2captureresolutionY = int(self.webcamdevice2captureresolution.split('x')[1])
		self.webcamdevice2finalresolutionX = int(self.webcamdevice2finalresolution.split('x')[0])
		self.webcamdevice2finalresolutionY = int(self.webcamdevice2finalresolution.split('x')[1])
		
		#[Camera]
		self.usecameradivice = config.getboolean('Camera', 'usecameradivice',True)
		self.cameradivicefinalresolution = config.get('Camera', 'cameradivicefinalresolution',"800x600")
		self.gphoto2options = config.get('Camera', 'gphoto2options',",,,,,,,,,,")
		self.reset_usb = config.getboolean('Camera', 'reset_usb',False)
		self.clear_all_sd_cards_at_startup = config.getboolean('Camera', 'clear_all_sd_cards_at_startup',True)
		self.start_camera_number = config.getint('Camera', 'start_camera_number',1)
		self.gphoto2_capture_image_and_download = config.getboolean('Camera', 'gphoto2_capture_image_and_download',True)
		self.use_camera_resetter = config.getboolean('Camera', 'use_camera_resetter',False)



		self.cameradivicefinalresolutionX = int(self.cameradivicefinalresolution.split('x')[0])
		self.cameradivicefinalresolutionY = int(self.cameradivicefinalresolution.split('x')[1])
						
		# [ftp]
		self.ftpserver = config.get('ftp', 'ftpserver',"ftp.yoursite.it")
		self.ftpserverDestFolder = config.get('ftp', 'ftpserverDestFolder',"yoursite.it/img")
		self.ftpserverLogin = config.get('ftp', 'ftpserverLogin',"xxxxxxxxx")
		self.ftpserverPassowd = config.get('ftp', 'ftpserverPassowd',"xxxxxxxxxx")
		self.use_thread_for_sending_to_server = config.getboolean('ftp', 'use_thread_for_sending_to_server',False)

		# [Radio]
		self.useradio = config.getboolean('Radio', 'useradio',False)
		self.radiointerval = config.getint('Radio', 'radiointerval',900)

		# [Mail]
		self.gmail_user = config.get('Mail', 'gmail_user',"sintwindpi@gmail.com")
		self.gmail_pwd = config.get('Mail', 'gmail_pwd',"raspberrypi")
		self.mail_to = config.get('Mail', 'mail_to',"yourmail@gmail.com")
		self.use_mail = config.getboolean('Mail', 'use_mail',False)
		self.mail_ip = config.getboolean('Mail', 'mail_ip',True)

		# [SMS]
		self.send_IP_by_sms = config.getboolean('SMS', 'send_IP_by_sms',False)
		self.number_to_send = config.get('SMS', 'number_to_send',"+393330000000")

		#[WeatherUnderground]
		self.WeatherUnderground_logdata = config.getboolean('WeatherUnderground', 'WeatherUnderground_logdata',False)
		self.WeatherUnderground_ID = config.get('WeatherUnderground', 'WeatherUnderground_ID',"KCASANFR5")
		self.WeatherUnderground_password = config.get('WeatherUnderground', 'WeatherUnderground_password',"XXXXXXXX")

		f = open(self.cfgName,"w")
		config.write(f)					


	def writeCfg(self):

		config = myConfigParser()
		
		#[General]
		config.setboolean('General', 'config_web_server',self.config_web_server)
		config.setboolean('General', 'set_sistem_time_from_ntp_server_at_startup',self.set_system_time_from_ntp_server_at_startup)
		config.setstr('General', 'ntp_server',self.ntp_server)
		config.setstr('General', 'reboot_at',self.reboot_at)
		config.setstr('General', 'shutdown_at',self.shutdown_at)
		config.setstr('General', 'shutdown_hour_before_sunset',self.shutdown_hour_before_sunset)
		config.setfloat('General', 'location_latitude',self.location_latitude)
		config.setfloat('General', 'location_longitude',self.location_longitude)
		config.setfloat('General', 'location_altitude',self.location_altitude)
		config.setboolean('General', 'wifi_reset_if_down',self.wifi_reset_if_down)
		config.setint('General', 'config_web_server_port',self.config_web_server_port)



		# [Dongle]
		config.setboolean('Dongle', 'usedongle',self.usedongle)
		config.setboolean('Dongle', 'alwaysoninternet',self.AlwaysOnInternet)
		config.setstr('Dongle', 'dongleCtrlPort',self.dongleCtrlPort)
		config.setstr('Dongle', 'dongleAudioPort',self.dongleAudioPort)
		config.setstr('Dongle', 'dongleDataPort',self.dongleDataPort)
		config.setboolean('Dongle', 'UseDongleNet',self.UseDongleNet)
		config.setstr('Dongle', 'operator',self.operator)
		config.setfloat('Dongle', 'prober_timeout',self.prober_timeout)
		config.setint('Dongle', 'modem_baudrate',self.modem_baudrate)
		config.setint('Dongle', 'audio_baudrate',self.audio_baudrate)
		config.setint('Dongle', 'ctrl__baudrate',self.ctrl__baudrate)
		config.setstr('Dongle', 'dialnum',self.dialnum)
		config.setstr('Dongle', 'pppd_path',self.pppd_path)

		#[Security]
		config.setstr('Security', 'SMSPwd',self.SMSPwd)

		#[DataLogging]
		config.setboolean('DataLogging', 'logdata',self.logdata)
		config.setstr('DataLogging', 'serverfile',self.serverfile)

		#[Upload]
		config.setboolean('Upload', 'upload_data',self.upload_data)
		config.setstr('Upload', 'upload_folder',self.upload_folder)

		# [Sensors]
		config.setstr('Sensors', 'sensor_type',self.sensor_type)
		config.setboolean('Sensors', 'use_wind_sensor',self.use_wind_sensor)
		config.setint('Sensors', 'number_of_measure_for_wind_dir_average',self.number_of_measure_for_wind_dir_average)
		config.setfloat('Sensors', 'windspeed_offset',self.windspeed_offset)
		config.setfloat('Sensors', 'windspeed_gain',self.windspeed_gain)
		config.setint('Sensors', 'windmeasureinterval',self.windmeasureinterval)
		config.setboolean('Sensors', 'use_bmp085',self.use_bmp085)
		config.setboolean('Sensors', 'use_tmp36',self.use_tmp36)
		config.setint('Sensors', 'number_of_measure_for_wind_average_gust_calculation',self.number_of_measure_for_wind_average_gust_calculation)

		# [Sensor_PCE-FWS20]
		config.setboolean('Sensor_PCE-FWS20', 'set_system_time_from_WeatherStation',self.set_system_time_from_WeatherStation)

		# [Sensor_NEVIO8-16]

		#[WebCam]
		config.setstr('WebCam', 'webcamDevice1',self.webcamDevice1)
		config.setstr('WebCam', 'webcamDevice2',self.webcamDevice2)
		config.setstr('WebCam', 'webcamLogo',self.webcamLogo)
		config.setboolean('WebCam', 'sendImagesToServer',self.sendImagesToServer)
		config.setint('WebCam', 'WebCamInterval',self.WebCamInterval)
		config.setstr('WebCam', 'webcamdevice1captureresolution',"640x480")
		config.setstr('WebCam', 'webcamdevice2captureresolution',self.webcamdevice1captureresolution)
		config.setstr('WebCam', 'webcamdevice1finalresolution',self.webcamdevice1finalresolution)
		config.setstr('WebCam', 'webcamdevice2finalresolution',self.webcamdevice2finalresolution)
		config.setboolean('WebCam', 'capturewithffmpeg',self.capturewithffmpeg)
		config.setboolean('WebCam', 'sendallimagestoserver',self.sendallimagestoserver)
		config.setboolean('WebCam', 'delete_images_on_sd',self.delete_images_on_sd)

		#[Camera]
		config.setboolean('Camera', 'usecameradivice',self.usecameradivice)
		config.setstr('Camera', 'cameradivicefinalresolution',self.cameradivicefinalresolution)
		config.setstr('Camera', 'gphoto2options',self.gphoto2options)
		config.setboolean('Camera', 'reset_usb',self.reset_usb)
		config.setboolean('Camera', 'clear_all_sd_cards_at_startup',self.clear_all_sd_cards_at_startup)
		config.setint('Camera', 'start_camera_number',self.start_camera_number)
		config.setboolean('Camera', 'gphoto2_capture_image_and_download',self.gphoto2_capture_image_and_download)
		config.setboolean('Camera', 'use_camera_resetter',self.use_camera_resetter)



		# [ftp]
		config.setstr('ftp', 'ftpserver',self.ftpserver)
		config.setstr('ftp', 'ftpserverDestFolder',self.ftpserverDestFolder)
		config.setstr('ftp', 'ftpserverLogin',self.ftpserverLogin)
		config.setstr('ftp', 'ftpserverPassowd',self.ftpserverPassowd)
		config.setboolean('ftp', 'use_thread_for_sending_to_server',self.use_thread_for_sending_to_server)

		# [Radio]
		config.setboolean('Radio', 'useradio',self.useradio)
		config.setint('Radio', 'radiointerval',self.radiointerval)

		# [Mail]
		config.setstr('Mail', 'gmail_user',self.gmail_user)
		config.setstr('Mail', 'gmail_pwd',self.gmail_pwd)
		config.setstr('Mail', 'mail_to',self.mail_to)
		config.setboolean('Mail', 'use_mail',self.use_mail)
		config.setboolean('Mail', 'mail_ip',self.mail_ip)

		# [SMS]
		config.setboolean('SMS', 'send_IP_by_sms',self.send_IP_by_sms)
		config.setstr('SMS', 'number_to_send',self.number_to_send)

		#[WeatherUnderground]
		config.setboolean('WeatherUnderground', 'WeatherUnderground_logdata',self.WeatherUnderground_logdata)
		config.setstr('WeatherUnderground', 'WeatherUnderground_ID',self.WeatherUnderground_ID)		
		config.setstr('WeatherUnderground', 'WeatherUnderground_password',self.WeatherUnderground_password)		
		
		
		
		f = open(self.cfgName,"w")
		config.write(f)			

	def setWebCamInterval(self,newWebCamInterval):
		self.WebCamInterval = int(newWebCamInterval)
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('WebCam', 'webcaminterval',str(self.WebCamInterval))
		f = open(self.cfgName,"w")
		config.write(f)

	def setAlwaysOnInternet(self,AlwaysOnInternet):
		self.AlwaysOnInternet = AlwaysOnInternet
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('Dongle', 'alwaysoninternet',AlwaysOnInternet)
		f = open(self.cfgName,"w")
		config.write(f)
		
		
	def setDataLogging(self,LogData):
		self.logdata = LogData
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('DataLogging', 'LogData',LogData)
		f = open(self.cfgName,"w")
		config.write(f)		
		
		
	def setDataUpload(self,uploadData):
		self.upload_data = uploadData
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('Upload', 'upload_data',uploadData)
		f = open(self.cfgName,"w")
		config.write(f)		



		
	def setUseDongleNet(self,UseDongleNet):
		self.UseDongleNet = UseDongleNet
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('Dongle', 'UseDongleNet',UseDongleNet)
		f = open(self.cfgName,"w")
		config.write(f)		
		
		
	def setWindSpeed_offset(self,windspeed_offset):
		self.windspeed_offset = float(windspeed_offset)
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('Sensors', 'windspeed_offset',str(self.windspeed_offset))
		f = open(self.cfgName,"w")
		config.write(f)
		
	def setWindSpeed_gain(self,windspeed_gain):
		self.windspeed_gain = float(windspeed_gain)
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('Sensors', 'windspeed_gain',str(self.windspeed_gain))
		f = open(self.cfgName,"w")
		config.write(f)
		
		
	def setCamera_resolution(self,newres):
		ires = int(newres)
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		if (ires == 0 ):
			self.cameradivicefinalresolution = "640x480"
		elif (ires == 1 ):
			self.cameradivicefinalresolution = "800x600"
		elif (ires == 2 ):
			self.cameradivicefinalresolution = "1024x768"
		elif (ires == 3 ):
			self.cameradivicefinalresolution = "1280x960"
		elif (ires == 4 ):
			self.cameradivicefinalresolution = "1400x1050"
		elif (ires == 5 ):
			self.cameradivicefinalresolution = "1600x1200"
		elif (ires == 6 ):
			self.cameradivicefinalresolution = "2048x1536"		

		self.cameradivicefinalresolutionX = int(self.cameradivicefinalresolution.split('x')[0])
		self.cameradivicefinalresolutionY = int(self.cameradivicefinalresolution.split('x')[1])
		
		config.set('Camera', 'cameradivicefinalresolution',self.cameradivicefinalresolution)	
		f = open(self.cfgName,"w")
		config.write(f)		
		
		
if __name__ == '__main__':
	pass