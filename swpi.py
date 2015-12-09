#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""     Main program """

import time
import sqlite3
import os
import humod 
import config
import webcam
import sys
import urllib2, urllib
import datetime
import camera
from TTLib import *
import version
import sensor_thread
import globalvars
import radio
import ntplib
import meteodata
import math
import service
import tarfile
import signal
import thread
import database
import web_server
import socket
import pluginmanager
import importlib
import subprocess
import cameraPI
import IPCam
import traceback


socket.setdefaulttimeout(30)

################################  functions############################
def reset_sms(modem):
	modem.enable_textmode(True)
	modem.enable_clip(True)	
	modem.enable_nmi(True)
	log ("sms reset")
	

def new_sms(modem, message):
	"""Event Function for new incoming SMS"""
	waitForHandUP()
	log( 'New message arrived: %r' % message)
	msg_num = int(message[12:].strip())
	process_sms(modem,msg_num)

def process_sms(modem, smsID):
	"""Parse SMS number smsID"""
	try:	
		global cfg
		global logFileDate
		msgID = smsID
		smslist = modem.sms_list()
		bFound = False
		for message in smslist:
			if (message[0] == msgID ):
				bFound = True
				break
		if ( not bFound ):
			print "ERROR - SMS not found"
			return();
		
		msgText =  modem.sms_read(msgID)
		msgSender = message[2]
		msgDate = message[4]
		log( "Processind SMS : " + str(msgID) + " - Text:  " +  msgText + "  - Sender :" + msgSender)
	
		command = msgText.split()
		if ( len(command) < 2 ):
			log( "Bad Command .. Deleting")
			modem.sms_del(msgID)
			return False
		pwd = command[0]
		if ( pwd.upper() != cfg.SMSPwd.upper() ):
			log( "Bad SMS Password .. deleting")
			modem.sms_del(msgID)
			return False
		cmd = command[1].upper()
		if ( len(command) == 3 ):
			param = command[2] 
		conn = sqlite3.connect('db/swpi.s3db',200)
		dbCursor = conn.cursor()
		#----------------------------------------------------------------------------------------
		#                                          SMS COMMANDS
		#	command	param	desc
		#
		#	RBT				reboot
		#	HLT				halt	
		#	MDB				mail database to sender
		#	RDB				Reset Database
		#	MCFG			mail cfg to sender
		#	MLOG			mail current logfiles
		#	MALOG			mail all logfiles
		#   BCK				backup
		#   RST             Restore
		#	CAM		X		set camera/logging interval to X seconds
		#	LOG		[0/1]	enable [1] or disable [0] internet data logging
		#	UPL		[0/1]	enable [1] or disable [0] internet data uploading
		#	AOI		[0/1]	set [1] or reset [0] always on internet parameter
		#	UDN		[0/1]	set [1] or reset [0] use dongle net parameter
		#	IP				send sms with current IP to sender
		#	UPD				Update software
		#	WSO		X		set calibration wind speed offset to X 
		#	WSG		X		set calibration wind speed gain to X
		#   CRES    x       Change camera resolution 	0	640x480    
		#												1	800x600
		#												2	1024x768
		#												3	1280x960
		#												4	1400x1050
		#												5	1600x1200
		#												6	2048x1536
		#---------------------------------------------------------------------------------------	
		if (len(command) == 2 and cmd == "RBT" ):
			modem.sms_del(msgID)
			dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
			conn.commit()		
			log( "Receiced rebooting command  " )
			systemRestart()
		#---------------------------------------------------------------------------------------	
		elif (len(command) == 2 and cmd == "BCK" ):
			modem.sms_del(msgID)
			dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
			conn.commit()		
			log( "Receiced backup command  " )
			os.system("backup")
		#---------------------------------------------------------------------------------------	
		elif (len(command) == 2 and cmd == "RST" ):
			modem.sms_del(msgID)
			dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
			conn.commit()		
			log( "Receiced Restore command  " )
			os.system("restore")
		#---------------------------------------------------------------------------------------	
		elif (len(command) == 2 and cmd == "HLT" ):
			modem.sms_del(msgID)
			dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
			conn.commit()		
			log( "Receiced halt command  " )
			systemHalt()
		#---------------------------------------------------------------------------------------	

		elif (len(command) == 2 and cmd == "RDB" ):
			modem.sms_del(msgID)
			dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
			conn.commit()		
			dbCursor.execute("delete from METEO")
			conn.commit()
			log( "Database resetted  " )
		#---------------------------------------------------------------------------------------	
		elif (len(command) == 2 and cmd == "MDB" ):
			modem.sms_del(msgID)
			tarname = "db.tar.gz"
			tar = tarfile.open(tarname, "w:gz")
			tar.add("./db")
			tar.close()
						
			bbConnected = False
			if ( ( not internet_on())  and cfg.UseDongleNet and dongle_detected):
				log( "Trying to connect to internet with 3G dongle ....")
				time.sleep(1)
				modem.connectwvdial()
				time.sleep(2)
				waitForIP()
				bbConnected = True
			
			if ( internet_on() ):
				SendMail(cfg, "DB", "Here your DB", tarname)
				os.remove(tarname)
				dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
				conn.commit()		
				
			if (bbConnected ):
				log("Try to disconnect")
				modem.disconnectwvdial()
				#reset_sms(modem)

				#modem.enable_textmode(True)
				#modem.enable_clip(True)	
				#modem.enable_nmi(True)
				
	
			log( "DB sent by mail" )
			
		#---------------------------------------------------------------------------------------	
		elif (len(command) == 2 and cmd == "MCFG" ):
			modem.sms_del(msgID)
			tarname = "cfg.tar.gz"
			tar = tarfile.open(tarname, "w:gz")
			tar.add("swpi.cfg")
			tar.close()
			bbConnected = False
			if ( ( not internet_on())  and cfg.UseDongleNet and dongle_detected):
				log( "Trying to connect to internet with 3G dongle ....")
				time.sleep(1)
				modem.connectwvdial()
				time.sleep(2)
				waitForIP()
				bbConnected = True
			
			if ( internet_on() ):
				SendMail(cfg, "CFG", "Here your CFG", tarname)
				os.remove(tarname)
				dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
				conn.commit()		
				
			if (bbConnected ):
				log("Try to disconnect")
				modem.disconnectwvdial()
				#reset_sms(modem)
				#modem.enable_textmode(True)
				#modem.enable_clip(True)	
				#modem.enable_nmi(True)
				
	
			log( "CFG sent by mail" )

		#---------------------------------------------------------------------------------------	
		elif (len(command) == 2 and cmd == "MLOG" ):
			modem.sms_del(msgID)
			tarname = "log.tar.gz"
			tar = tarfile.open(tarname, "w:gz")
			filetoadd = "log/log"+logFileDate+".log"
			if ( os.path.isfile(filetoadd) ) :  
				tar.add(filetoadd)
			filetoadd = "log/gphoto2"+logFileDate+".log"
			if ( os.path.isfile(filetoadd) ) :  
				tar.add(filetoadd)				
				tar.close()
			bbConnected = False
			if ( ( not internet_on())  and cfg.UseDongleNet and dongle_detected):
				log( "Trying to connect to internet with 3G dongle ....")
				time.sleep(1)
				modem.connectwvdial()
				time.sleep(2)
				waitForIP()
				bbConnected = True
			
			if ( internet_on() ):
					SendMail(cfg, "LOF", "Here your LOG", tarname)
					os.remove(tarname)
					dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
					conn.commit()		
				
			if (bbConnected ):
				log("Try to disconnect")
				modem.disconnectwvdial()
				#reset_sms(modem)

				#modem.enable_textmode(True)
				#modem.enable_clip(True)	
				#modem.enable_nmi(True)
				
	
			log( "LOG sent by mail" )
			
		
		#---------------------------------------------------------------------------------------	
		elif (len(command) == 2 and cmd == "MALOG" ):
			modem.sms_del(msgID)
			tarname = "alog.tar.gz"
			tar = tarfile.open(tarname, "w:gz")
			tar.add("log")				
			tar.close()
			bbConnected = False
			if ( ( not internet_on())  and cfg.UseDongleNet and dongle_detected):
				log( "Trying to connect to internet with 3G dongle ....")
				time.sleep(1)
				modem.connectwvdial()
				time.sleep(2)
				waitForIP()
				bbConnected = True
			
			if ( internet_on() ):
				SendMail(cfg, "LOF", "Here your LOG", tarname)
				os.remove(tarname)
				dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
				conn.commit()			
				
			if (bbConnected ):
				log("Try to disconnect")
				modem.disconnectwvdial()
				#reset_sms(modem)
				#modem.enable_textmode(True)
				#modem.enable_clip(True)	
				#modem.enable_nmi(True)
				
	
			log( "All LOG sent by mail" )
			
			
		#---------------------------------------------------------------------------------------	
		elif (len(command) > 2 and cmd == "SYS" ):
			modem.sms_del(msgID)
			syscmd = ''.join(command[2:])
			log( 'Executing %r' % syscmd)
			cmd_exec = os.popen(syscmd)
			output = cmd_exec.read()
			
			if ( len(output) > 250 ):
				output = output[:250]
			output = "SYS OK"
			log( 'Sending the output back to %s output: %s' % (msgSender, output))
			modem.sms_send(msgSender, output)
			dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
			conn.commit()		
			systemRestart()
		#---------------------------------------------------------------------------------------		
		elif (len(command) == 3 and cmd == "CAM" ):
			modem.sms_del(msgID)
			WebCamInterval = int(param)
			cfg.setWebCamInterval(WebCamInterval)
			dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
			conn.commit()		
			log( "New CAM interval set to : " + str(cfg.WebCamInterval))
		#---------------------------------------------------------------------------------------	
		elif (len(command) == 3 and cmd == "LOG" ):
			modem.sms_del(msgID)
			if ( param == '0' or param == '1' ):
				cfg.setDataLogging(param)
				dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
				conn.commit()	
				if param == '0':	
					log( "Internet logging disabled ")
				else:
					log( "Internet logging enabled ")
		#---------------------------------------------------------------------------------------		
		elif (len(command) == 3 and cmd == "UPL" ):
			modem.sms_del(msgID)
			if ( param == '0' or param == '1' ):
				cfg.setDataUpload(param)
				dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
				conn.commit()	
				if param == '0':	
					log( "Internet Uploading disabled ")
				else:
					log( "Internet Uploading enabled ")
		#---------------------------------------------------------------------------------------				
		elif (len(command) == 3 and cmd == "AOI" ):
			modem.sms_del(msgID)
			AlwaysOnInternet = param
			cfg.setAlwaysOnInternet(AlwaysOnInternet)
			dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
			conn.commit()		
			log( "New Always On Internet set to : " + cfg.AlwaysOnInternet )
			systemRestart()
		#---------------------------------------------------------------------------------------		
		elif (len(command) == 3 and cmd == "UDN" ):
			modem.sms_del(msgID)
			UseDongleNet = param
			cfg.setUseDongleNet(UseDongleNet)
			dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
			conn.commit()		
			log( "UseDongleNet set to : " + cfg.UseDongleNet )
			systemRestart()
		#---------------------------------------------------------------------------------------		
		elif (len(command) == 2 and cmd == "IP" ):
			modem.sms_del(msgID)
			if ( IP != None and cfg.usedongle  ):
				try:
					modem.sms_send(msgSender, IP)
					log ("SMS sent to %s" % msgSender)
				except:
					log("Error sending IP by SMS")
			dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
			conn.commit()		
			log( "Sent IP" )
		#----------------------------------------------------------------------------		
		elif (len(command) == 3 and cmd == "WSO" ):
			modem.sms_del(msgID)
			cfg.setWindSpeed_offset(param)
			dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
			conn.commit()		
			log( "Wind Speed offset set to : " + str(cfg.windspeed_offset ))
		#---------------------------------------------------------------------------------------		
		elif (len(command) == 3 and cmd == "WSG" ):
			modem.sms_del(msgID)
			cfg.setWindSpeed_gain(param)
			dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
			conn.commit()		
			log( "Wind Speed gain set to : " + str(cfg.windspeed_gain ))
		#---------------------------------------------------------------------------------------		
		elif (len(command) == 3 and cmd == "CRES" ):
			modem.sms_del(msgID)
			cfg.setCamera_resolution(param)
			dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
			conn.commit()		
			log( "Camera_resolution : " + str(cfg.cameradivicefinalresolution ))
		#---------------------------------------------------------------------------------------		
		elif (len(command) == 2 and cmd == "UPD" ):
			modem.sms_del(msgID)
			
			bbConnected = False
			if ( ( not internet_on())  and cfg.UseDongleNet and dongle_detected):
				log( "Trying to connect to internet with 3G dongle ....")
				time.sleep(1)
				modem.connectwvdial()
				time.sleep(2)
				waitForIP()
				bbConnected = True
			
			if ( internet_on() ):
				swpi_update()
				dbCursor.execute("insert into SMS(Number, Date,Message) values (?,?,?)", (msgSender,msgDate,msgText,))
				conn.commit()		
				
			if (bbConnected ):
				log("Try to disconnect")
				modem.disconnectwvdial()
				
	
			log( "SWPI-UPDATE" )
			systemRestart()
		else:
			print "Unknown command"
		#----------------------------------------------------------------------------	
		
		if conn:
			conn.close()
		
		modem.sms_del(msgID)
		#log("alla fine  dei messaggi reset sms")
		reset_sms(modem)	
		return True
	except :
		log( "D - Exept in MSG" )
		modem.sms_del(msgID)
		#log("se errore in sms reset ")
		reset_sms(modem)	
		if conn:
			conn.close()
		return False
		
	
	return True
	
################################################## CALL ##############################################################	
def answer_call(modem, message):
	#global ws
	try:
		if (  globalvars.bCapturingCamera ):
			log("Not answering because capturing camera images")
			return
		
		if (  globalvars.meteo_data.last_measure_time == None or  globalvars.meteo_data.status != 0 ):
			log("Not answering because no valid meteo data yet")
			return		
				
		
		if ( len(message) > 7 and message[:6] == '+CLIP:' ):
			callingNumber = message[6:].split(',')[0]
		else:
			callingNumber = 'Error'
		log( "Receiving call from : " + callingNumber )
		
		delay = (datetime.datetime.now() - globalvars.meteo_data.last_measure_time)
		delay_seconds = int(delay.total_seconds())
		log("Answering with data of %d seconds old" % delay_seconds	)	
		
			
		#prepare list of messages
		listOfMessages = []
		
		listOfMessages.append("./audio/silence05s.raw") 
		
		listOfMessages.append("./audio/hello.raw")
		
		# Message
		listOfMessages.append("./audio/message.raw")
		
		if ( cfg.sensor_type.upper() == "SIMULATE" ):
			listOfMessages.append("./audio/simulate.raw")
			
		if (delay_seconds > 600 ):
			listOfMessages.append("./audio/some_problem.raw") 
	
		if( globalvars.meteo_data.rain_rate_1h != None and globalvars.meteo_data.rain_rate_1h >= 0.001 ):
			listOfMessages.append("./audio/raining.raw")
		
		# Wind Speed and Direction
		listOfMessages.append("./audio/winddirection.raw")
		listOfMessages.append("./audio/" + str(globalvars.meteo_data.wind_dir_code) + ".raw")		
		listOfMessages.append("./audio/from.raw")
		listOfMessages.append("./audio/" + str(int(globalvars.meteo_data.wind_ave)) + ".raw")
		listOfMessages.append("./audio/to.raw")
		
		listOfMessages.append("./audio/" + str(int(globalvars.meteo_data.wind_gust)) + ".raw")
		listOfMessages.append("./audio/km.raw")
	
		if ( globalvars.meteo_data.wind_trend != None ):
			if ( globalvars.meteo_data.wind_trend < - cfg.wind_trend_limit) :
				listOfMessages.append("./audio/winddown.raw")
			if ( globalvars.meteo_data.wind_trend >  cfg.wind_trend_limit) :
				listOfMessages.append("./audio/windup.raw")	
		# Temperature
		if ( globalvars.meteo_data.temp_out != None ):
			listOfMessages.append("./audio/silence05s.raw") 
			listOfMessages.append("./audio/temperature.raw")
			if ( globalvars.meteo_data.temp_out < 0) :
				listOfMessages.append("./audio/minus.raw") 
	
	#			intera =  int( math.floor(abs(globalvars.meteo_data.temp_out)) )
	#			dec = int( (abs(globalvars.meteo_data.temp_out)-intera)*10 )
	#			listOfMessages.append("./audio/temperature.raw")
	#			listOfMessages.append("./audio/" + str(intera) + ".raw")
	#			listOfMessages.append("./audio/comma.raw")
	#			listOfMessages.append("./audio/" + str(dec ) + ".raw")
						
			intera = int(round( abs(globalvars.meteo_data.temp_out) ))
			listOfMessages.append("./audio/" + str(intera) + ".raw")
			listOfMessages.append("./audio/degree.raw")
	
		# Pressure
		if ( globalvars.meteo_data.rel_pressure != None ):
			thousands, rem = divmod(round(globalvars.meteo_data.rel_pressure), 1000) 
			thousands = int(thousands * 1000)
			hundreds, tens = divmod(rem, 100)
			hundreds = int(hundreds * 100)
			tens = int(round(tens))	
			listOfMessages.append("./audio/silence05s.raw") 
			listOfMessages.append("./audio/pressure.raw")
			if ( thousands != 0):
				listOfMessages.append("./audio/" + str(thousands) + ".raw")
			if ( hundreds != 0):
				listOfMessages.append("./audio/" + str(hundreds) + ".raw")
			if ( tens != 0 ):
				listOfMessages.append("./audio/" + str(tens) + ".raw")
			listOfMessages.append("./audio/hpa.raw")	
	
		# Humidity
		if ( globalvars.meteo_data.hum_out != None ):
			listOfMessages.append("./audio/silence05s.raw") 
			intera =  int( globalvars.meteo_data.hum_out) 
			listOfMessages.append("./audio/umidity.raw")
			listOfMessages.append("./audio/" + str(intera) + ".raw")
			listOfMessages.append("./audio/percent.raw")
	
	# 		# Dew point
		if ( globalvars.meteo_data.dew_point != None ):
			listOfMessages.append("./audio/silence05s.raw")
			listOfMessages.append("./audio/dewpoint.raw")
			if ( globalvars.meteo_data.dew_point < 0) :
				listOfMessages.append("./audio/minus.raw")
			intera = int(round( abs(globalvars.meteo_data.dew_point) ))
			listOfMessages.append("./audio/" + str(intera) + ".raw")
			listOfMessages.append("./audio/degree.raw")
	
		#Cloud base
		if (globalvars.meteo_data.cloud_base_altitude != None ) : 
			if ( globalvars.meteo_data.cloud_base_altitude != -1 ) :
				thousands, rem = divmod(round(globalvars.meteo_data.cloud_base_altitude), 1000) 
				thousands = int(thousands * 1000)
				hundreds, tens = divmod(rem, 100)
				hundreds = int(hundreds * 100)
				tens = int(round(tens))	
				listOfMessages.append("./audio/silence05s.raw") 
				listOfMessages.append("./audio/cloudbase.raw")
				if ( thousands != 0):
					listOfMessages.append("./audio/" + str(thousands) + ".raw")
				if ( hundreds != 0):
					listOfMessages.append("./audio/" + str(hundreds) + ".raw")
				if ( tens != 0 ):
					listOfMessages.append("./audio/" + str(tens) + ".raw")
				listOfMessages.append("./audio/meters.raw")
			else:
				listOfMessages.append("./audio/incloud.raw")
	
		
		# Statistics
		if ( globalvars.meteo_data.winDayMin != None ):
			listOfMessages.append("./audio/minday.raw")
			listOfMessages.append("./audio/" + str(int(globalvars.meteo_data.winDayMin)) + ".raw")	
		
		if ( globalvars.meteo_data.winDayMax != None ):	
			listOfMessages.append("./audio/maxday.raw")	
			listOfMessages.append("./audio/" + str(int(globalvars.meteo_data.winDayMax)) + ".raw")
		
	
		
		listOfMessages.append("./audio/silence05s.raw") 		
		listOfMessages.append("./audio/thanks.raw")
		listOfMessages.append("./audio/www.raw")
		listOfMessages.append("./audio/silence05s.raw") 
		listOfMessages.append("./audio/swpi.raw")
			
			
			
		modem.answerCallNew(listOfMessages)
		
		#log to database
		conn = sqlite3.connect('db/swpi.s3db',200)
		dbCursor = conn.cursor()
		dbCursor.execute("insert into CALL(Number) values (?)", (callingNumber,))
		conn.commit()
		conn.close()

	except :
		log("Error in answering %s" % sys.exc_info()[0])
		pass




# Load Configuration
configfile = 'swpi.cfg'
if not os.path.isfile(configfile):
	cfg = config.config(configfile,False)
	os.system( "sudo chown pi swpi.cfg" )

	log("Configurantion file created with default option. Now edit the file :  %s and restart with command  : swpi "  % (configfile))
	#exit(0)
else:
	cfg = config.config(configfile,False)
	

##################################################################################
v = version.Version("VERSION").getVersion()
log( "Starting SINT WIND PI  ... ")
############################ MAIN ###############################################
print "************************************************************************"
print "*                      Sint Wind PI "+v+"                           *"
print "*                                                                      *"
print "*          2012-2015 by Tonino Tarsi  <tony.tarsi@gmail.com>           *"
print "*                                                                      *"
print "*     System will start in 10 seconds - Press Ctrl-C to cancel         *"
print "************************************************************************"
# Get curret log file
globalvars.TimeSetFromNTP = False
globalvars.logFileDate = datetime.datetime.now().strftime("%d%m%Y")
logFileDate = datetime.datetime.now().strftime("%d%m%Y")

SecondsToWait = 10
# give 10 seconds for interrupt the application
try:
	if not ( '-i' in sys.argv ) :
		for i in range(0,SecondsToWait):
			sys.stdout.write(str(SecondsToWait-i) + ".....")
			sys.stdout.flush()
			time.sleep(1)
		print ""
except KeyboardInterrupt:
	#print  "Stopping swpi"
	exit(0)

# Radio Voice output shoud go to the analog device
os.system( "sudo amixer cset numid=3 1 > /dev/null " )

#Make sure every executable is executable
os.system( "sudo chmod +x ./dwcfg.sh" )
os.system( "sudo chmod +x ./usbreset" )
os.system( "sudo chmod +x ./wifi_reset.sh" )
os.system( "sudo chmod +x ./swpi.sh" )
os.system( "sudo chmod +x ./swpi-update.sh" )
os.system( "sudo chmod +x ./killswpi.sh" )
os.system( "sudo chmod +x ./DHT/DHT" )
os.system( "sudo chmod +x ./DHT/DHT_rf" )
os.system( "sudo chmod +x ./wh1080_rf/wh1080_rf" )
os.system( "sudo chmod +x ./wh1080_rf/spi_init" )

os.system( "sudo chown  pi ./DHT" )
os.system( "sudo chown  pi ./mcp3002" )
os.system( "sudo chown  pi ./TX23" )
os.system( "sudo chown  pi ./wh1080_rf" )
os.system( "sudo chown -R pi ./jscolor" )
os.system( "sudo chmod -R 777 ./jscolor" )

if(os.path.isfile("webcamtmp")):
	os.system( "sudo rm ./webcamtmp")
if(os.path.isfile("wget-log")):
	os.system( "sudo rm ./wget-log")


# Some Globasl :-(
globalvars.bAnswering = False
globalvars.bCapturingCamera = False
globalvars.meteo_data = meteodata.MeteoData(cfg)
globalvars.takenPicture = meteodata.CameraFiles()


IP = None
publicIP = None

# Start sensors thread ##
if ( cfg.use_wind_sensor ):
	wind_sensor_thread = sensor_thread.WindSensorThread(cfg)
	wind_sensor_thread.start()

# load plugins
pl = pluginmanager.PluginLoader("./plugins",cfg)
pl.loadAll()
if os.path.exists('./plugins/sync_plugin.py'):
	log("Loading sync plugin")
	from plugins.sync_plugin import *
	plugin_sync = swpi_sync_plugin(cfg)
else:
	plugin_sync = None


# start config eweb server
if ( cfg.config_web_server ):
	webserver = web_server.config_webserver(cfg)
	webserver.start()

# Set Time from NTP ( using a thread to avoid strange freezing )
if ( cfg.set_system_time_from_ntp_server_at_startup ):
	thread.start_new_thread(SetTimeFromNTP, (cfg.ntp_server,)) 

# Init Dongle
bConnected = False

x=os.system("ls " + cfg.dongleDataPort )
if x==0:
	dongle_detected = True
else:
	dongle_detected = False 
	
if ( dongle_detected ):
	modem = humod.Modem(cfg.dongleDataPort,cfg.dongleAudioPort,cfg.dongleCtrlPort,cfg)
else:
	modem = None
	
if cfg.usedongle  :
	if ( dongle_detected ):
		sms_action = (humod.actions.PATTERN['new sms'], new_sms)
		call_action = (humod.actions.PATTERN['incoming callclip'], answer_call)
		actions = [sms_action , call_action]
		modem.prober.start(actions) # Starts the prober.
		#modem.enable_nmi(True)
		reset_sms(modem)
	
		
		print ""
		log( "Modem Model : "  + modem.show_model())
		log(  "Revision : "  + modem.show_revision())
		log(  "Modem Serial Number : " + modem.show_sn())
		log(  "Pin Status : " + modem.get_pin_status())
		log(  "Device Center : " + modem.get_service_center()[0] + " " + str(modem.get_service_center()[1]))
		log(  "Signal quality : " + str(modem.get_rssi()))
	
		log( "Checking new sms messages...")
		smslist = modem.sms_list()
		for message in smslist:
			smsID = message[0]
			process_sms(modem,smsID)
	else:
		log("3G Dongle not detected")

if ( ( not internet_on()) and cfg.UseDongleNet and dongle_detected ):
	log( "Trying to connect to internet with 3G dongle ....")
	time.sleep(1)
	modem.connectwvdial()
	#test
	#modem.enable_nmi(True)
	time.sleep(2)
	waitForIP()
	reset_sms(modem)
	if ( not cfg.AlwaysOnInternet ) :
		bConnected = True

# Get network IP
if (internet_on() ):
	IP = getIP()
	publicIP = getPublicIP()
	if publicIP != None:
		log("Connected with IP :" + publicIP)
else:
	log("Running without internet connection")



if ( cfg.set_time_at_boot.upper() != "NONE"):
	hours=int((cfg.set_time_at_boot.split(":")[0]))
	minutes=int((cfg.set_time_at_boot.split(":")[1]))
	seconds="00"
	date_file = "/home/pi/swpi/date.txt"
	if os.path.exists(date_file):
		in_file = open(date_file,"r")
		text = in_file.read()
		in_file.close()
		now = datetime.datetime.strptime(text, "%Y-%m-%d %H:%M:%S.%f")
	else:
		now = datetime.datetime.now()
		
	new_date = now + datetime.timedelta(days=1)
	d = new_date.replace( hour=hours )
	new_date =  d.replace( minute=minutes )
	os.system("sudo date -s '%s'" %  new_date)
	in_file = open(date_file,"w")
	in_file.write(str(new_date))
	in_file.close()
	
	
# Set Time from NTP ( using a thread to avoid strange freezing )
if ( cfg.set_system_time_from_ntp_server_at_startup ):
	thread.start_new_thread(SetTimeFromNTP, (cfg.ntp_server,)) 

# Send mail with IP information ( using a thread to avoid strange freezing )
if ( publicIP != None and cfg.use_mail and cfg.mail_ip ):
	log("Local IP :" + IP + " Public IP : " + publicIP)
	thread.start_new_thread(SendMail,(cfg, cfg.station_name + " - My IP has changed","Local IP :" + IP + " Public IP : " + publicIP,"")) 
	
if ( publicIP != None and cfg.use_DNSExit) :
	DNSExit(cfg.DNSExit_uname,cfg.DNSExit_pwd,cfg.DNSExit_hname)
	
	
# Send mail with IP information
#if ( IP != None and cfg.use_mail and cfg.mail_ip ):
#	if ( SendMail(cfg,"IP","My IP today is : " + IP ,"") ):
#		log ("Mail sent to :" + cfg.mail_to )
#	else:
#		log ("ERROR sending mail" )

# Send SMS with IP information
if ( publicIP != None and cfg.usedongle and dongle_detected and cfg.send_IP_by_sms  ):
	try:
		modem.sms_send(cfg.number_to_send, publicIP)
		log ("SMS sent to %s" % cfg.number_to_send)
	except:
		log("Error sending IP by SMS")





# Start radio thread
if ( cfg.useradio ):
	radio = radio.RadioThread(cfg)
	radio.start()
	
# Start service thread if necessary
service.run_all_service_thread(cfg)

if bConnected:
	log("Try to disconnect")
	modem.disconnectwvdial()
	reset_sms(modem)
	#modem.enable_textmode(True)
	#modem.enable_clip(True)	
	#modem.enable_nmi(True)
	
# Wait for valid data
maxwait = 0
if ( cfg.use_wind_sensor ) :
	while ( globalvars.meteo_data.last_measure_time == None and maxwait < 120) :
		maxwait = maxwait + 1 
		time.sleep(1)

# clear all sd cards at startup
if ( cfg.usecameradivice ):
	cameras = camera.PhotoCamera(cfg)
	if ( cfg.clear_all_sd_cards_at_startup):
		camera.ClearAllCameraSDCards(cfg)		


	

# Start main thread
############################ MAIN  LOOP###############################################

while 1:
	

	
	bipcam2 = False;
	
	last_data_time = datetime.datetime.now()
	
	if ( plugin_sync != None ):
		plugin_sync.run_before()
		
	
	try:
		#if ( cfg.usedongle ):  log("Signal quality : " + str(modem.get_rssi()))

		if ( cfg.wifi_reset_if_down ) :
			os.system("sudo ./wifi_reset.sh")
		
		# Wait till 45 seconds in case of PCE-FWS20 to avoid USB overload
		if (cfg.use_wind_sensor and cfg.sensor_type == "PCE-FWS20"):
			seconds = datetime.datetime.now().second
			if ( seconds < 45 ):
				time.sleep(45-seconds)
		
		waitForHandUP()  # do to replace with lock object
		# WebCam 1
		if ( cfg.webcamDevice1.upper() != "NONE" ):
			webcam1 =  webcam.webcam(1,cfg)
			img1FileName = "./img/webcam1_" + datetime.datetime.now().strftime("%d%m%Y-%H%M%S.jpg") 
			globalvars.takenPicture.img1FileName = img1FileName
			waitForHandUP()
			bwebcam1 = webcam1.capture(img1FileName)
			if ( bwebcam1 ):
				log( "Webcam 1 Captured : ok : "  + img1FileName )
				addTextandResizePhoto(img1FileName,cfg.webcamdevice1finalresolutionX,cfg.webcamdevice1finalresolutionY,cfg,v)
		# WebCam 2
		if ( cfg.webcamDevice2.upper() != "NONE" ):
			webcam2 =  webcam.webcam(2,cfg)
			img2FileName = "./img/webcam2_" + datetime.datetime.now().strftime("%d%m%Y-%H%M%S.jpg")
			globalvars.takenPicture.img2FileName = img2FileName
			waitForHandUP()
			bwebcam2 = webcam2.capture(img2FileName)
			if ( bwebcam2):
				log( "Webcam 2 Captured : ok : "  + img2FileName	)	
				addTextandResizePhoto(img2FileName,cfg.webcamdevice2finalresolutionX,cfg.webcamdevice2finalresolutionY,cfg,v)	
				
		# Cameras			
		if ( cfg.usecameradivice ):
			waitForHandUP()
			fotos = cameras.take_pictures()
			globalvars.takenPicture.fotos = fotos
			for foto in fotos:
				addTextandResizePhoto(foto,cfg.cameradivicefinalresolutionX,cfg.cameradivicefinalresolutionY,cfg,v)

		# IPCam 1
		if ( cfg.IPCamIP1.upper() != "NONE" ):
			#if (cfg.IPCamCfg.upper() == "IPCAM1" or cfg.IPCamCfg.upper() == "COMBINED"):
			IPCam1 =  IPCam.IPCam(1,cfg)
			img1IPFileName = "./img/webcam1_" + datetime.datetime.now().strftime("%d%m%Y-%H%M%S.jpg") 
			globalvars.takenPicture.img1IPFileName = img1IPFileName
			waitForHandUP()
			bipcam1 = IPCam1.IPCamCapture(img1IPFileName,1)
			if ( bipcam1 ):
				log( "IPcam 1 Captured : ok : "  + img1IPFileName )
				addTextandResizePhoto(img1IPFileName,cfg.webcamdevice1finalresolutionX,cfg.webcamdevice1finalresolutionY,cfg,v)
		#else:		
		# IPCam 2
		if (cfg.IPCamCfg.upper() == "IPCAM2"):
			IPCam2 =  IPCam.IPCam(2,cfg)
			img2IPFileName = "./img/webcam2_" + datetime.datetime.now().strftime("%d%m%Y-%H%M%S.jpg")
			globalvars.takenPicture.img2IPFileName = img2IPFileName
			waitForHandUP()
			bipcam2 = IPCam2.IPCamCapture(img2IPFileName,2)
			if ( bipcam2 ):
				log( "IPcam 2 Captured : ok : "  + img2IPFileName	)	
				addTextandResizePhoto(img2IPFileName,cfg.webcamdevice2finalresolutionX,cfg.webcamdevice2finalresolutionY,cfg,v)	
		
		bcPI = False
		cPIFilemane =""
		if ( cfg.use_cameraPI):
			cPI = cameraPI.cameraPI(cfg)
			cPIFilemane = "./img/raspi_" + datetime.datetime.now().strftime("%d%m%Y-%H%M%S.jpg")
			globalvars.takenPicture.cPIFilemane = cPIFilemane			
			bcPI = cPI.capture(cPIFilemane)
			addTextandResizePhoto(cPIFilemane,cfg.cameradivicefinalresolutionX,cfg.cameradivicefinalresolutionY,cfg,v)

		bConnected = False
		
		if ( cfg.sendImagesToServer or cfg.logdata or cfg.upload_data or cfg.WeatherUnderground_logdata or cfg.PWS_logdata):
			waitForHandUP()
			if ( cfg.UseDongleNet and dongle_detected and ( not internet_on())  and modem._pppd_pid == None): # connect if not
				log( "Trying to connect to internet with 3G dongle")
				modem.connectwvdial()
				IP = waitForIP()
				log("Connected with IP :" + IP)
				if ( IP != None ):
					bConnected = True

			if (  internet_on() ):
				#log("Sending to server ...")
				waitForHandUP()
				if ( cfg.webcamDevice1.upper() != "NONE" and bwebcam1 ):
					if (cfg.sendallimagestoserver ):
						waitForHandUP()
						log("Sending to server "+ img1FileName)
						sendFileToServer(img1FileName,getFileName(img1FileName),cfg.ftpserver,cfg.ftpserverDestFolder,cfg.ftpserverLogin,cfg.ftpserverPassowd,False,cfg.use_thread_for_sending_to_server)
					else:
						waitForHandUP()
						sendFileToServer(img1FileName,"current1.jpg",cfg.ftpserver,cfg.ftpserverDestFolder,cfg.ftpserverLogin,cfg.ftpserverPassowd,False,cfg.use_thread_for_sending_to_server)

				if ( cfg.webcamDevice2.upper() != "NONE" and bwebcam2 ):
					if (cfg.sendallimagestoserver ):
						waitForHandUP()
						sendFileToServer(img2FileName,getFileName(img2FileName),cfg.ftpserver,cfg.ftpserverDestFolder,cfg.ftpserverLogin,cfg.ftpserverPassowd,False,cfg.use_thread_for_sending_to_server)
					else:
						waitForHandUP()
						sendFileToServer(img2FileName,"current2.jpg",cfg.ftpserver,cfg.ftpserverDestFolder,cfg.ftpserverLogin,cfg.ftpserverPassowd,False,cfg.use_thread_for_sending_to_server)
				
				if ( cfg.IPCamCfg.upper() != "NONE" and bipcam1 ):
					if (cfg.sendallimagestoserver ):
						waitForHandUP()
						log("Sending to server "+ img1IPFileName)
						sendFileToServer(img1IPFileName,getFileName(img1IPFileName),cfg.ftpserver,cfg.ftpserverDestFolder,cfg.ftpserverLogin,cfg.ftpserverPassowd,False,cfg.use_thread_for_sending_to_server)
					else:
						waitForHandUP()
						sendFileToServer(img1IPFileName,"current1.jpg",cfg.ftpserver,cfg.ftpserverDestFolder,cfg.ftpserverLogin,cfg.ftpserverPassowd,False,cfg.use_thread_for_sending_to_server)

				if (cfg.IPCamCfg.upper() == "IPCAM2" and bipcam2 ):
					if (cfg.sendallimagestoserver ):
						waitForHandUP()
						sendFileToServer(img2IPFileName,getFileName(img2IPFileName),cfg.ftpserver,cfg.ftpserverDestFolder,cfg.ftpserverLogin,cfg.ftpserverPassowd,False,cfg.use_thread_for_sending_to_server)
					else:
						waitForHandUP()
						sendFileToServer(img2IPFileName,"current2.jpg",cfg.ftpserver,cfg.ftpserverDestFolder,cfg.ftpserverLogin,cfg.ftpserverPassowd,False,cfg.use_thread_for_sending_to_server)

				
				if ( cfg.use_cameraPI and bcPI ): 
					if (cfg.sendallimagestoserver ):
						waitForHandUP()
						sendFileToServer(cPIFilemane,getFileName(cPIFilemane),cfg.ftpserver,cfg.ftpserverDestFolder,cfg.ftpserverLogin,cfg.ftpserverPassowd,False,cfg.use_thread_for_sending_to_server)
					else:
						waitForHandUP()
						sendFileToServer(cPIFilemane,"raspi.jpg",cfg.ftpserver,cfg.ftpserverDestFolder,cfg.ftpserverLogin,cfg.ftpserverPassowd,False,cfg.use_thread_for_sending_to_server)
					
	
				if ( cfg.usecameradivice   ):
					nCamera = 0
					for foto in fotos:
						nCamera = nCamera + 1
						if (cfg.sendallimagestoserver ):
							waitForHandUP()
							log("Sending :" + getFileName(foto))
							sendFileToServer(foto,getFileName(foto),cfg.ftpserver,cfg.ftpserverDestFolder,cfg.ftpserverLogin,cfg.ftpserverPassowd,False,cfg.use_thread_for_sending_to_server)
						else:
							waitForHandUP()
							log("Sending :" + "camera" + str(nCamera+cfg.start_camera_number-1) + ".jpg")
							sendFileToServer(foto,"camera"+str(nCamera+cfg.start_camera_number-1)+".jpg",cfg.ftpserver,cfg.ftpserverDestFolder,cfg.ftpserverLogin,cfg.ftpserverPassowd,False,cfg.use_thread_for_sending_to_server)				
						
				if ( cfg.logdata and  globalvars.meteo_data.last_measure_time != None and  globalvars.meteo_data.status == 0 ) :
					log("Logging data ...")
					logData(cfg.serverfile,cfg.SMSPwd)
					
				if ( cfg.WeatherUnderground_logdata and  globalvars.meteo_data.last_measure_time != None and  globalvars.meteo_data.status == 0 ) :
					log("Logging data to Wunderground ...")
					logDataToWunderground(cfg.WeatherUnderground_ID,cfg.WeatherUnderground_password,cfg.wind_speed_units)	
					

				if ( cfg.upload_data and  globalvars.meteo_data.last_measure_time != None and  globalvars.meteo_data.status == 0 ) :
					log("Uploading data ...")
					UploadData(cfg)		
					
				if ( cfg.CWOP_logdata and  globalvars.meteo_data.last_measure_time != None and  globalvars.meteo_data.status == 0 ) : 
					logDataToCWOP(cfg.CWOP_ID,cfg.CWOP_password,cfg.location_latitude,cfg.location_longitude,v)
			
				if ( cfg.PWS_logdata and  globalvars.meteo_data.last_measure_time != None and  globalvars.meteo_data.status == 0 ) :
					log("Logging data to PWS ...")
					logDataToPWS(cfg.PWS_ID,cfg.PWS_password,cfg.wind_speed_units)	
					
			
			
				thenewIP = getPublicIP()
				if ( thenewIP != None and publicIP != thenewIP ):
					publicIP = thenewIP
					publicIP = getPublicIP()
					log("Public IP : " + publicIP)
					if ( cfg.use_mail and cfg.mail_ip ):
						if ( IP == None ):
							IP = "None" 
						SendMail(cfg,"My IP has changed","Local IP :" + IP + " Public IP : " + publicIP,"")
					if ( cfg.use_DNSExit):
						DNSExit(cfg.DNSExit_uname,cfg.DNSExit_pwd,cfg.DNSExit_hname)
						
				if ( cfg.config_web_server ) :
					log("Rereading config file ..")
					cfg.readCfg(False)
				
				# Set Time from NTP ( using a thread to avoid strange freezing )
				if ( cfg.set_system_time_from_ntp_server_at_startup ):
					thread.start_new_thread(SetTimeFromNTP, (cfg.ntp_server,)) 
				
				if bConnected:
					log("Try to disconnect")
					modem.disconnectwvdial()
					reset_sms(modem)
					#modem.enable_textmode(True)
					#modem.enable_clip(True)	
					#modem.enable_nmi(True)
			else:
				log("Error. Non internet connection available")
			
		#check if all threads are alive
		if cfg.useradio:
			if ( not radio.isAlive()):
				log("Error : Something wrong with radio .. restarting")
				systemRestart()
		if cfg.use_wind_sensor:
			if ( not wind_sensor_thread.isAlive()):
				log("Error : Something wrong with sensors .. restarting ws")
				systemRestart()		
			
		#Check disk space
		disk_space = disk_free()/1000000
		if cfg.usedongle and dongle_detected:
			#log("alla fine")
			reset_sms(modem)
		#modem.enable_nmi(True)
		#log("reset sms")
# 		if ( disk_space < 500000000L ):
# 			log("Clearing /var/log/")
# 			os.system( "sudo rm -r /var/log/*" )
# 		else:
# 			log("Disk space left = %s" % disk_space)	
		
		log("Disk space left = %d Mb" % disk_space)
		
		globalvars.WatchDogTime = datetime.datetime.now()
		
		if ( plugin_sync != None ):
			plugin_sync.run_after()
			

			
		if ( cfg.WebCamInterval != 0):
			tosleep = cfg.WebCamInterval-(datetime.datetime.now()-last_data_time).seconds
			if ( tosleep > 30):
				log("Sleeping %s seconds" % tosleep)
				time.sleep(tosleep)

		
		else:
			log("Sleeping 1000 seconds")
			time.sleep(30)	
			
		# Delete pictures
		if ( cfg.delete_images_on_sd ) :
			if  globalvars.takenPicture.img1FileName != None  :
				deleteFile(globalvars.takenPicture.img1FileName)
			if  globalvars.takenPicture.img2FileName != None  :
				deleteFile(globalvars.takenPicture.img2FileName)
			if (  globalvars.takenPicture.fotos != None  ):
				for foto in globalvars.takenPicture.fotos :
					deleteFile(foto)
			if  globalvars.takenPicture.cPIFilemane != None  :
				deleteFile(globalvars.takenPicture.cPIFilemane)
			if ( globalvars.takenPicture.img1IPFileName != None ) :
				deleteFile(globalvars.takenPicture.img1IPFileName)
			if ( globalvars.takenPicture.img2IPFileName != None ) :
				deleteFile(globalvars.takenPicture.img2IPFileName)
			
		
	except KeyboardInterrupt:
		if cfg.usedongle and dongle_detected:
			modem.prober.stop()
		if ( cfg.useradio):
			radio.stop()
		wind_sensor_thread.stop()
		exit(0)
	
	except Exception,e:
		print e.message
		print e.__class__.__name__
		traceback.print_exc(e)
			
	





