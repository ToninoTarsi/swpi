###########################################################################
#	 Sint Wind PI
#	 Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#	 Please refer to the LICENSE file for conditions 
#	 Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""config web server page"""

import config
import string
import globalvars


def str2bool(v):
	return v.lower() in ("yes", "true", "t", "1")

def outputPage(cfg):

	in_file = open("template.html","r")
	text_template = in_file.read()
	in_file.close()

	html_template=string.Template(text_template)
	d = dict(location_latitude=cfg.location_latitude)

	#[General]
	d.update(offline=globalvars.offline)
	d.update(station_name=cfg.station_name)
	d.update(config_web_server=cfg.config_web_server)
	d.update(set_system_time_from_ntp_server_at_startup=cfg.set_system_time_from_ntp_server_at_startup)
	d.update(set_time_at_boot=cfg.set_time_at_boot)
	d.update(ntp_server=cfg.ntp_server)	
	d.update(reboot_at=cfg.reboot_at)
	d.update(shutdown_at=cfg.shutdown_at)
	d.update(shutdown_hour_before_sunset=cfg.shutdown_hour_before_sunset)	
	d.update(location_longitude=cfg.location_longitude)
	d.update(location_altitude=cfg.location_altitude)
	d.update(wifi_reset_if_down=cfg.wifi_reset_if_down)
	d.update(config_web_server_port=cfg.config_web_server_port)
	d.update(wind_speed_units=cfg.wind_speed_units)	
	d.update(set_time_at_boot=cfg.set_time_at_boot)
	d.update(ntp_url=cfg.ntp_url)
	d.update(disable_hdmi=cfg.disable_hdmi)


	# [Dongle]
	d.update(usedongle=cfg.usedongle)
	d.update(AlwaysOnInternet=cfg.AlwaysOnInternet)
	d.update(UseDongleNet=cfg.UseDongleNet)
	d.update(operator=cfg.operator)
	d.update(dongledataport=cfg.dongleDataPort)
	d.update(dongleaudioport=cfg.dongleAudioPort)
	d.update(donglectrlport=cfg.dongleCtrlPort)

	#[Security]
	d.update(SMSPwd=cfg.SMSPwd)

	#[DataLogging]
	d.update(logdata=cfg.logdata)
	d.update(serverfile=cfg.serverfile)

	#[Upload]
	d.update(upload_data=cfg.upload_data)
	d.update(upload_folder=cfg.upload_folder)

	# [Sensors]
	d.update(sensor_type=cfg.sensor_type)
	d.update(use_wind_sensor=cfg.use_wind_sensor)
	d.update(number_of_measure_for_wind_dir_average=cfg.number_of_measure_for_wind_dir_average)
	d.update(windspeed_offset=cfg.windspeed_offset)
	d.update(windspeed_gain=cfg.windspeed_gain)
	d.update(windmeasureinterval=cfg.windmeasureinterval)
	d.update(use_bmp085=cfg.use_bmp085)
	d.update(use_bme280=cfg.use_bme280)
	d.update(use_tmp36=cfg.use_tmp36)
	d.update(use_dht=cfg.use_dht)
	d.update(dht_type=cfg.dht_type)
	d.update(number_of_measure_for_wind_trend=cfg.number_of_measure_for_wind_trend)
	d.update(wind_trend_limit=cfg.wind_trend_limit)
	d.update(number_of_measure_for_wind_average_gust_calculation=cfg.number_of_measure_for_wind_average_gust_calculation)
	d.update(solarsensor=cfg.solarsensor)
	d.update(uvsensor=cfg.uvsensor)
	d.update(external_sensor_path=cfg.external_sensor_path)
	d.update(anemometer_pin=cfg.anemometer_pin)


	# [mcp3002]
	d.update(mcp3002_spiDev=cfg.mcp3002_spiDev)
	
	# [LoRa]
	d.update(use_LoRa=cfg.use_LoRa)
	d.update(LoRa_spiDev=cfg.LoRa_spiDev)
	d.update(LoRa_frequency=cfg.LoRa_frequency)
	d.update(LoRa_power=cfg.LoRa_power)
	d.update(LoRa_ID=cfg.LoRa_ID)
	d.update(LoRa_BW=cfg.LoRa_BW)
	d.update(LoRa_CR=cfg.LoRa_CR)
	d.update(LoRa_SF=cfg.LoRa_SF)
	d.update(LoRa_mode=cfg.LoRa_mode)

	
	# [Sensor_PCE-FWS20]
	d.update(set_system_time_from_WeatherStation=cfg.set_system_time_from_WeatherStation)

	# [Sensor Serial]
	d.update(sensor_serial_port=cfg.sensor_serial_port)

	# [Sensor_NEVIO8-16]

	# [RFM01]
	d.update(rfm01_frequenzy=cfg.rfm01_frequenzy)
	d.update(rfm01_band=cfg.rfm01_band)
	d.update(rfm01_lna=cfg.rfm01_lna)
	d.update(rfm01_rssi=cfg.rfm01_rssi)
	
	# [RTL-SDR]
	d.update(rtlsdr_frequency=cfg.rtlsdr_frequency)
	d.update(rtlsdr_bdl=cfg.rtlsdr_bdl)
	d.update(rtlsdr_ppm=cfg.rtlsdr_ppm)
	d.update(rtlsdr_timesync=cfg.rtlsdr_timesync)	

	#[WebCam]	
	d.update(webcamDevice1=cfg.webcamDevice1)
	d.update(webcamDevice2=cfg.webcamDevice2)
	d.update(webcamLogo=cfg.webcamLogo)
	d.update(sendImagesToServer=cfg.sendImagesToServer)
	d.update(WebCamInterval=cfg.WebCamInterval)
	d.update(webcamdevice1captureresolution=cfg.webcamdevice1captureresolution)
	d.update(webcamdevice2captureresolution=cfg.webcamdevice2captureresolution)
	d.update(webcamdevice1finalresolution=cfg.webcamdevice1finalresolution)
	d.update(webcamdevice2finalresolution=cfg.webcamdevice2finalresolution)
	d.update(sendallimagestoserver=cfg.sendallimagestoserver)
	d.update(delete_images_on_sd=cfg.delete_images_on_sd)
	d.update(captureprogram=cfg.captureprogram)

	#[Camera]
	d.update(usecameradivice=cfg.usecameradivice)
	d.update(cameradivicefinalresolution=cfg.cameradivicefinalresolution)
	d.update(gphoto2options=cfg.gphoto2options)
	d.update(gphoto2options_Night=cfg.gphoto2options_Night)
	d.update(reset_usb=cfg.reset_usb)
	d.update(clear_all_sd_cards_at_startup=cfg.clear_all_sd_cards_at_startup)
	d.update(start_camera_number=cfg.start_camera_number)
	d.update(gphoto2_capture_image_and_download=cfg.gphoto2_capture_image_and_download)
	d.update(use_camera_resetter=cfg.use_camera_resetter)
	d.update(camera_resetter_normaly_on=cfg.camera_resetter_normaly_on)
	d.update(on_off_camera=cfg.on_off_camera)

	#[CameraPI]
	d.update(use_cameraPI=cfg.use_cameraPI)
	d.update(cameraPI_day_settings=cfg.cameraPI_day_settings)
	d.update(cameraPI_night_settings=cfg.cameraPI_night_settings)
		
	# [ftp]
	d.update(ftpserver=cfg.ftpserver)
	d.update(ftpserverDestFolder=cfg.ftpserverDestFolder)
	d.update(ftpserverLogin=cfg.ftpserverLogin)
	d.update(ftpserverPassowd=cfg.ftpserverPassowd)
	d.update(use_thread_for_sending_to_server=cfg.use_thread_for_sending_to_server)

	# [Radio]
	d.update(useradio=cfg.useradio)
	d.update(radiointerval=cfg.radiointerval)
	d.update(radio_verbosity=cfg.radio_verbosity)

	# [Mail]
	d.update(gmail_user=cfg.gmail_user)
	d.update(gmail_pwd=cfg.gmail_pwd)
	d.update(mail_to=cfg.mail_to)
	d.update(use_mail=cfg.use_mail)
	d.update(mail_ip=cfg.mail_ip)

	# [SMS]
	d.update(send_IP_by_sms=cfg.send_IP_by_sms)
	d.update(number_to_send=cfg.number_to_send)
	
	#[WeatherUnderground]
	d.update(WeatherUnderground_logdata=cfg.WeatherUnderground_logdata)
	d.update(WeatherUnderground_ID=cfg.WeatherUnderground_ID)
	d.update(WeatherUnderground_password=cfg.WeatherUnderground_password)

	#[CWOP]
	d.update(CWOP_logdata=cfg.CWOP_logdata)
	d.update(CWOP_ID=cfg.CWOP_ID)
	d.update(CWOP_password=cfg.CWOP_password)
	
	#[WindFinder]
	d.update(WindFinder_logdata=cfg.WindFinder_logdata)
	d.update(WindFinder_ID=cfg.WindFinder_ID)
	d.update(WindFinder_password=cfg.WindFinder_password)	

	#[PWS]		
	d.update(PWS_logdata=cfg.PWS_logdata)
	d.update(PWS_ID=cfg.PWS_ID)
	d.update(PWS_password=cfg.PWS_password)
	
	#[DNS Exit]
	d.update(use_DNSExit=cfg.use_DNSExit)
	d.update(DNSExit_uname=cfg.DNSExit_uname)
	d.update(DNSExit_pwd=cfg.DNSExit_pwd)
	d.update(DNSExit_hname=cfg.DNSExit_hname)

	#[IP CAM]
	d.update(IPCamInterval=cfg.IPCamInterval)
	d.update(IPCamCfg=cfg.IPCamCfg)
	d.update(IPCamIP1=cfg.IPCamIP1)
	d.update(IPCamUS1=cfg.IPCamUS1)
	d.update(IPCamPW1=cfg.IPCamPW1)
	d.update(IPCamSN1=cfg.IPCamSN1)
	d.update(IPCamIP2=cfg.IPCamIP2)
	d.update(IPCamUS2=cfg.IPCamUS2)
	d.update(IPCamPW2=cfg.IPCamPW2)
	d.update(IPCamSN2=cfg.IPCamSN2)
	d.update(IPCamZZZ=cfg.IPCamZZZ)	
	d.update(IPCamPosN=cfg.IPCamPosN)
	d.update(IPCamPosNE=cfg.IPCamPosNE)
	d.update(IPCamPosE=cfg.IPCamPosE)
	d.update(IPCamPosSE=cfg.IPCamPosSE)
	d.update(IPCamPosS=cfg.IPCamPosS)
	d.update(IPCamPosSW=cfg.IPCamPosSW)
	d.update(IPCamPosW=cfg.IPCamPosW)
	d.update(IPCamPosNW=cfg.IPCamPosNW)

	#[LAYOUT]
	d.update(LayColorTBC=cfg.LayColorTBC)
	d.update(LayColorTTC=cfg.LayColorTTC)
	d.update(LayColorBBC=cfg.LayColorBBC)
	d.update(LayColorBTC=cfg.LayColorBTC)


	html = html_template.safe_substitute(d)

	print html

so = Session()


if not hasattr(so,'loggedin'):
	raise HTTP_REDIRECTION,"index.html"
#else:
#	if ( not so['loggedin'] ):
#		raise HTTP_REDIRECTION,"index.html"	
#	

configfile = 'swpi.cfg'
cfg = config.config(configfile,False)

#print request
	
if ( len(request) != 0 ):

	#[General]
	cfg.offline = request['offline'][0]	
	cfg.station_name = request['station_name'][0]
	cfg.config_web_server = request['config_web_server'][0]																 
	cfg.set_system_time_from_ntp_server_at_startup = request['set_system_time_from_ntp_server_at_startup'][0]	
	cfg.set_time_at_boot = request['set_time_at_boot'][0]					   
	cfg.ntp_server = request['ntp_server'][0]																		   
	cfg.reboot_at = request['reboot_at'][0]																		   
	cfg.shutdown_at = request['shutdown_at'][0]																		   
	cfg.shutdown_hour_before_sunset = request['shutdown_hour_before_sunset'][0]																		 					   
	cfg.location_latitude = request['location_latitude'][0]																 
	cfg.location_longitude = request['location_longitude'][0]																 
	cfg.location_altitude = request['location_altitude'][0]																 
	cfg.wifi_reset_if_down = request['wifi_reset_if_down'][0]       
	cfg.config_web_server_port = request['config_web_server_port'][0]                                                                 
	cfg.wind_speed_units = request['wind_speed_units'][0]
	cfg.ntp_url = request['ntp_url'][0]
	cfg.disable_hdmi = request['disable_hdmi'][0]


	# [Dongle]
	cfg.usedongle = request['usedongle'][0]																		   
	cfg.AlwaysOnInternet = request['AlwaysOnInternet'][0]																 
	cfg.UseDongleNet = request['UseDongleNet'][0]																	  
	cfg.operator = request['operator'][0]																		   
	cfg.dongleDataPort = request['dongledataport'][0]																		   
	cfg.dongleAudioPort = request['dongleaudioport'][0]																		   
	cfg.dongleCtrlPort = request['donglectrlport'][0]																		   


	#[Security]
	cfg.SMSPwd = request['SMSPwd'][0]
	
	#[DataLogging]
	cfg.logdata = request['logdata'][0]																				
	cfg.serverfile = request['serverfile'][0]																		   

	#[Upload]
	cfg.upload_data = request['upload_data'][0]																		   
	cfg.upload_folder = request['upload_folder'][0]
	
	# [Sensors]
	cfg.sensor_type = request['sensor_type'][0]																		   
	cfg.use_wind_sensor = request['use_wind_sensor'][0]																	  
	cfg.number_of_measure_for_wind_dir_average = request['number_of_measure_for_wind_dir_average'][0]										
	cfg.windspeed_offset = request['windspeed_offset'][0]																 
	cfg.windspeed_gain = request['windspeed_gain'][0]																	  
	cfg.windmeasureinterval = request['windmeasureinterval'][0]																 
	cfg.use_bmp085 = request['use_bmp085'][0]																		   
	cfg.use_bme280 = request['use_bme280'][0]
	cfg.use_tmp36 = request['use_tmp36'][0]		
	cfg.use_dht = request['use_dht'][0]		
	cfg.dht_type = request['dht_type'][0]		
	cfg.number_of_measure_for_wind_trend = request['number_of_measure_for_wind_trend'][0]	
	cfg.wind_trend_limit = request['wind_trend_limit'][0]																		   
	cfg.number_of_measure_for_wind_average_gust_calculation = request['number_of_measure_for_wind_average_gust_calculation'][0]
	cfg.solarsensor = request['solarsensor'][0]
	cfg.uvsensor = request['uvsensor'][0]
	cfg.external_sensor_path = request['external_sensor_path'][0]
	cfg.anemometer_pin = request['anemometer_pin'][0]																 

	
	# [mcp3002]
	cfg.mcp3002_spiDev = request['mcp3002_spiDev'][0]
	
	# [LoRa]
	cfg.LoRa_spiDev = request['LoRa_spiDev'][0]
	cfg.use_LoRa = request['use_LoRa'][0]
	cfg.LoRa_frequency = request['LoRa_frequency'][0]
	cfg.LoRa_power = request['LoRa_power'][0]
	cfg.LoRa_ID = request['LoRa_ID'][0]
	cfg.LoRa_BW = request['LoRa_BW'][0]
	cfg.LoRa_CR = request['LoRa_CR'][0]
	cfg.LoRa_SF = request['LoRa_SF'][0]
	cfg.LoRa_mode = request['LoRa_mode'][0]


	# [Sensor_PCE-FWS20]
	cfg.set_system_time_from_WeatherStation = request['set_system_time_from_WeatherStation'][0]
	
	# [Sensor Serial]
	cfg.sensor_serial_port = request['sensor_serial_port'][0]											 

	#[WebCam]
	cfg.webcamDevice1 = request['webcamDevice1'][0]																	  
	cfg.webcamDevice2 = request['webcamDevice2'][0]		
	cfg.webcamLogo = request['webcamLogo'][0]													   
	cfg.sendImagesToServer = request['sendImagesToServer'][0]																 
	cfg.WebCamInterval = request['WebCamInterval'][0]																	  
	cfg.webcamdevice1captureresolution = request['webcamdevice1captureresolution'][0]												  
	cfg.webcamdevice2captureresolution = request['webcamdevice2captureresolution'][0]												  
	cfg.webcamdevice1finalresolution = request['webcamdevice1finalresolution'][0]												  
	cfg.webcamdevice2finalresolution = request['webcamdevice2finalresolution'][0]												  
	cfg.captureprogram = request['captureprogram'][0]																 
	cfg.sendallimagestoserver = request['sendallimagestoserver'][0]															
	cfg.delete_images_on_sd = request['delete_images_on_sd'][0]																								   
	
	#[Camera]	
	cfg.usecameradivice = request['usecameradivice'][0]																	  
	cfg.cameradivicefinalresolution = request['cameradivicefinalresolution'][0]													   
	cfg.gphoto2options = request['gphoto2options'][0]		
	cfg.gphoto2options_Night = request['gphoto2options_Night'][0]																	  
	cfg.reset_usb = request['reset_usb'][0]																		   
	cfg.clear_all_sd_cards_at_startup = request['clear_all_sd_cards_at_startup'][0]												  
	cfg.start_camera_number = request['start_camera_number'][0]																 
	cfg.gphoto2_capture_image_and_download = request['gphoto2_capture_image_and_download'][0]											 
	cfg.use_camera_resetter = request['use_camera_resetter'][0]											 
	cfg.camera_resetter_normaly_on = request['camera_resetter_normaly_on'][0]
	cfg.on_off_camera = request['on_off_camera'][0]

	#[CameraPI]
	cfg.use_cameraPI = request['use_cameraPI'][0]											 
	cfg.cameraPI_day_settings = request['cameraPI_day_settings'][0]											 
	cfg.cameraPI_night_settings = request['cameraPI_night_settings'][0]											 

	# [RFM01]
	cfg.rfm01_frequenzy = request['rfm01_frequenzy'][0]											 
	cfg.rfm01_band = request['rfm01_band'][0]											 
	cfg.rfm01_lna = request['rfm01_lna'][0]											 
	cfg.rfm01_rssi = request['rfm01_rssi'][0]
	
	# [RTL-SDR]
	cfg.rtlsdr_frequency = request['rtlsdr_frequency'][0]
	cfg.rtlsdr_bdl = request['rtlsdr_bdl'][0]
	cfg.rtlsdr_ppm = request['rtlsdr_ppm'][0]
	cfg.rtlsdr_timesync = request['rtlsdr_timesync'][0]	

	# [ftp]
	cfg.ftpserver = request['ftpserver'][0]																		   
	cfg.ftpserverDestFolder = request['ftpserverDestFolder'][0]																 
	cfg.ftpserverLogin = request['ftpserverLogin'][0]																	  
	cfg.ftpserverPassowd = request['ftpserverPassowd'][0]		
	cfg.use_thread_for_sending_to_server = request['use_thread_for_sending_to_server'][0]		

	# [Radio]	
	cfg.useradio = request['useradio'][0]																		   
	cfg.radiointerval = request['radiointerval'][0]																	  
	cfg.radio_verbosity = request['radio_verbosity'][0]																	  

	# [Mail]
	cfg.gmail_user = request['gmail_user'][0]																		   
	cfg.gmail_pwd = request['gmail_pwd'][0]																		   
	cfg.mail_to = request['mail_to'][0]																				
	cfg.use_mail = request['use_mail'][0]																		   
	cfg.mail_ip = request['mail_ip'][0]																				

	# [SMS]
	cfg.send_IP_by_sms = request['send_IP_by_sms'][0]				  
	cfg.number_to_send = request['number_to_send'][0]	  

	#[WeatherUnderground]
	cfg.WeatherUnderground_logdata = request['WeatherUnderground_logdata'][0]																	  
	cfg.WeatherUnderground_ID = request['WeatherUnderground_ID'][0]	  	
	cfg.WeatherUnderground_password = request['WeatherUnderground_password'][0]	  	

	#[CWOP]	
	cfg.CWOP_logdata = request['CWOP_logdata'][0]																	  
	cfg.CWOP_ID = request['CWOP_ID'][0]	  	
	cfg.CWOP_password = request['CWOP_password'][0]	
	
	
	#[WindFinder]	
	cfg.WindFinder_logdata = request['WindFinder_logdata'][0]																	  
	cfg.WindFinder_ID = request['WindFinder_ID'][0]	  	
	cfg.WindFinder_password = request['WindFinder_password'][0]	    	

	#[PWS]
	cfg.PWS_logdata = request['PWS_logdata'][0]																	  
	cfg.PWS_ID = request['PWS_ID'][0]	  	
	cfg.PWS_password = request['PWS_password'][0]	  

	#[DNS Exit]
	cfg.use_DNSExit = request['use_DNSExit'][0]																		   
	cfg.DNSExit_uname = request['DNSExit_uname'][0]																				
	cfg.DNSExit_pwd = request['DNSExit_pwd'][0]																		   
	cfg.DNSExit_hname = request['DNSExit_hname'][0]		

	# cfg.AlwaysOnInternet = request['AlwaysOnInternet'][0]
	# cfg.UseDongleNet = request['UseDongleNet'][0]

	#[IP CAM]
	cfg.IPCamInterval = request['IPCamInterval'][0]
	cfg.IPCamCfg = request['IPCamCfg'][0]
	cfg.IPCamIP1 = request['IPCamIP1'][0]
	cfg.IPCamUS1 = request['IPCamUS1'][0]
	cfg.IPCamPW1 = request['IPCamPW1'][0]
	cfg.IPCamSN1 = request['IPCamSN1'][0]
	cfg.IPCamIP2 = request['IPCamIP2'][0]
	cfg.IPCamUS2 = request['IPCamUS2'][0]
	cfg.IPCamPW2 = request['IPCamPW2'][0]
	cfg.IPCamSN2 = request['IPCamSN2'][0]
	cfg.IPCamZZZ = request['IPCamZZZ'][0]	
	cfg.IPCamPosN = request['IPCamPosN'][0]
	cfg.IPCamPosNE = request['IPCamPosNE'][0]
	cfg.IPCamPosE = request['IPCamPosE'][0]
	cfg.IPCamPosSE = request['IPCamPosSE'][0]
	cfg.IPCamPosS = request['IPCamPosS'][0]
	cfg.IPCamPosSW = request['IPCamPosSW'][0]
	cfg.IPCamPosW = request['IPCamPosW'][0]
	cfg.IPCamPosNW = request['IPCamPosNW'][0]

	#[LAYOUT]
	cfg.LayColorTBC = request['LayColorTBC'][0]
	cfg.LayColorTTC = request['LayColorTTC'][0]
	cfg.LayColorBBC = request['LayColorBBC'][0]
	cfg.LayColorBTC = request['LayColorBTC'][0]


	cfg.writeCfg()

outputPage(cfg)
	