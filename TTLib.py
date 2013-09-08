###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################
#                      Generic function Library
import ftplib
import urllib2
import os
import datetime
import socket
import Image
import ImageFont
import ImageDraw
import time
import datetime
import config    
import globalvars
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import urllib,urllib2
import cmath ,math
import json
import tempfile    
#import sensor_simulator
import ntplib
import tarfile
import thread
import os
import requests

socket.setdefaulttimeout(30)


def disk_free():
    """Return disk usage statistics about the given path.

    Returned valus is a named tuple with attributes 'total', 'used' and
    'free', which are the amount of total, used and free space, in bytes.
    """
    path = "/"
    st = os.statvfs(path)
    free = st.f_bavail * st.f_frsize
    #total = st.f_blocks * st.f_frsize
    #used = (st.f_blocks - st.f_bfree) * st.f_frsize
    return free

def linreg(X, Y):
    N = len(X)
    Sx = Sy = Sxx = Syy = Sxy = 0.0
    for x, y in zip(X, Y):
        Sx = Sx + x
        Sy = Sy + y
        Sxx = Sxx + x*x
        #Syy = Syy + y*y
        Sxy = Sxy + x*y
    det = Sxx * N - Sx * Sx
    return (Sxy * N - Sy * Sx)/det


class RingBuffer(object):
    def __init__(self, size):
        self.data = [None for i in xrange(size)]

    def append(self, x):
        self.data.pop(0)
        self.data.append(x)

    def get(self):
        return self.data
    
    def getMean(self):
        i = 0
        s = 0
        for val in self.data:
            if val != None:
                #print val
                i = i+1
                s = s+val
        if ( i == 0 ):
            return None
        else:       
            return (s/float(i))

    def getMeanDir(self):
        s = 0
        for val in self.data:
            if val != None:
                s = s + cmath.rect(1, math.radians(val)) 
        return math.degrees(cmath.phase(s))


    def getMeanMax(self):
        i = 0
        s = 0
        maxval = None
        for val in self.data:
            if val != None:
                #print val
                i = i+1
                s = s+val
                if ( maxval == None ):
                    maxval = val
                else:
                    maxval = max(maxval,val)
        if ( i == 0 ):
            return None,None
        else:
            return (s/float(i)),maxval
        
    def getTrend(self):
        if self.get()[0] == None:
            return None
        reg = linreg(range(len(self.get())),self.get())
        #print self.get()
        #print reg
        if ( reg != None):
            return reg * 60
        else:
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




def swpi_update():
    url = ' http://www.vololiberomontecucco.it/swpi/swpi-src.tar.gz'
    urllib.urlretrieve(url,filename='swpi-src.tar.gz')
    t = tarfile.open('swpi-src.tar.gz', 'r:gz')
    t.extractall('../')  
    os.remove("swpi-src.tar.gz")
    os.system( "sudo chown pi mcp3002/" )
    os.system( "sudo chown pi TX23/" )


def SetTimeFromNTP(ntp_server):
    try:
        c = ntplib.NTPClient()
        date_str = c.request(ntp_server, version=3,timeout=10)
        if (date_str != None ):
            os.system("sudo date -s '%s'" %  time.ctime(date_str.tx_time))
            log("System time adjusted from NPT server : " + ntp_server)
            globalvars.TimeSetFromNTP = True 
            return True
        return False
    except:
        log("ERROR - Failed to set time system from ntp server")
        return False
       
def DNSExit(uname,pwd,hname):
    ip = getPublicIP()
    if ( ip == None):
        return
    params = {
        'login':uname,
        'password':pwd,
        'host':hname,
        'myip':ip}
    posturl = "http://update.dnsexit.com/RemoteUpdate.sv"
    
    try:
        r = requests.get(posturl, params=params,timeout=10)
        log("DNS Exit -: " +  r.text)
        return True
    except:
        log("Error DNS Exit"  ) 
        return False   
        
    
#    posturl = posturl + "?"
#    for key in params:
#        posturl = (posturl + "&" + str(key) + "=" +  str(params[key]) )
#    req = urllib2.Request(posturl)
#    #print req
#    try:
#        resp= urllib2.urlopen(req,timeout=10)
#        page= resp.read()
#        tolog = True
#        status,msg = page.split('\n')
#        status_code = status.split()[1]
#        msg_code,msg_content = msg.split('=')
#        if msg_code == "0":
#            log("DNS Exit - Successfully Updated IP for host:%s"%hname)
#            return True
#        elif msg_code in ["2","3","10"]:
#            log("DNS Exit -Error Updating Dynamic IP:%s"%msg_content)
#            return False
#        else:
#            log("DNS Exit - Error with Connection:%s"%msg_content)
#            return False
#
#    except Exception,err:
#        log("DNS Exit - Unexpected Error occured with the service")
#        return False
        
    return True

def logDataToCWOP(CWOP_ID,CWOP_password,location_latitude,location_longitude,swpi_version=""):
    # http://pond1.gladstonefamily.net:8080/aprswxnet.html
    log("Logging to CWOP server ...")
    if ( globalvars.meteo_data.last_measure_time == None):
        return False
    
    delay = (datetime.datetime.now() - globalvars.meteo_data.last_measure_time)
    delay_seconds = int(delay.total_seconds())
    
    if ( delay_seconds > 120 ):
        return False
    
    
    send = ""
    
    send += CWOP_ID
    send += ">APRS,TCPXX*:"
    
    d = (datetime.datetime.utcnow())
    aprs_time = d.strftime("%d%H%M")
    send += "/" + aprs_time + "z"
 
    lat = abs(location_latitude)
    d = int(lat)
    p = (lat-d)*60
    location = "%2d%5.2f" % (d,p)
    if (location_latitude) > 0:
        location += "N"
    else:
        location += "S"
    
    location += "/"
    
        
    lon = abs(location_longitude)
    d = int(lon)
    p = (lon-d)*60
    location += "%03d%5.2f" % (d,p)
    if (location_longitude) > 0:
        location += "E"
    else:
        location += "W"
    
    send += location
    
    if ( globalvars.meteo_data.wind_dir != None):
        direction = "%03.0f" % float(globalvars.meteo_data.wind_dir)
        send += "_"+direction

    # average wind speed
    if (globalvars.meteo_data.wind_ave != None):
        wind_speed =  globalvars.meteo_data.wind_ave *  0.621371192   
        wind_str = '/' + "%03.0f" % wind_speed
        send += wind_str

    # wind gust
    if (globalvars.meteo_data.wind_gust != None ):
        wind_gust= globalvars.meteo_data.wind_gust * 0.621371192
        wind_gust_str = 'g' + "%03.0f" % wind_gust
        send += wind_gust_str

    # temp
    if ( globalvars.meteo_data.temp_out != None):
        temp_in_f = ( globalvars.meteo_data.temp_out * 1.8 ) + 32
        temp_str = "t" + "%03.0f" % temp_in_f
        send += temp_str

    # rain last hour -- each count is 0.0204" 
    if (globalvars.meteo_data.rain_rate_1h != None):
        rain_hr_hundredth_inches = int(globalvars.meteo_data.rain_rate_1h  * 0.0393700787)
        rain_hr_str = "r" + "%03d" % rain_hr_hundredth_inches
        send += rain_hr_str

    # rain last 24 hours -- each count is 0.0204"
    # so the math accidentally scales perfect -- report in hundreths of inches
    if (globalvars.meteo_data.rain_rate_24h != None) :
        rain_24_hrs_hundredth_inches = int(globalvars.meteo_data.rain_rate_24h  * 0.0393700787)
        rain_24_hrs_str = "p" + "%03d" % rain_24_hrs_hundredth_inches
        send += rain_24_hrs_str

    # skip rain since midnight
    if (globalvars.meteo_data.rain_rate != None ) :
        rain_today_hundredth_inches = int(globalvars.meteo_data.rain_rate  * 0.0393700787)
        rain_midnight_str = "P" + "%03d" % rain_today_hundredth_inches
        send += rain_midnight_str

    # humidity
    if (globalvars.meteo_data.hum_out != None):
        rh = float(globalvars.meteo_data.hum_out / 100 )
        if rh >= 0.995:
            humid_str = "h00"
        else:
            humid_str = "h" + "%02.0f" % (rh * 100.0)
        send += humid_str

    # barometric pressure (in tenths of millibars)
    if (globalvars.meteo_data.rel_pressure != None ) :
        baro = float(globalvars.meteo_data.rel_pressure  *    10)
        baro_str = "b" + "%05.0f"%baro
        send += baro_str

    # equipment used
    equip_str = ".Sint Wind PI - "+swpi_version
    send += equip_str
    

    #log(send)
    
    # Don't send errors in the case that connect fails...
    try:
        HOST = 'cwop.aprs.net'
        PORT = 14580
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST,PORT))
        s.send('user '+ CWOP_ID +' pass ' + CWOP_password + ' vers linux-1wire 1.00\r\n')
        time.sleep(3)
        s.send(send+'\r\n')
        s.close()
        log(CWOP_ID + " Ok")
    except:
        log(CWOP_ID + " ERROR")
        s.close()
        return False



    return True



def logDataToWunderground(ID,password,wind_speed_units="kmh"):

    if ( globalvars.meteo_data.last_measure_time == None):
        return
    
    delay = (datetime.datetime.now() - globalvars.meteo_data.last_measure_time)
    delay_seconds = int(delay.total_seconds())
    
    if ( delay_seconds > 120 ):
        return


    serverfile = "http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"

    parameters = {}
    parameters['action'] = "updateraw"
    parameters['ID'] = ID
    parameters['PASSWORD'] = password
    parameters['dateutc'] = str(datetime.datetime.utcnow())
    
    if globalvars.meteo_data.wind_dir != None :  parameters['winddir'] = int(globalvars.meteo_data.wind_dir)
    if ( wind_speed_units == "kmh" ):
        if globalvars.meteo_data.wind_ave != None :  parameters['windspeedmph'] = "{:.2f}".format(globalvars.meteo_data.wind_ave *  0.621371192)
        if globalvars.meteo_data.wind_gust != None :  parameters['windgustmph'] = "{:.2f}".format(globalvars.meteo_data.wind_gust * 0.621371192)
    else:
        if globalvars.meteo_data.wind_ave != None :  parameters['windspeedmph'] = "{:.2f}".format((globalvars.meteo_data.wind_ave / 0.539956803456  ) *  0.621371192)
        if globalvars.meteo_data.wind_gust != None :  parameters['windgustmph'] = "{:.2f}".format((globalvars.meteo_data.wind_gust / 0.539956803456  ) * 0.621371192)  
    if globalvars.meteo_data.hum_out != None :  parameters['humidity'] = "{:.1f}".format(globalvars.meteo_data.hum_out )
    if globalvars.meteo_data.temp_out != None :  parameters['tempf'] = "{:.2f}".format(( globalvars.meteo_data.temp_out * 1.8 ) + 32) 
    if globalvars.meteo_data.rel_pressure != None :  parameters['baromin'] = "{:.4f}".format(globalvars.meteo_data.rel_pressure  *    0.0295299830714) #new
    if globalvars.meteo_data.dew_point != None :  parameters['dewptf'] = "{:.2f}".format(( globalvars.meteo_data.dew_point * 1.8 ) + 32)
    if globalvars.meteo_data.rain_rate != None :  parameters['dailyrainin'] = "{:.4f}".format(globalvars.meteo_data.rain_rate  * 0.0393700787)
    if globalvars.meteo_data.rain_rate_1h != None :  parameters['rainin'] = "{:.4f}".format(globalvars.meteo_data.rain_rate_1h  * 0.0393700787)
    parameters['softwaretype'] = "Sint Wind PI"
        
    #print  parameters   
    try:
        r = requests.get(serverfile, params=parameters,timeout=10)
        msg = r.text.splitlines()
        log("Log to Wunderground : " +  msg[0])
    except:
        log(  "Error Logging to Wunderground : "  )    
        
        
#    try:
#        serverfile = serverfile + "?"
#        for key in parameters:
#            serverfile = (serverfile + "&" + str(key) + "=" +  str(parameters[key]) )
#        print serverfile
#        req=urllib2.Request(serverfile)
#        log("Sending request to Wunderground") 
#        page=urllib2.urlopen(req,timeout=10).read()
#        log( "Log to Wunderground : " + page )
#    except:
#        log(  "Error Logging to Wunderground : "  )

     
      

def logData(serverfile,SMSPwd):
    
    if ( globalvars.meteo_data.last_measure_time == None):
        return
    
    delay = (datetime.datetime.now() - globalvars.meteo_data.last_measure_time)
    delay_seconds = int(delay.total_seconds())
    
    if ( delay_seconds > 120 ):
        return
    
    mydata = {} 
    mydata['pwd'] = SMSPwd
    mydata['last_measure_time'] = NoneToNull(globalvars.meteo_data.last_measure_time)
    mydata['idx'] = NoneToNull(globalvars.meteo_data.idx)
    mydata['wind_dir_code'] = NoneToNull(globalvars.meteo_data.wind_dir_code)
    mydata['wind_dir'] = NoneToNull(globalvars.meteo_data.wind_dir)
    mydata['wind_ave'] = NoneToNull(globalvars.meteo_data.wind_ave)
    mydata['wind_gust'] = NoneToNull(globalvars.meteo_data.wind_gust)
    mydata['temp_out'] = NoneToNull(globalvars.meteo_data.temp_out)
    mydata['abs_pressure'] = NoneToNull(globalvars.meteo_data.abs_pressure)
    mydata['rel_pressure'] = NoneToNull(globalvars.meteo_data.rel_pressure)
    mydata['hum_out'] = NoneToNull(globalvars.meteo_data.hum_out)
    mydata['rain'] = NoneToNull(globalvars.meteo_data.rain)
    mydata['rain_rate'] = NoneToNull(globalvars.meteo_data.rain_rate)
    mydata['temp_in'] = NoneToNull(globalvars.meteo_data.temp_in)
    mydata['hum_in'] = NoneToNull(globalvars.meteo_data.hum_in)
    mydata['wind_chill'] = NoneToNull(globalvars.meteo_data.wind_chill)
    mydata['temp_apparent'] = NoneToNull(globalvars.meteo_data.temp_apparent)
    mydata['dew_point'] = NoneToNull(globalvars.meteo_data.dew_point)
    mydata['uv'] = NoneToNull(globalvars.meteo_data.uv)
    mydata['illuminance'] = NoneToNull(globalvars.meteo_data.illuminance)
    mydata['winDayMin'] = NoneToNull(globalvars.meteo_data.winDayMin)
    mydata['winDayMax'] = NoneToNull(globalvars.meteo_data.winDayMax)
    mydata['winDayGustMin'] = NoneToNull(globalvars.meteo_data.winDayGustMin)
    mydata['winDayGustMax'] = NoneToNull(globalvars.meteo_data.winDayGustMax)
    mydata['TempOutMin'] = NoneToNull(globalvars.meteo_data.TempOutMin)
    mydata['TempOutMax'] = NoneToNull(globalvars.meteo_data.TempOutMax)
    mydata['TempInMin'] = NoneToNull(globalvars.meteo_data.TempInMin)
    mydata['TempInMax'] = NoneToNull(globalvars.meteo_data.TempInMax)
    mydata['UmOutMin'] = NoneToNull(globalvars.meteo_data.UmOutMin)
    mydata['UmOutMax'] = NoneToNull(globalvars.meteo_data.UmOutMax)
    mydata['UmInMin'] = NoneToNull(globalvars.meteo_data.UmInMin)
    mydata['UmInMax'] = NoneToNull(globalvars.meteo_data.UmInMax)
    mydata['PressureMin'] = NoneToNull(globalvars.meteo_data.PressureMin)
    mydata['PressureMax'] = NoneToNull(globalvars.meteo_data.PressureMax)
    mydata['wind_dir_ave'] = NoneToNull(globalvars.meteo_data.wind_dir_ave)
    mydata['rain_rate_24h'] = NoneToNull(globalvars.meteo_data.rain_rate_24h)
    mydata['rain_rate_1h'] = NoneToNull(globalvars.meteo_data.rain_rate_1h)
    
    
    try:
        r = requests.post(serverfile, data=mydata,timeout=10)
        log( "Data sent to server : " + r.text )
    except:
        log(  "Error connecting to server : " + serverfile )
    

    
#    mydata = [] 

#    mydata.append(('pwd', SMSPwd))
#
#    
#    mydata.append(('last_measure_time',NoneToNull(globalvars.meteo_data.last_measure_time)))
#    mydata.append(('idx',NoneToNull(globalvars.meteo_data.idx)))
#    mydata.append(('wind_dir_code',NoneToNull(globalvars.meteo_data.wind_dir_code)))
#    mydata.append(('wind_dir',NoneToNull(globalvars.meteo_data.wind_dir)))
#    mydata.append(('wind_ave',NoneToNull(globalvars.meteo_data.wind_ave)))
#    mydata.append(('wind_gust',NoneToNull(globalvars.meteo_data.wind_gust)))
#    mydata.append(('temp_out',NoneToNull(globalvars.meteo_data.temp_out)))
#    mydata.append(('abs_pressure',NoneToNull(globalvars.meteo_data.abs_pressure)))
#    mydata.append(('rel_pressure',NoneToNull(globalvars.meteo_data.rel_pressure)))
#    mydata.append(('hum_out',NoneToNull(globalvars.meteo_data.hum_out)))
#    mydata.append(('rain',NoneToNull(globalvars.meteo_data.rain)))
#    mydata.append(('rain_rate',NoneToNull(globalvars.meteo_data.rain_rate)))
#    mydata.append(('temp_in',NoneToNull(globalvars.meteo_data.temp_in)))
#    mydata.append(('hum_in',NoneToNull(globalvars.meteo_data.hum_in)))
#    mydata.append(('wind_chill',NoneToNull(globalvars.meteo_data.wind_chill)))
#    mydata.append(('temp_apparent',NoneToNull(globalvars.meteo_data.temp_apparent)))
#    mydata.append(('dew_point',NoneToNull(globalvars.meteo_data.dew_point)))
#    mydata.append(('uv',NoneToNull(globalvars.meteo_data.uv)))
#    mydata.append(('illuminance',NoneToNull(globalvars.meteo_data.illuminance)))
#    mydata.append(('winDayMin',NoneToNull(globalvars.meteo_data.winDayMin)))
#    mydata.append(('winDayMax',NoneToNull(globalvars.meteo_data.winDayMax)))
#        
#    mydata.append(('winDayGustMin',NoneToNull(globalvars.meteo_data.winDayGustMin)))
#    mydata.append(('winDayGustMax',NoneToNull(globalvars.meteo_data.winDayGustMax)))
#    
#    mydata.append(('TempOutMin',NoneToNull(globalvars.meteo_data.TempOutMin)))
#    mydata.append(('TempOutMax',NoneToNull(globalvars.meteo_data.TempOutMax)))
#    
#    mydata.append(('TempInMin',NoneToNull(globalvars.meteo_data.TempInMin)))
#    mydata.append(('TempInMax',NoneToNull(globalvars.meteo_data.TempInMax)))
#    
#    mydata.append(('UmOutMin',NoneToNull(globalvars.meteo_data.UmOutMin)))
#    mydata.append(('UmOutMax',NoneToNull(globalvars.meteo_data.UmOutMax)))
#    
#    mydata.append(('UmInMin',NoneToNull(globalvars.meteo_data.UmInMin)))
#    mydata.append(('UmInMax',NoneToNull(globalvars.meteo_data.UmInMax)))
#    
#    mydata.append(('PressureMin',NoneToNull(globalvars.meteo_data.PressureMin)))
#    mydata.append(('PressureMax',NoneToNull(globalvars.meteo_data.PressureMax)))
#    
#       
#    mydata.append(('wind_dir_ave',NoneToNull(globalvars.meteo_data.wind_dir_ave)))
#
#    
#    mydata.append(('rain_rate_24h',NoneToNull(globalvars.meteo_data.rain_rate_24h)))
#    mydata.append(('rain_rate_1h',NoneToNull(globalvars.meteo_data.rain_rate_1h)))
#        
#    
#    mydata=urllib.urlencode(mydata)
#    
#    
#    try:
#        req=urllib2.Request(serverfile, mydata)
#        req.add_header("Content-type", "application/x-www-form-urlencoded")
#        page=urllib2.urlopen(req,timeout=10).read()
#        log( "Data sent to server : " + page )
#    except:
#        log(  "Error connecting to server : " + serverfile )
#        pass

def UploadData(cfg):
    
    if ( globalvars.meteo_data.last_measure_time == None):
        return
    
    delay = (datetime.datetime.now() - globalvars.meteo_data.last_measure_time)
    delay_seconds = int(delay.total_seconds())
    
    if ( delay_seconds > 120 ):
        return
    
    mydata = {} 
    mydata['last_measure_time'] = (globalvars.meteo_data.last_measure_time.strftime("[%d/%m/%Y-%H:%M:%S]"))
    mydata['idx'] = (globalvars.meteo_data.idx.strftime("[%d/%m/%Y-%H:%M:%S]"))
    mydata['wind_dir_code'] = (globalvars.meteo_data.wind_dir_code)
    mydata['wind_dir'] = (globalvars.meteo_data.wind_dir)
    mydata['wind_ave'] = (globalvars.meteo_data.wind_ave)
    mydata['wind_gust'] = (globalvars.meteo_data.wind_gust)
    mydata['temp_out'] = (globalvars.meteo_data.temp_out)
    mydata['abs_pressure'] = (globalvars.meteo_data.abs_pressure)
    mydata['rel_pressure'] = (globalvars.meteo_data.rel_pressure)
    mydata['hum_out'] = (globalvars.meteo_data.hum_out)
    mydata['rain'] = (globalvars.meteo_data.rain)
    mydata['rain_rate'] = (globalvars.meteo_data.rain_rate)
    mydata['temp_in'] = (globalvars.meteo_data.temp_in)
    mydata['hum_in'] = (globalvars.meteo_data.hum_in)
    mydata['wind_chill'] = (globalvars.meteo_data.wind_chill)
    mydata['temp_apparent'] = (globalvars.meteo_data.temp_apparent)
    mydata['dew_point'] = (globalvars.meteo_data.dew_point)
    mydata['cloud_base_altitude'] = (globalvars.meteo_data.cloud_base_altitude)

    mydata['uv'] = (globalvars.meteo_data.uv)
    mydata['illuminance'] = (globalvars.meteo_data.illuminance)
    mydata['winDayMin'] = (globalvars.meteo_data.winDayMin)
    mydata['winDayMax'] = (globalvars.meteo_data.winDayMax)
        
    mydata['winDayGustMin'] = (globalvars.meteo_data.winDayGustMin)
    mydata['winDayGustMax'] = (globalvars.meteo_data.winDayGustMax)
    
    mydata['TempOutMin'] = (globalvars.meteo_data.TempOutMin)
    mydata['TempOutMax'] = (globalvars.meteo_data.TempOutMax)
    
    mydata['TempInMin'] = (globalvars.meteo_data.TempInMin)
    mydata['TempInMax'] = (globalvars.meteo_data.TempInMax)
    
    mydata['UmOutMin'] = (globalvars.meteo_data.UmOutMin)
    mydata['UmOutMax'] = (globalvars.meteo_data.UmOutMax)
    
    mydata['UmInMin'] = (globalvars.meteo_data.UmInMin)
    mydata['UmInMax'] = (globalvars.meteo_data.UmInMax)
    
    mydata['PressureMin'] = (globalvars.meteo_data.PressureMin)
    mydata['PressureMax'] = (globalvars.meteo_data.PressureMax)
    
       
    mydata['wind_dir_ave'] = (globalvars.meteo_data.wind_dir_ave)
    
    mydata['rain_rate_24h'] = (globalvars.meteo_data.rain_rate_24h)
    mydata['rain_rate_1h'] = (globalvars.meteo_data.rain_rate_1h)
    

    if ( globalvars.meteo_data.wind_trend != None):
        mydata['wind_trend'] = (globalvars.meteo_data.wind_trend)
    else:
        mydata['wind_trend'] = 0

    mydata['station_name'] = (cfg.station_name)
    mydata['location_longitude'] = (cfg.location_longitude)
    mydata['location_latitude'] = (cfg.location_latitude)
    mydata['location_altitude'] = (cfg.location_altitude)

    mydata['wind_speed_units'] = (cfg.wind_speed_units)
    
    mydata['wind_trend_limit'] = (cfg.wind_trend_limit)
    
    mydata['pressure_trend'] = (globalvars.meteo_data.pressure_trend)


    #mydata['swpi_versione'] = swpi_version



    
    
    #print mydata
    
    
    j = json.dumps(mydata)
    objects_file = './meteo.txt'

    f = open(objects_file,'w')
    f.write(j + "\n")
    f.close()
    
    
    sendFileToServer(objects_file,'meteo.txt',cfg.ftpserver,cfg.upload_folder,cfg.ftpserverLogin,cfg.ftpserverPassowd,True,cfg.use_thread_for_sending_to_server)

    
def NoneToNull(var):
    if ( var == None ):
        return "Null"
    else:
        return var
    
def DBFielsToNumbet(var):
    if ( var == None ):
        return None
    else:
        return var    
    
    
def waitForHandUP():
    if ( not globalvars.bAnswering):
        return
    else:
        log("Waiting for HangUP ...")
        for i in range (1,100):
            if (  globalvars.bAnswering):
                time.sleep(1)
            else:
                globalvars.bAnswering = False
                return
            
def waitForCameraCapture():
    if ( not globalvars.bCapturingCamera):
        return
    else:
        log("Waiting cameras to capture ...")
        for i in range (1,100):
            if (  globalvars.bCapturingCamera):
                time.sleep(1)
            else:
                globalvars.bCapturingCamera = False
                return


def log(message) :
    print datetime.datetime.now().strftime("[%d/%m/%Y-%H:%M:%S]") , message

def getFileName(path):
    return os.path.basename(path)

def addTextandResizePhoto(filename,finalresolutionX,finalresolutionY,cfg,version=None):
    log("Processing image :" + filename )
    textColor = (255,255,0)
    offsetUpper = 20
    offsetBottom = 32
    marginLeft = 10
    MarginRight = 10
    bgrColor = (50, 30, 255)
    
    #font_path = "./fonts/arial.ttf"
    font_path = "./fonts/LucidaBrightDemiItalic.ttf"
    font = ImageFont.truetype(font_path, 15, encoding='unic')
    
    img1 = Image.open(filename)
    w, h = img1.size
    
    if ( w != finalresolutionX or h != finalresolutionY ):
        new_size=[finalresolutionX, finalresolutionY]
        img2 = img1.resize(new_size) 
        img1 = img2.copy()
        
    img = Image.new("RGB", (finalresolutionX,finalresolutionY+offsetUpper+offsetBottom), bgrColor)
    img.paste(img1, (0,offsetUpper,finalresolutionX,finalresolutionY+offsetUpper))
        
    w, h = img.size
    draw = ImageDraw.Draw(img)
    
    text =  cfg.webcamLogo
    draw.text((marginLeft, 0),text,textColor,font=font)
    
    text =   datetime.datetime.now().strftime("Data : %d/%m/%Y - %H:%M:%S ")
    width, height = font.getsize(text)
    draw.text((w-width-MarginRight-10, 0),text,textColor,font=font)
    
    font = ImageFont.truetype(font_path, 13, encoding='unic')
    
    # Adding Meteo information
    if ( cfg.use_wind_sensor ):
        if (  globalvars.meteo_data.status == 0 ):
     
            delay = (datetime.datetime.now() - globalvars.meteo_data.last_measure_time)
            delay_seconds = int(delay.total_seconds())
            
            if (globalvars.meteo_data.wind_dir_code != None and globalvars.meteo_data.wind_ave != None and globalvars.meteo_data.wind_gust != None):    
                
                if ( len(globalvars.meteo_data.wind_dir_code) == 3 ):
                    dir = globalvars.meteo_data.wind_dir_code
                elif ( len(globalvars.meteo_data.wind_dir_code) == 2 ):
                    dir = " " + globalvars.meteo_data.wind_dir_code
                else:
                    dir = "  " + globalvars.meteo_data.wind_dir_code
                text = "Direzione del vento: " + dir + " - Intensita:%5.1f" % globalvars.meteo_data.wind_ave + " km/h  - Raffica:%5.1f" % globalvars.meteo_data.wind_gust  + " km/h" 
                if (globalvars.meteo_data.temp_out  != None) : 
                    text = text + " - Temperatura:%4.1f" % globalvars.meteo_data.temp_out + " C"
                if (globalvars.meteo_data.rel_pressure != None ) : 
                    text = text + " - Pressione:%6.1f" % globalvars.meteo_data.rel_pressure + " hpa"         
                if (globalvars.meteo_data.cloud_base_altitude != None ) : 
                    text = text + " - Base cumulo:%d" % globalvars.meteo_data.cloud_base_altitude + " m"   
                
                width, height = font.getsize(text)
                draw.text((32+marginLeft, h-offsetBottom),text,textColor,font=font)
                
            text = ""
            if (globalvars.meteo_data.hum_out  != None) : 
                text = text + "Umidita : %d" % (globalvars.meteo_data.hum_out) + " % - "
            
            if (globalvars.meteo_data.rain_rate != None) : 
                text = text + "Pioggia oggi : %3.1f" % (globalvars.meteo_data.rain_rate) + " mm - "
            
            if ( globalvars.meteo_data.last_measure_time != None ):
                text = text + "Ultima misura: " + str(globalvars.meteo_data.last_measure_time)
                width, height = font.getsize(text)
                draw.text((32+marginLeft, h-height),text,textColor,font=font)
                
        else:
            text = "Nessun dato meteo - status = " + str(globalvars.meteo_data.status)
            width, height = font.getsize(text)
            draw.text((marginLeft, h-offsetBottom),text,textColor,font=font)
    
    if ( version != None):
        font = ImageFont.truetype(font_path, 11, encoding='unic')
        text = "(Sint Wind PI : " + version + ")"
        width, height = font.getsize(text)
        draw.text((w-width-MarginRight, h-height),text,textColor,font=font)            
    
    
    if ( os.path.isfile("./fonts/windsock.png") ):
        im_windsock = Image.open("./fonts/windsock.png")
        # Box for paste is (left, upper, right, lower).
        img.paste(im_windsock,(int(marginLeft/2),h-offsetBottom+2),im_windsock)
    
    if ( os.path.isfile("./fonts/rpi_logo.png") ):
        im_logo = Image.open("./fonts/rpi_logo.png")
        # Box for paste is (left, upper, right, lower).
        img.paste(im_logo,(w-17,0),im_logo)   
    
    img.save(filename)
    
    if ( not os.path.isfile(filename)):
        log("Problem processing image :" + filename )
        return False
    
    log("Processed image :" + filename )
    return True


wind_rose = {
    0:  "N",
    22.5:  "NNE",
    45: "NE",
    67.5 :"ENE",
    90: "E",
    112.5: "ESE",
    127:"SE",
    149.5: "SSE",
    180:"S",
    202.5: "SSW",
    225:"SW",
    247.5: "WSW",
    270:"W",
    295.5:"WNW",
    315:"NW",
    337.5:"NNW"}


def angle2direction(angle):
    return wind_rose[angle]
    
    

def direction2angle(direction):
    return [item[0] for item in wind_rose() if item[1] == direction]



def mean(numberList):
    if len(numberList) == 0:
        return 0
    floatNums = [float(x) for x in numberList]
    return sum(floatNums) / len(numberList)

def isnumeric(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def sendFileToFTPServer(filename,name,server,destFolder,login,password,delete):
    try:
        s = ftplib.FTP(server,login,password,timeout=30) 	# Connect
        f = open(filename,'rb')                # file to send
        s.cwd(destFolder)
        s.storbinary('STOR ' + name, f)         # Send the file
        f.close()                                # Close file and FTP
        s.quit() 
        log("Sent file to server : " + name)
        if delete : 
            os.remove(filename)
            log("Deleted file : " + filename )
        return True
    except Exception, err:
        print "Exception"
        print '%s' % str(err)    
        log("Error sending  file to server : " + name)
        if delete : 
            os.remove(filename)
            log("Deleted file : " + filename )
        return False

def sendFileToServer(filename,name,server,destFolder,login,password,delete,usethread):
    if ( not usethread ):
        sendFileToFTPServer(filename,name,server,destFolder,login,password,delete)
    else:
        thread.start_new_thread(sendFileToFTPServer, (filename,name,server,destFolder,login,password,delete))


def internet_on():
    log("Checking internet connetion ...")
    ret = os.system("ping -c 1 8.8.8.8 1> /dev/null")
    if ( ret >= 1 ):
        log("No Internet")    
        return False
    else:
        log("Internet ok")
        return True



def internet_on1():
    try:
        log("Checking internet connetion ...")
        #urllib2.urlopen('http://74.125.113.99',timeout=10)
        requests.get('http://74.125.113.99',timeout=10)
        log("Internet ok")
        return True
    except :
        log("No Internet")	
        return False
    
def systemRestart():
    if os.name != 'nt':
        log("Rebooting system ..")
        os.system("sudo reboot")
    else:
        print " Sorry can not rebbot windows"
        
def systemHalt():
    if os.name != 'nt':
        log("Halting system ..")
        os.system("sudo halt")
    else:
        print " Sorry can not rebbot windows"        

def getIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("gmail.com", 80)) 
    except Exception, e:
        #log("something wrong in get IP. Exception type is %s" % ( e))
        return None
    ip = (s.getsockname()[0])
    s.close()
    return ip


def getPublicIP():
    try:
        ip = requests.get("http://www.vololiberomontecucco.it/ip.php",timeout=10).text
        #ip = urllib.urlopen("http://www.vololiberomontecucco.it/ip.php").read()
        return ip
    except Exception, e:
        return None    

def waitForIP():
    # wait maximum 2 minute for a valid IP
    log("Waiting for a valid IP ...")
    n = 60
    for i in range(1,n):
        theIP = getIP()
        if ( theIP != None):
            return theIP
        log("No IP yet. Retrying ..%d" % (n-i) )
        time.sleep(2)
    return None

def SendMail(cfg, subject, text, attach):
    try:
        msg = MIMEMultipart()
        
        msg['From'] = "Sint Wind PI"
        msg['To'] = cfg.mail_to
        msg['Subject'] = subject
        
        #cfg.gmail_user.encode('utf-8')
        #cfg.gmail_pwd.encode('utf-8')        
        
        gmail_user = cfg.gmail_user
        gmail_pwd = cfg.gmail_pwd

        msg.attach(MIMEText(text))
        if (attach != "" ): 
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(attach, 'rb').read())
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                'attachment; filename="%s"' % os.path.basename(attach))
            msg.attach(part)
        
        mailServer = smtplib.SMTP("smtp.gmail.com", 587)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(gmail_user, gmail_pwd)
        mailServer.sendmail(cfg.gmail_user, cfg.mail_to, msg.as_string())
        # Should be mailServer.quit(), but that crashes...
        mailServer.close()
        log("Mail sent to :" + cfg.mail_to)
        return True
    except Exception as e:
        log ("ERROR sending mail" )
        print "Exeption", e
        return False
    



if __name__ == '__main__':
 
    configfile = 'swpi.cfg'
    if not os.path.isfile(configfile):
        "Configuration file not found"
        exit(1)    
    cfg = config.config(configfile)
    
    
    print logDataToCWOP(cfg)
    
    
    
#    rb = RingBuffer(cfg.number_of_measure_for_wind_average_gust_calculation)
#    rb.append(10)
#    wind_ave,wind_gust = rb.getMeanMax()
    
#    sensor = sensor_simulator.Sensor_Simulator(cfg)
#            
#
#                
#    sensor.GetData()
#    
#    print "addTextandResizePhoto"
#    addTextandResizePhoto("F:/jessica2/temp/DSC00192.JPG",800,600,cfg)
#    print "done"
    
    #print SendMail(cfg,"DB","DB attached","mcp3002.tar.gz") 
    
    #for i in range (1,360):
    #    print  str(i) + str(angle2direction(i))