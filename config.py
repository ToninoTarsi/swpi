###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################
import globalvars
"""Classes and methods for handling configurationn file."""

from  TTLib import *
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
import datetime

def str2bool(v):
	return str(v).lower() in ("yes", "true", "t", "1")

def log(message) :
	print datetime.datetime.now().strftime("[%d/%m/%Y-%H:%M:%S]") , message

def systemRestart():
	if os.name != 'nt':
		log("Rebooting system ..")
		os.system("sudo reboot")
	else:
		print " Sorry, cannot reboot Windows"

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
		self.offline = config.getboolean('General', 'offline',False)
		#print "*******************self.offline",self.offline
		if ( self.offline or (self.offline == "True")):
			globalvars.offline = True
		else:
			globalvars.offline = False
		#print "*******************globalvars.offline",globalvars.offline	
		self.station_name = config.get('General', 'station_name',"Sint Wind PI")
		self.config_web_server = config.getboolean('General', 'config_web_server',True)
		self.config_web_server_port = config.getint('General', 'config_web_server_port',80)
		self.set_system_time_from_ntp_server_at_startup = config.getboolean('General', 'set_sistem_time_from_ntp_server_at_startup',True)
		self.ntp_server = config.get('General', 'ntp_server',"pool.ntp.org")
		self.reboot_at = config.get('General', 'reboot_at',"None")
		self.shutdown_at = config.get('General', 'shutdown_at',"None")
		self.shutdown_hour_before_sunset = config.get('General', 'shutdown_hour_before_sunset',"None")
		self.location_latitude = config.getfloat('General', 'location_latitude',43.351983)
		self.location_longitude = config.getfloat('General', 'location_longitude',12.743187)
		self.location_altitude = config.getfloat('General', 'location_altitude',0)
		self.wifi_reset_if_down = config.getboolean('General', 'wifi_reset_if_down',False)
		self.cloudbase_calib = config.getfloat('General', 'cloudbase_calib',1.0)
		self.set_time_at_boot = config.get('General', 'set_time_at_boot',"None")
		self.wind_speed_units = config.get('General', 'wind_speed_units',"kmh")
		self.ntp_url=config.get('General', 'ntp_url',"None")
		self.disable_hdmi = config.getboolean('General', 'disable_hdmi',False)
		#self.seconds_after_sunset_for_night = config.getint('General', 'seconds_after_sunset_for_night',3600)

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
		self.davis_error= config.getint('Sensors', 'davis_error',0)
		self.use_wind_sensor = config.getboolean('Sensors', 'use_wind_sensor',True)
		self.number_of_measure_for_wind_dir_average =  config.getint('Sensors', 'number_of_measure_for_wind_dir_average',30)
		self.windspeed_offset = config.getfloat('Sensors', 'windspeed_offset',0)
		self.windspeed_gain = config.getfloat('Sensors', 'windspeed_gain',1)
		self.windmeasureinterval = config.getint('Sensors', 'windmeasureinterval',6)
		self.use_bmp085 = config.getboolean('Sensors', 'use_bmp085',False)
		self.use_bme280 = config.getboolean('Sensors', 'use_bme280',False)
		self.use_tmp36 = config.getboolean('Sensors', 'use_tmp36',False)
		self.use_dht = config.getboolean('Sensors', 'use_dht',False)
		self.dht_type = config.get('Sensors', 'dht_type',"DHT11")
		self.number_of_measure_for_wind_trend = config.getint('Sensors', 'number_of_measure_for_wind_trend',40)
		self.wind_trend_limit = config.getfloat('Sensors', 'wind_trend_limit',10)
		self.number_of_measure_for_wind_average_gust_calculation =  config.getint('Sensors', 'number_of_measure_for_wind_average_gust_calculation',10)
		self.sensor_temp_out =   config.get('Sensors', 'sensor_temp_out',"Default")
		self.sensor_temp_in =   config.get('Sensors', 'sensor_temp_in',"Default")
		self.solarsensor =   config.getboolean('Sensors', 'solarsensor',False)
		self.uvsensor =   config.getboolean('Sensors', 'uvsensor',False)
		self.external_sensor_path = config.get('Sensors', 'external_sensor_path',"http://yoursite.com/meteo.txt")
		self.anemometer_pin = config.getint('Sensors', 'anemometer_pin',23)

		# [mcp3002]
		self.mcp3002_spiDev = config.getint('mcp3002', 'mcp3002_spiDev',0)
		
		# [LoRa]
		self.use_LoRa = config.getboolean('LoRa', 'use_LoRa',False)
		self.LoRa_spiDev = config.getint('LoRa', 'LoRa_spiDev',1)
		self.LoRa_frequency = config.getfloat('LoRa', 'LoRa_frequency',868.0)
		self.LoRa_power = config.getint('LoRa', 'LoRa_power',23) # 23 - max LoRa power ( min = 5 )
		self.LoRa_ID = config.get('LoRa', 'LoRa_ID',"1")  # station ID ( only one char )
		self.LoRa_BW = config.get('LoRa', 'LoRa_BW',"125")  # ["7.8" , "10.4" , "15.6" , "20.8" , "31.23" , "41.7" , "62.5" , "125" , "250" , "500"]
		self.LoRa_CR = config.get('LoRa', 'LoRa_CR',"4/5") # 4/[5,6,7,8]
		self.LoRa_SF = config.get('LoRa', 'LoRa_SF',"7") # [6,7,8,9,10,11,12]
		self.LoRa_mode = config.get('LoRa', 'LoRa_mode',"Bidirectional") # 


		# [Sensor_PCE-FWS20]
		self.set_system_time_from_WeatherStation = config.getboolean('Sensor_PCE-FWS20', 'set_system_time_from_WeatherStation',False)

		# [Sensor_serial]
		self.sensor_serial_port = config.get('Sensor_serial', 'sensor_serial_port',"/dev/ttyUSB0")

		# [Sensor_NEVIO8-16]

		# [RFM01]
		self.rfm01_frequenzy = config.getint('RFM01', 'rfm01_frequenzy',868)
		self.rfm01_band = config.getint('RFM01', 'rfm01_band',134)
		self.rfm01_lna = config.getint('RFM01', 'rfm01_lna',0)
		self.rfm01_rssi = config.getint('RFM01', 'rfm01_rssi',97)
		
		# [RTL-SDR]
		self.rtlsdr_frequency = config.getint('RTL-SDR', 'rtlsdr_frequency',868)
		self.rtlsdr_bdl = config.getint('RTL-SDR', 'rtlsdr_bdl',0)
		self.rtlsdr_ppm = config.getint('RTL-SDR', 'rtlsdr_ppm',0)
		self.rtlsdr_timesync = config.getboolean('RTL-SDR', 'rtlsdr_timesync',True)

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
		self.sendallimagestoserver = config.getboolean('WebCam', 'sendallimagestoserver',False)
		self.delete_images_on_sd = config.getboolean('WebCam', 'delete_images_on_sd',False)
		self.captureprogram = config.get('WebCam', 'captureprogram',"fswebcam")

		#[Camera]
		self.usecameradivice = config.getboolean('Camera', 'usecameradivice',True)
		self.cameradivicefinalresolution = config.get('Camera', 'cameradivicefinalresolution',"800x600")
		self.gphoto2options = config.get('Camera', 'gphoto2options',",,,,,,,,,,")
		self.gphoto2options_Night = config.get('Camera', 'gphoto2options_Night',",,,,,,,,,,")
		self.reset_usb = config.getboolean('Camera', 'reset_usb',False)
		self.clear_all_sd_cards_at_startup = config.getboolean('Camera', 'clear_all_sd_cards_at_startup',True)
		self.start_camera_number = config.getint('Camera', 'start_camera_number',1)
		self.gphoto2_capture_image_and_download = config.getboolean('Camera', 'gphoto2_capture_image_and_download',True)
		self.use_camera_resetter = config.getboolean('Camera', 'use_camera_resetter',False)
		self.camera_resetter_normaly_on = config.getboolean('Camera', 'camera_resetter_normaly_on',True)
		self.on_off_camera = config.getboolean('Camera', 'on_off_camera',False)

		self.webcamdevice1captureresolutionX = int(self.webcamdevice1captureresolution.split('x')[0])
		self.webcamdevice1captureresolutionY = int(self.webcamdevice1captureresolution.split('x')[1])
		self.webcamdevice1finalresolutionX = int(self.webcamdevice1finalresolution.split('x')[0])
		self.webcamdevice1finalresolutionY = int(self.webcamdevice1finalresolution.split('x')[1])		
		self.webcamdevice2captureresolutionX = int(self.webcamdevice2captureresolution.split('x')[0])
		self.webcamdevice2captureresolutionY = int(self.webcamdevice2captureresolution.split('x')[1])
		self.webcamdevice2finalresolutionX = int(self.webcamdevice2finalresolution.split('x')[0])
		self.webcamdevice2finalresolutionY = int(self.webcamdevice2finalresolution.split('x')[1])
		self.cameradivicefinalresolutionX = int(self.cameradivicefinalresolution.split('x')[0])
		self.cameradivicefinalresolutionY = int(self.cameradivicefinalresolution.split('x')[1])
		
		#[CameraPI]
		self.use_cameraPI = config.getboolean('CameraPI', 'use_cameraPI',False)
		self.cameraPI_day_settings = config.get('CameraPI', 'cameraPI_day_settings',"")
		self.cameraPI_night_settings = config.get('CameraPI', 'cameraPI_night_settings',"")
						
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
		self.radio_verbosity = config.get('Radio', 'radio_verbosity',"only_wind")
		self.use_ptt = config.getboolean('Radio', 'use_ptt',False)

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

		#[CWOP]
		self.CWOP_logdata = config.getboolean('CWOP', 'CWOP_logdata',False)
		self.CWOP_ID = config.get('CWOP', 'CWOP_ID',"EW0000")
		self.CWOP_password = config.get('CWOP', 'CWOP_password',"-1")
	
		#[WindFinder]
		self.WindFinder_logdata = config.getboolean('WindFinder', 'WindFinder_logdata',False)
		self.WindFinder_ID = config.get('WindFinder', 'WindFinder_ID',"XXXXXX")
		self.WindFinder_password = config.get('WindFinder', 'WindFinder_password',"******")
		
		#[PWS]
		self.PWS_logdata = config.getboolean('PWS', 'PWS_logdata',False)
		self.PWS_ID = config.get('PWS', 'PWS_ID',"KCASANFR5")
		self.PWS_password = config.get('PWS', 'PWS_password',"XXXXXXXX")

		#[DNS Exit]
		self.use_DNSExit = config.getboolean('DNSExit', 'use_DNSExit',False)
		self.DNSExit_uname = config.get('DNSExit', 'DNSExit_uname',"user")
		self.DNSExit_pwd = config.get('DNSExit', 'DNSExit_pwd',"pwd")
		self.DNSExit_hname = config.get('DNSExit', 'DNSExit_hname',"xxxx.linkpc.net")		

		#[IP CAM]
		self.IPCamInterval = config.getint('IPCam', 'IPCamInterval',600)
		self.IPCamCfg = config.get('IPCam', 'IPCamCfg',"None")
		self.IPCamIP1 = config.get('IPCam', 'IPCamIP1',"None")
		self.IPCamUS1 = config.get('IPCam', 'IPCamUS1',"None")
		self.IPCamPW1 = config.get('IPCam', 'IPCamPW1',"None")
		self.IPCamSN1 = config.get('IPCam', 'IPCamSN1',"None")
		self.IPCamIP2 = config.get('IPCam', 'IPCamIP2',"None")		
		self.IPCamUS2 = config.get('IPCam', 'IPCamUS2',"None")
		self.IPCamPW2 = config.get('IPCam', 'IPCamPW2',"None")
		self.IPCamSN2 = config.get('IPCam', 'IPCamSN2',"None")
		self.IPCamZZZ = config.getint('IPCam', 'IPCamZZZ',0)				
		self.IPCamPosN = config.get('IPCam', 'IPCamPosN',"None")
		self.IPCamPosNE = config.get('IPCam', 'IPCamPosNE',"None")	
		self.IPCamPosE = config.get('IPCam', 'IPCamPosE',"None")	
		self.IPCamPosSE = config.get('IPCam', 'IPCamPosSE',"None")	
		self.IPCamPosS = config.get('IPCam', 'IPCamPosS',"None")	
		self.IPCamPosSW = config.get('IPCam', 'IPCamPosSW',"None")	
		self.IPCamPosW = config.get('IPCam', 'IPCamPosW',"None")	
		self.IPCamPosNW = config.get('IPCam', 'IPCamPosNW',"None")			
		
		#[LAYOUT]
		self.LayColorTBC = config.get('LayOut', 'LayColorTBC',"FF99FF")
		self.LayColorTTC = config.get('LayOut', 'LayColorTTC',"0000FF")
		self.LayColorBBC = config.get('LayOut', 'LayColorBBC',"FF99FF")
		self.LayColorBTC = config.get('LayOut', 'LayColorBTC',"0000FF")
		
		
		
 		if ( not os.path.isfile(self.cfgName)  ):
	 		f = open(self.cfgName,"w")
 			config.write(f)		
 			f.close()			


	def writeCfg(self):

		config = myConfigParser()
		
		#[General]
		#print "*****************",self.offline,globalvars.offline
		config.setboolean('General', 'offline',self.offline)
		if ( self.offline == "True"):
			globalvars.offline = True
		else:
			globalvars.offline = False
		#print "*****************",self.offline,globalvars.offline
		config.setstr('General', 'station_name',self.station_name)
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
		config.setfloat('General', 'cloudbase_calib',self.cloudbase_calib)
		config.setstr('General', 'set_time_at_boot',self.set_time_at_boot)
		config.setstr('General', 'wind_speed_units',self.wind_speed_units)
		config.setstr('General', 'ntp_url',self.ntp_url)
		config.setboolean('General', 'disable_hdmi',self.disable_hdmi)
		#config.setint('General', 'seconds_after_sunset_for_night',self.seconds_after_sunset_for_night)

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
		config.setint('Sensors', 'davis_error',self.davis_error)
		config.setboolean('Sensors', 'use_wind_sensor',self.use_wind_sensor)
		config.setint('Sensors', 'number_of_measure_for_wind_dir_average',self.number_of_measure_for_wind_dir_average)
		config.setfloat('Sensors', 'windspeed_offset',self.windspeed_offset)
		config.setfloat('Sensors', 'windspeed_gain',self.windspeed_gain)
		config.setint('Sensors', 'windmeasureinterval',self.windmeasureinterval)
		config.setboolean('Sensors', 'use_bmp085',self.use_bmp085)
		config.setboolean('Sensors', 'use_bme280',self.use_bme280)
		config.setboolean('Sensors', 'use_tmp36',self.use_tmp36)
		config.setboolean('Sensors', 'use_dht',self.use_dht)
		config.setstr('Sensors', 'dht_type',self.dht_type)
		config.setint('Sensors', 'number_of_measure_for_wind_trend',self.number_of_measure_for_wind_trend)
		config.setfloat('Sensors', 'wind_trend_limit',self.wind_trend_limit)
		config.setint('Sensors', 'number_of_measure_for_wind_average_gust_calculation',self.number_of_measure_for_wind_average_gust_calculation)
		config.setstr('Sensors', 'sensor_temp_out',self.sensor_temp_out)
		config.setstr('Sensors', 'sensor_temp_in',self.sensor_temp_in)
		config.setboolean('Sensors', 'solarsensor',self.solarsensor)
		config.setboolean('Sensors', 'uvsensor',self.uvsensor)
		config.setstr('Sensors', 'external_sensor_path',self.external_sensor_path)
		config.setint('Sensors', 'anemometer_pin',self.anemometer_pin)

		# [mcp3002]
		config.setint('mcp3002', 'mcp3002_spiDev',self.mcp3002_spiDev)
		
		# [LoRa] 
		config.setboolean('LoRa', 'use_LoRa',self.use_LoRa)
		config.setint('LoRa', 'LoRa_spiDev',self.LoRa_spiDev)
		config.setfloat('LoRa', 'LoRa_frequency',self.LoRa_frequency)
		config.setint('LoRa', 'LoRa_power',self.LoRa_power)
		config.setstr('LoRa', 'LoRa_ID',self.LoRa_ID)
		config.setstr('LoRa', 'LoRa_BW',self.LoRa_BW)
		config.setstr('LoRa', 'LoRa_CR',self.LoRa_CR)
		config.setstr('LoRa', 'LoRa_SF',self.LoRa_SF)
		config.setstr('LoRa', 'LoRa_mode',self.LoRa_mode)

		# [Sensor_PCE-FWS20]
		config.setboolean('Sensor_PCE-FWS20', 'set_system_time_from_WeatherStation',self.set_system_time_from_WeatherStation)

		# [Sensor_serial]
		config.setstr('Sensor_serial', 'sensor_serial_port',self.sensor_serial_port)

		# [Sensor_NEVIO8-16]

		config.setint('RFM01', 'rfm01_frequenzy',self.rfm01_frequenzy)
		config.setint('RFM01', 'rfm01_band',self.rfm01_band)
		config.setint('RFM01', 'rfm01_lna',self.rfm01_lna)
		config.setint('RFM01', 'rfm01_rssi',self.rfm01_rssi)
		
		# [RTL-SDR]
		config.setint('RTL-SDR', 'rtlsdr_frequency',self.rtlsdr_frequency)
		config.setint('RTL-SDR', 'rtlsdr_bdl',self.rtlsdr_bdl)
		config.setint('RTL-SDR', 'rtlsdr_ppm',self.rtlsdr_ppm)
		config.setboolean('RTL-SDR', 'rtlsdr_timesync',self.rtlsdr_timesync)
		
		#[WebCam]
		config.setstr('WebCam', 'webcamDevice1',self.webcamDevice1)
		config.setstr('WebCam', 'webcamDevice2',self.webcamDevice2)
		config.setstr('WebCam', 'webcamLogo',self.webcamLogo)
		config.setboolean('WebCam', 'sendImagesToServer',self.sendImagesToServer)
		config.setint('WebCam', 'WebCamInterval',self.WebCamInterval)
		config.setstr('WebCam', 'webcamdevice1captureresolution',self.webcamdevice1captureresolution)
		config.setstr('WebCam', 'webcamdevice2captureresolution',self.webcamdevice2captureresolution)
		config.setstr('WebCam', 'webcamdevice1finalresolution',self.webcamdevice1finalresolution)
		config.setstr('WebCam', 'webcamdevice2finalresolution',self.webcamdevice2finalresolution)
		config.setstr('WebCam', 'captureprogram',self.captureprogram)
		config.setboolean('WebCam', 'sendallimagestoserver',self.sendallimagestoserver)
		config.setboolean('WebCam', 'delete_images_on_sd',self.delete_images_on_sd)
				
		#[Camera]
		config.setboolean('Camera', 'usecameradivice',self.usecameradivice)
		config.setstr('Camera', 'cameradivicefinalresolution',self.cameradivicefinalresolution)
		config.setstr('Camera', 'gphoto2options',self.gphoto2options)
		config.setstr('Camera', 'gphoto2options_Night',self.gphoto2options_Night)
		config.setboolean('Camera', 'reset_usb',self.reset_usb)
		config.setboolean('Camera', 'clear_all_sd_cards_at_startup',self.clear_all_sd_cards_at_startup)
		config.setint('Camera', 'start_camera_number',self.start_camera_number)
		config.setboolean('Camera', 'gphoto2_capture_image_and_download',self.gphoto2_capture_image_and_download)
		config.setboolean('Camera', 'use_camera_resetter',self.use_camera_resetter)
		config.setboolean('Camera', 'camera_resetter_normaly_on',self.camera_resetter_normaly_on)
		config.setboolean('Camera', 'on_off_camera',self.on_off_camera) 

		#[CameraPI]
		config.setboolean('CameraPI', 'use_cameraPI',self.use_cameraPI)
		config.setstr('CameraPI', 'cameraPI_day_settings',self.cameraPI_day_settings)
		config.setstr('CameraPI', 'cameraPI_night_settings',self.cameraPI_night_settings)

		# [ftp]
		config.setstr('ftp', 'ftpserver',self.ftpserver)
		config.setstr('ftp', 'ftpserverDestFolder',self.ftpserverDestFolder)
		config.setstr('ftp', 'ftpserverLogin',self.ftpserverLogin)
		config.setstr('ftp', 'ftpserverPassowd',self.ftpserverPassowd)
		config.setboolean('ftp', 'use_thread_for_sending_to_server',self.use_thread_for_sending_to_server)

		# [Radio]
		config.setboolean('Radio', 'use_ptt',self.use_ptt)
		config.setint('Radio', 'radiointerval',self.radiointerval)
		config.setstr('Radio', 'radio_verbosity',self.radio_verbosity)
		config.setboolean('Radio', 'useradio',self.useradio)

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
		
		#[PWS]
		config.setboolean('PWS', 'PWS_logdata',self.PWS_logdata)
		config.setstr('PWS', 'PWS_ID',self.PWS_ID)		
		config.setstr('PWS', 'PWS_password',self.PWS_password)	
		
		#[CWOP]
		config.setboolean('CWOP', 'CWOP_logdata',self.CWOP_logdata)
		config.setstr('CWOP', 'CWOP_ID',self.CWOP_ID)		
		config.setstr('CWOP', 'CWOP_password',self.CWOP_password)	
		
		#[WindFinder]
		config.setboolean('WindFinder', 'WindFinder_logdata',self.WindFinder_logdata)
		config.setstr('WindFinder', 'WindFinder_ID',self.WindFinder_ID)		
		config.setstr('WindFinder', 'WindFinder_password',self.WindFinder_password)	
		

		#[DNS Exit]
		config.setboolean('DNSExit', 'use_DNSExit',self.use_DNSExit)
		config.setstr('DNSExit', 'DNSExit_uname',self.DNSExit_uname)		
		config.setstr('DNSExit', 'DNSExit_pwd',self.DNSExit_pwd)	
		config.setstr('DNSExit', 'DNSExit_hname ',self.DNSExit_hname)	

		#[IP CAM]
		config.setint('IPCam', 'IPCamInterval',self.IPCamInterval)
		config.setstr('IPCam', 'IPCamCfg',self.IPCamCfg)		
		config.setstr('IPCam', 'IPCamIP1',self.IPCamIP1)
		config.setstr('IPCam', 'IPCamUS1',self.IPCamUS1)
		config.setstr('IPCam', 'IPCamPW1',self.IPCamPW1)
		config.setstr('IPCam', 'IPCamSN1',self.IPCamSN1)
		config.setstr('IPCam', 'IPCamIP2',self.IPCamIP2)
		config.setstr('IPCam', 'IPCamUS2',self.IPCamUS2)
		config.setstr('IPCam', 'IPCamPW2',self.IPCamPW2)
		config.setstr('IPCam', 'IPCamSN2',self.IPCamSN2)
		config.setint('IPCam', 'IPCamZZZ',self.IPCamZZZ)		
		config.setstr('IPCam', 'IPCamPosN',self.IPCamPosN)
		config.setstr('IPCam', 'IPCamPosNE',self.IPCamPosNE)
		config.setstr('IPCam', 'IPCamPosE',self.IPCamPosE)
		config.setstr('IPCam', 'IPCamPosSE',self.IPCamPosSE)
		config.setstr('IPCam', 'IPCamPosS',self.IPCamPosS)
		config.setstr('IPCam', 'IPCamPosSW',self.IPCamPosSW)		
		config.setstr('IPCam', 'IPCamPosW',self.IPCamPosW)
		config.setstr('IPCam', 'IPCamPosNW',self.IPCamPosNW)

		#[LAYOUT]
		config.setstr('LayOut', 'LayColorTBC',self.LayColorTBC)
		config.setstr('LayOut', 'LayColorTTC',self.LayColorTTC)
		config.setstr('LayOut', 'LayColorBBC',self.LayColorBBC)
		config.setstr('LayOut', 'LayColorBTC',self.LayColorBTC)
		
		
		f = open(self.cfgName,"w")
		config.write(f)			

	def setWebCamInterval(self,newWebCamInterval):
		self.WebCamInterval = int(newWebCamInterval)
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('WebCam', 'webcaminterval',str(self.WebCamInterval))
		f = open(self.cfgName,"w")
		config.write(f)
		
	def setLoRa_power(self,newLoRa_power):
		self.LoRa_power = int(newLoRa_power)
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('LoRa', 'LoRa_power',str(self.LoRa_power))
		f = open(self.cfgName,"w")
		config.write(f)
		
	def setLoRa_BW(self,newLoRa_BW):
		self.LoRa_BW = str(newLoRa_BW)
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('LoRa', 'LoRa_BW',str(self.LoRa_BW))
		f = open(self.cfgName,"w")
		config.write(f)		
		
	def setLoRa_CR(self,newLoRa_CR):
		self.LoRa_CR = str(newLoRa_CR)
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('LoRa', 'LoRa_CR',str(self.LoRa_CR))
		f = open(self.cfgName,"w")
		config.write(f)				
		
	def setLoRa_SF(self,newLoRa_SF):
		self.LoRa_SF = str(newLoRa_SF)
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('LoRa', 'LoRa_SF',str(self.LoRa_SF))
		f = open(self.cfgName,"w")
		config.write(f)	

	def setAlwaysOnInternet(self,AlwaysOnInternet):
		self.AlwaysOnInternet = AlwaysOnInternet
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('Dongle', 'alwaysoninternet',AlwaysOnInternet)
		f = open(self.cfgName,"w")
		config.write(f)
		
	def setShutdownTime(self,strTime):
		strTime = strTime.strip()
		if ( strTime.upper() != "NONE"):
			if ( strTime[2] != ":" or len(strTime) != 5  or not strTime[0:2].isdigit() or not strTime[3:5].isdigit()):
				log("ERORR - bad formatted time")
				return
			theHH = int(strTime[0:2])
			if ( theHH < 0 or theHH >24 ):
				log("ERORR - bad formatted time")
				return
			theMM = int(strTime[3:5])
			if ( theMM < 0 or theMM >60 ):
				log("ERORR - bad formatted time")
				return
		self.shutdown_at = strTime
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('General', 'shutdown_at',strTime)
		f = open(self.cfgName,"w")
		config.write(f)		
		log( "New Shutdown time set to : " + strTime + "... REBOOTING")
		systemRestart()
		
	def setDataLogging(self,LogData):
		self.logdata = LogData
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('DataLogging', 'LogData',LogData)
		f = open(self.cfgName,"w")
		config.write(f)		
		
	def setOffline(self,LogData):
		if (LogData == '0'):
			log("Station is now ONLINE")
			self.offline = "False"
		if (LogData == '1'):
			log("Station is now OFFLINE")			
			self.offline = "True"
		self.writeCfg()

	def setBMP085(self,LogData):
		if (LogData == '0'):
			log("BMP085 disabled")
			self.use_bmp085 = "False"
		if (LogData == '1'):
			log("BMP085 enabled")			
			self.use_bmp085 = "True"
		self.writeCfg()		
		
	def setBME280(self,LogData):
		if (LogData == '0'):
			log("BME280 disabled")
			self.use_bme280 = "False"
		if (LogData == '1'):
			log("BME280 enabled")			
			self.use_bme280 = "True"
		self.writeCfg()				
			
	def setDHT(self,LogData):
		if (LogData == '0'):
			log("DHT disabled")
			self.use_dht = "False"
		if (LogData == '1'):
			log("DHT enabled")			
			self.use_dht = "True"
		self.writeCfg()	
				
		
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

	def setIPCamInterval(self,newIPCamInterval):
		self.IPCamInterval = int(newIPCamInterval)
		config = ConfigParser.SafeConfigParser()
		config.read(self.cfgName)
		config.set('IPCam', 'ipcaminterval',str(self.IPCamInterval))
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
