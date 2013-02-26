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

def str2bool(v):
	return v.lower() in ("yes", "true", "t", "1")

def outputPage(cfg):

	in_file = open("template.html","r")
	text_template = in_file.read()
	in_file.close()

	html_template=string.Template(text_template)

	d = dict(location_latitude=cfg.location_latitude)
	d.update(location_longitude=cfg.location_longitude)
	d.update(location_altitude=cfg.location_altitude)
	d.update(reboot_at=cfg.reboot_at)
	d.update(shutdown_at=cfg.shutdown_at)
	d.update(shutdown_hour_before_sunset=cfg.shutdown_hour_before_sunset)
	d.update(set_system_time_from_ntp_server_at_startup=cfg.set_system_time_from_ntp_server_at_startup)
#	if (cfg.set_system_time_from_ntp_server_at_startup ):
#		d.update(selected_True_set_system_time_from_ntp_server_at_startup='selected')
#		d.update(selected_False_set_system_time_from_ntp_server_at_startup='')
#	else:
#		d.update(selected_True_set_system_time_from_ntp_server_at_startup='')
#		d.update(selected_False_set_system_time_from_ntp_server_at_startup='selected')
	d.update(ntp_server=cfg.ntp_server)
	d.update(config_web_server=cfg.config_web_server)
	d.update(wifi_reset_if_down=cfg.wifi_reset_if_down)
	d.update(config_web_server_port=cfg.config_web_server_port)



	d.update(usedongle=cfg.usedongle)
	d.update(AlwaysOnInternet=cfg.AlwaysOnInternet)
	d.update(UseDongleNet=cfg.UseDongleNet)
	d.update(operator=cfg.operator)

	d.update(SMSPwd=cfg.SMSPwd)

	d.update(logdata=cfg.logdata)
	d.update(serverfile=cfg.serverfile)

	d.update(upload_data=cfg.upload_data)
	d.update(upload_folder=cfg.upload_folder)


	d.update(sensor_type=cfg.sensor_type)
	d.update(use_wind_sensor=cfg.use_wind_sensor)
	d.update(number_of_measure_for_wind_dir_average=cfg.number_of_measure_for_wind_dir_average)
	d.update(windspeed_offset=cfg.windspeed_offset)
	d.update(windspeed_gain=cfg.windspeed_gain)
	d.update(windmeasureinterval=cfg.windmeasureinterval)
	d.update(use_bmp085=cfg.use_bmp085)
	d.update(use_tmp36=cfg.use_tmp36)
	d.update(number_of_measure_for_wind_average_gust_calculation=cfg.number_of_measure_for_wind_average_gust_calculation)

	d.update(set_system_time_from_WeatherStation=cfg.set_system_time_from_WeatherStation)


	d.update(webcamDevice1=cfg.webcamDevice1)
	d.update(webcamDevice2=cfg.webcamDevice2)
	d.update(webcamLogo=cfg.webcamLogo)
	d.update(sendImagesToServer=cfg.sendImagesToServer)
	d.update(WebCamInterval=cfg.WebCamInterval)
	d.update(webcamdevice1captureresolution=cfg.webcamdevice1captureresolution)
	d.update(webcamdevice2captureresolution=cfg.webcamdevice2captureresolution)
	d.update(webcamdevice1finalresolution=cfg.webcamdevice1finalresolution)
	d.update(webcamdevice2finalresolution=cfg.webcamdevice2finalresolution)
	d.update(capturewithffmpeg=cfg.capturewithffmpeg)
	d.update(sendallimagestoserver=cfg.sendallimagestoserver)
	d.update(delete_images_on_sd=cfg.delete_images_on_sd)


	d.update(usecameradivice=cfg.usecameradivice)
	d.update(cameradivicefinalresolution=cfg.cameradivicefinalresolution)
	d.update(gphoto2options=cfg.gphoto2options)
	d.update(gphoto2options_Night=cfg.gphoto2options_Night)
	d.update(reset_usb=cfg.reset_usb)
	d.update(clear_all_sd_cards_at_startup=cfg.clear_all_sd_cards_at_startup)
	d.update(start_camera_number=cfg.start_camera_number)
	d.update(gphoto2_capture_image_and_download=cfg.gphoto2_capture_image_and_download)
	d.update(use_camera_resetter=cfg.use_camera_resetter)




	d.update(ftpserver=cfg.ftpserver)
	d.update(ftpserverDestFolder=cfg.ftpserverDestFolder)
	d.update(ftpserverLogin=cfg.ftpserverLogin)
	d.update(ftpserverPassowd=cfg.ftpserverPassowd)
	d.update(use_thread_for_sending_to_server=cfg.use_thread_for_sending_to_server)



	d.update(useradio=cfg.useradio)
	d.update(radiointerval=cfg.radiointerval)

	d.update(gmail_user=cfg.gmail_user)
	d.update(gmail_pwd=cfg.gmail_pwd)
	d.update(mail_to=cfg.mail_to)
	d.update(use_mail=cfg.use_mail)
	d.update(mail_ip=cfg.mail_ip)

	d.update(send_IP_by_sms=cfg.send_IP_by_sms)
	d.update(number_to_send=cfg.number_to_send)

	d.update(WeatherUnderground_logdata=cfg.WeatherUnderground_logdata)
	d.update(WeatherUnderground_ID=cfg.WeatherUnderground_ID)
	d.update(WeatherUnderground_password=cfg.WeatherUnderground_password)

	d.update(use_DNSExit=cfg.use_DNSExit)
	d.update(DNSExit_uname=cfg.DNSExit_uname)
	d.update(DNSExit_pwd=cfg.DNSExit_pwd)
	d.update(DNSExit_hname=cfg.DNSExit_hname)		
	
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
	
	cfg.config_web_server = request['config_web_server'][0]																 
	cfg.set_system_time_from_ntp_server_at_startup = request['set_system_time_from_ntp_server_at_startup'][0]								   
	cfg.ntp_server = request['ntp_server'][0]																		   
	cfg.reboot_at = request['reboot_at'][0]																		   
	cfg.shutdown_at = request['shutdown_at'][0]																		   
	cfg.shutdown_hour_before_sunset = request['shutdown_hour_before_sunset'][0]													   
	cfg.location_latitude = request['location_latitude'][0]																 
	cfg.location_longitude = request['location_longitude'][0]																 
	cfg.location_altitude = request['location_altitude'][0]																 
	cfg.wifi_reset_if_down = request['wifi_reset_if_down'][0]       
	cfg.config_web_server_port = request['config_web_server_port'][0]                                                                 

	cfg.usedongle = request['usedongle'][0]																		   
	cfg.AlwaysOnInternet = request['AlwaysOnInternet'][0]																 
	cfg.UseDongleNet = request['UseDongleNet'][0]																	  
	cfg.operator = request['operator'][0]																		   

	cfg.SMSPwd = request['SMSPwd'][0]																				

	cfg.logdata = request['logdata'][0]																				
	cfg.serverfile = request['serverfile'][0]																		   

	cfg.upload_data = request['upload_data'][0]																		   
	cfg.upload_folder = request['upload_folder'][0]																	  

	cfg.sensor_type = request['sensor_type'][0]																		   
	cfg.use_wind_sensor = request['use_wind_sensor'][0]																	  
	cfg.number_of_measure_for_wind_dir_average = request['number_of_measure_for_wind_dir_average'][0]										
	cfg.windspeed_offset = request['windspeed_offset'][0]																 
	cfg.windspeed_gain = request['windspeed_gain'][0]																	  
	cfg.windmeasureinterval = request['windmeasureinterval'][0]																 
	cfg.use_bmp085 = request['use_bmp085'][0]																		   
	cfg.use_tmp36 = request['use_tmp36'][0]																		   
	cfg.number_of_measure_for_wind_average_gust_calculation = request['number_of_measure_for_wind_average_gust_calculation'][0]						 

	cfg.set_system_time_from_WeatherStation = request['set_system_time_from_WeatherStation'][0]											 

	cfg.webcamDevice1 = request['webcamDevice1'][0]																	  
	cfg.webcamDevice2 = request['webcamDevice2'][0]		
	cfg.webcamLogo = request['webcamLogo'][0]													   
	cfg.sendImagesToServer = request['sendImagesToServer'][0]																 
	cfg.WebCamInterval = request['WebCamInterval'][0]																	  
	cfg.webcamdevice1captureresolution = request['webcamdevice1captureresolution'][0]												  
	cfg.webcamdevice2captureresolution = request['webcamdevice2captureresolution'][0]												  
	cfg.webcamdevice1finalresolution = request['webcamdevice1finalresolution'][0]												  
	cfg.webcamdevice2finalresolution = request['webcamdevice2finalresolution'][0]												  
	cfg.capturewithffmpeg = request['capturewithffmpeg'][0]																 
	cfg.sendallimagestoserver = request['sendallimagestoserver'][0]															
	cfg.delete_images_on_sd = request['delete_images_on_sd'][0]																								   

	cfg.usecameradivice = request['usecameradivice'][0]																	  
	cfg.cameradivicefinalresolution = request['cameradivicefinalresolution'][0]													   
	cfg.gphoto2options = request['gphoto2options'][0]		
	cfg.gphoto2options_Night = request['gphoto2options_Night'][0]																	  
	cfg.reset_usb = request['reset_usb'][0]																		   
	cfg.clear_all_sd_cards_at_startup = request['clear_all_sd_cards_at_startup'][0]												  
	cfg.start_camera_number = request['start_camera_number'][0]																 
	cfg.gphoto2_capture_image_and_download = request['gphoto2_capture_image_and_download'][0]											 
	cfg.use_camera_resetter = request['use_camera_resetter'][0]											 

	cfg.ftpserver = request['ftpserver'][0]																		   
	cfg.ftpserverDestFolder = request['ftpserverDestFolder'][0]																 
	cfg.ftpserverLogin = request['ftpserverLogin'][0]																	  
	cfg.ftpserverPassowd = request['ftpserverPassowd'][0]		
	cfg.use_thread_for_sending_to_server = request['use_thread_for_sending_to_server'][0]		

	cfg.useradio = request['useradio'][0]																		   
	cfg.radiointerval = request['radiointerval'][0]																	  

	cfg.gmail_user = request['gmail_user'][0]																		   
	cfg.gmail_pwd = request['gmail_pwd'][0]																		   
	cfg.mail_to = request['mail_to'][0]																				
	cfg.use_mail = request['use_mail'][0]																		   
	cfg.mail_ip = request['mail_ip'][0]																				

	cfg.send_IP_by_sms = request['send_IP_by_sms'][0]																	  
	cfg.number_to_send = request['number_to_send'][0]	  
	
	cfg.WeatherUnderground_logdata = request['WeatherUnderground_logdata'][0]																	  
	cfg.WeatherUnderground_ID = request['WeatherUnderground_ID'][0]	  	
	cfg.WeatherUnderground_password = request['WeatherUnderground_password'][0]	  	
	

	cfg.use_DNSExit = request['use_DNSExit'][0]																		   
	cfg.DNSExit_uname = request['DNSExit_uname'][0]																				
	cfg.DNSExit_pwd = request['DNSExit_pwd'][0]																		   
	cfg.DNSExit_hname = request['DNSExit_hname'][0]		


		
	# cfg.AlwaysOnInternet = request['AlwaysOnInternet'][0]
	# cfg.UseDongleNet = request['UseDongleNet'][0]

	cfg.writeCfg()



outputPage(cfg)
	