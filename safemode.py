#!/usr/bin/env python
import smtplib
import config
import sys
import time
import os
import tarfile
import datetime
from datetime import datetime
import humod
import subprocess, signal
import urllib2
import socket
import filecmp
import logging
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders

def new_sms(modem, message):
	logger.debug('new sms')
	msg_num = int(message[12:].strip())
	process_sms(modem,msg_num)

def process_sms(modem, smsID):
	logger.debug('process_sms')
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
			logger.error('SMS not found')
			return();
		
		msgText =  modem.sms_read(msgID)
		msgSender = message[2]
		msgDate = message[4]
		command = msgText.split()
		if ( len(command) < 2 ):
			modem.sms_del(msgID)
			return False
		pwd = command[0]
		if ( pwd.upper() != cfg.SMSPwd.upper() ):
			modem.sms_del(msgID)
			return False
		cmd = command[1].upper()
		if ( len(command) == 3 ):
			param = command[2] 
		if (len(command) == 2 and cmd == "RBT" ):
			modem.sms_del(msgID)
			logger.debug('SMS RBT')
			os.system("sudo reboot")
		if (len(command) == 2 and cmd == "MALOG" ):
			modem.sms_del(msgID)
			logger.debug('SMS MALOG')
			tarname = "alog.tar.gz"
			tar = tarfile.open(tarname, "w:gz")
			tar.add("log")
			tar.close()
			if  not internet() :
				logger.debug('No internet')
				connetti()
			
			if ( internet() ):
				logger.debug('Internet ok send email')
				send_email(cfg.gmail_user, cfg.mail_to, "Cartella Log Swpi", "allegato log", cfg.gmail_user,cfg.gmail_pwd,tarname)
				logger.debug('email: ' + cfg.gmail_user + cfg.mail_to + "Cartella Log Swpi" +message +cfg.gmail_user + cfg.gmail_pwd)
				os.remove(tarname)
			else:
				inviasms()
	
		if (len(command) == 2 and cmd == "SSH" ):
			logger.debug('SMS SSH')
			modem.sms_del(msgID)
			if  not internet() :
				logger.debug('internet ko')
				connetti()

			if ( internet() ):
				message = "Problemi ip:" + trovaip()+ " ip pubblico:" + getPublicIP()
				send_email(cfg.gmail_user, cfg.mail_to, "Problemi swpi", message, cfg.gmail_user,cfg.gmail_pwd,"")
				logger.debug('email: ' + cfg.gmail_user + cfg.mail_to + "Cartella Log Swpi" +message +cfg.gmail_user + cfg.gmail_pwd)
			else:
				inviasms()

		if (len(command) == 2 and cmd == "IP" ):
			modem.sms_del(msgID)
			modem.sms_send(msgSender, getPublicIP())
		modem.sms_del(msgID)
		return True
	except :
		modem.sms_del(msgID)
		return False
	return True


def standby():
	logger.debug('check standby')
	d1 = datetime.strptime(time.ctime(os.stat("db/swpi.s3db").st_mtime), "%a %b %d %H:%M:%S %Y")
	d2 = datetime.strptime(datetime.today().strftime("%a %b %d %H:%M:%S %Y"), "%a %b %d %H:%M:%S %Y")
	return (d2-d1).seconds / 60



def checkswpi():
    try:
       	logger.debug('check swpi run')
	if int(os.popen('ps ax | grep swpi.py | grep -v -c grep').readline()) > 0:
            return True
        else:
            return False
    except Exception, e:
            return False


def killprocess(processo):
	logger.debug('kill process '+ processo)
	p = subprocess.Popen(['ps', '-aef'], stdout=subprocess.PIPE)
	out, err = p.communicate()
	for line in out.splitlines():
		if processo in line:
			pid = int(line.split(None, 2)[1])
			os.kill(pid, signal.SIGKILL)

def scrivifile(nomefile,valore):
	out_file = open(nomefile,"w")
	out_file.write(str(valore))
	out_file.close()
	
def leggifile(nomefile):
	in_file = open(nomefile,"r")
	text = int(in_file.read())
	in_file.close()
	return text



def internet():
	try:
		logger.debug('check internet')
		urllib2.urlopen("http://www.google.com").close()
	except urllib2.URLError:
		return False
	else:
		return True


def connetti():
	logger.debug('check internet')
	if not internet():
		i=0	
		while (i < 3):
			logger.debug('internet ko')
			killprocess("wvdial")
			killprocess("pppd")
			#os.system("kill -INT `ps | grep wvdial | grep -v grep | awk '{print $1}'` & /etc/ppp/ppp-stop")
			os.fork()
			logger.debug('try connect 3G..')
			os.system("wvdial -C " + cfg.operator + ".conf 2>> log/safewdial.log")
			logger.debug('continuo dopo wvdial')
			time.sleep(10)
			i=i+1
			if internet():
				logger.debug('internet ok')
				break

def sms_on():
	logger.debug('reset sms on')
	modem.enable_textmode(True)
	modem.enable_clip(True)
	modem.enable_nmi(True)
	sms_action = (humod.actions.PATTERN['new sms'], new_sms)
	actions = [sms_action]
	modem.prober.start(actions) 
	

def send_email(send_from, send_to, subject, text, login, password, files, server="smtp.gmail.com:587"):
	msg = MIMEMultipart()
	msg['From'] = send_from
	msg['To'] = send_to
	msg['Subject'] = subject
	msg.attach( MIMEText(text) )
	if (files != "" ):
		part = MIMEBase('application', "octet-stream")
		part.set_payload( open(files,"rb").read() )
		Encoders.encode_base64(part)
		part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(files))
		msg.attach(part)
	smtp = smtplib.SMTP(server)
	smtp.starttls()
	smtp.login(login,password)
	smtp.sendmail(send_from, send_to, msg.as_string())
	smtp.close()


def trovaip():
	logger.debug('find ip public ')	
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("gmail.com",80))
	return (s.getsockname()[0])
	s.close()
def getPublicIP():
	try:
		ip = urllib2.urlopen('http://ip.42.pl/raw').read()
		logger.debug('find ip public '+ip)		
		return ip
	except Exception, e:
		return ""
	
def controlloswpi():
	killprocess("swpi.py")
	if ( not internet() ):
		connetti()
	if ( internet() ):
		message = "Problemi SwPi ip:" + trovaip()+ " ip pubblico:" + getPublicIP()
		logger.debug('send email')
		send_email(cfg.gmail_user, cfg.mail_to, "Problemi SwPi", message, cfg.gmail_user,cfg.gmail_pwd,"")
		sms_on()
		#raw_input("Wait...")
		time.sleep(72000)
	else:
		inviasms()
		logger.debug('send sms')
		sms_on()
		#raw_input("Wait...")
		time.sleep(72000)


def inviasms():
	logger.debug('send sms to admin internet problem')	
	modem.enable_textmode(True)
	modem.sms_send(cfg.number_to_send, "Problemi SwPi ip:" + getPublicIP())

os.chdir("/home/pi/swpi")
logger = logging.getLogger('safemode')
hdlr = logging.FileHandler('log/safemode.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.DEBUG)

logger.debug('start script')


if not(os.path.exists("swpibak.cfg")):
	os.system("sudo cp swpi.cfg swpibak.cfg")
	logger.debug('create copy of swpi.cfg')


if (filecmp.cmp('swpibak.cfg', 'swpi.cfg')):
	os.system("sudo cp swpi.cfg swpibak.cfg")
	logger.debug('cfg file is changed-new copy')


configfile = 'swpibak.cfg'
cfg = config.config(configfile,False)
logger.debug('Wait for first control')
modem = humod.Modem(cfg.dongleDataPort,cfg.dongleAudioPort,cfg.dongleCtrlPort,cfg)

time.sleep(240)

while True:
	if checkswpi():
		logger.debug('SwPi work')
		if standby()>10:
			logger.error('SwPi not Update')
			controlloswpi()
		else:
			logger.debug('Swpi ok')
	else:
		logger.error('SwPi not Work')
		controlloswpi()
		
	logger.debug('Wait for new check')
	time.sleep(780)
