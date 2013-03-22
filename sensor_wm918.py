###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""This module defines the base sensors Sensor_WMR100 ."""


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

def log(message) :
    print datetime.datetime.now().strftime("[%d/%m/%Y-%H:%M:%S]") , message

windDirMap = { 0:"N", 1:"NNE", 2:"NE", 3:"ENE", 4:"E", 5:"ESE", 6:"SE", 7:"SSE",
              8:"S", 9:"SSW", 10:"SW", 11:"WSW", 12:"W", 13:"WNW", 14:"NW", 15:"NWN" }

def toBCD(n):
    if n < 0 or n > 99: return 0

    n1 = n / 10
    n2 = n % 10

    m = n1 << 4 | n2
    return m

def fromBCD(n):
    n1 = n & 0x0F
    n2 = n >> 4
    return n2 * 10 + n1

class Sensor_WM918(sensor.Sensor):
    '''
    Station driver for the Oregon Scientific WM918.
    '''
    def __init__(self,cfg ):
        self.cfg = cfg

    def GetData(self):     
        log("Thread started")
        while True:
            try:
                log("Opening serial port")
                ## Open Serial port
                ser = serial.Serial()
                ser.setBaudrate(9600)
                ser.setParity(serial.PARITY_NONE)
                ser.setByteSize(serial.EIGHTBITS)
                ser.setStopbits(serial.STOPBITS_ONE)
                ser.setPort(self.cfg.sensor_serial_port)
                ser.setTimeout(60)  # 60s timeout
                ser.open()
                ser.setRTS(True)
                ## Do the actual work
                log("Serial port open")
                self._run(ser)
            except:
                log(" WM918 reader exception")

            
            #self._run(ser)
            ## Close serial port connection
            log("Serial port  WM918 connection failure")
            try:
                ser.close()
                ser = None
            except:
                pass
            ## Wait 10 seconds
            time.sleep(10)


    def _run(self,ser):

        lastcmd = None
        buffer = []

        flags = [0,0,0,0,0]

        while 1:
            try:
                c = ser.read(1)
            except :
                time.sleep(1)
                continue

            intc = ord(c)
            #print intc
            
            if intc in (0x8f, 0x9f, 0xaf, 0xbf, 0xcf):
                if intc == 0x8f:
                    s = ser.read(34)
                    self.pr8F( c + s)
                    flags[0] = 1
                elif intc == 0x9f:
                    s = ser.read(33)
                    self.pr9F( c + s)
                    flags[1] = 1
                elif intc == 0xaf:
                    s = ser.read(30)
                    self.prAF( c+s)
                    flags[2] = 1
                elif intc == 0xbf:
                    s = ser.read(13)
                    self.prBF( c+s)
                    flags[3] = 1
                elif intc == 0xcf:
                    s = ser.read(26)
                    self.prCF( c + s)
                    flags[4] = 1

                #print  flags[0] , flags[1] , flags[2] , flags[3] , flags[4]
                if flags[0] and flags[1] and flags[2] and flags[3] and flags[4]:
                    if ( globalvars.meteo_data.last_measure_time == None or (datetime.datetime.now()-globalvars.meteo_data.last_measure_time).seconds >= 60 ) :   
                        globalvars.meteo_data.status = 0
                        globalvars.meteo_data.last_measure_time = datetime.datetime.now()
                        globalvars.meteo_data.idx = globalvars.meteo_data.last_measure_time 
                        #print "_logData1"
                        sensor.Sensor.GetData(self)                 
                    flags = [0,0,0,0,0]
    
            else:
                pass

    def hexBuffer(self, buffer):
        l = []
        for c in buffer:
            l.append("%02x" % ord(c))
        return string.join(l, " ")


    def toBinary(self, buffer):
        l = []
        for c in buffer: l.append(ord(c))
        return l

    def pd2int4p(self, buf):
        c = ((buf[1] >> 4) & 0x0f)
        c = c*10 + ((buf[1]) & 0x0f)
        c = c * 10 + ((buf[0] >> 4) & 0x0f)
        return c


    def pd2int3p(self, buf):
        c = ((buf[1] >> 4) & 0x0f)
        c = c*10 + ((buf[0] >> 4) & 0x0f)
        c = c * 10 + (buf[0] & 0x0f)
        c = c / 10.
        return c

    def pd2int3(self, buf):
        c = (buf[1] & 0x07)
        c = c*10 + ((buf[0]>>4)&0x0f)
        c = c*10 + (buf[0] & 0x0F)
        if (buf[1] & 0x08): c = -c
        return c
    

    def prBF(self, buffer):
#    log("prBF", self.hexBuffer(buffer))
        buffer = self.toBinary(buffer)
        total = (buffer[6] & 0xf)*100. + fromBCD(buffer[5])
        
        #log("Rain :  Total %g " % ( total) )
        self._report_rain(total, None)
        

        

        
    def prAF(self,  buffer):
#    log("prAF", self.hexBuffer(buffer))
        buffer = self.toBinary(buffer)
        abs_pressure = (fromBCD(buffer[2]) * 100 + fromBCD(buffer[1]))
        #log("Pressure : %f " %  abs_pressure )

        self._report_barometer_absolute(abs_pressure)
#    log(barometer_local)
#    log(barometer_sea)

            
    def pr8F(self,  buffer):
#    log("pr8F", self.hexBuffer(buffer))
        buffer = self.toBinary(buffer)
        outside_humidity = float(fromBCD(buffer[20]))
        inside_humidity = float(fromBCD(buffer[8]))
        #log("Umidity : inside %f outside %f" % (inside_humidity, outside_humidity))
        self._report_humidity( inside_humidity, outside_humidity)
        
    def prCF(self,  buffer):
#       log("prCF", self.hexBuffer(buffer))
        buffer = self.toBinary(buffer)

        #mps = self.pd2int3(buffer[1:3])
        mps = (fromBCD(buffer[1]) / 10.) + ((buffer[2] & 0xf) * 10)
        #mph = (mps*2236936L+50000L)/1000000L
        wind_gust_speed = mps * 3.6
        #wind_gust_speed = mph * 1.609344
        
        mps = (fromBCD(buffer[4]) / 10.) + ((buffer[5] & 0xf) * 10)
        #mph = (mps*2236936L+50000L)/1000000L
        wind_speed = mps * 3.6
        #wind_speed = mph * 1.609344
        
        dir = self.pd2int4p(buffer[2:4])

        wind_direction = dir


        dir = int(wind_direction * 16 / 360  )
        dirStr = windDirMap[dir]

        #print wind_direction,wind_speed,wind_gust_speed
        #log("Wind : direction: %d, gust: %f kmh, avg. speed: %f kmh" % (wind_direction, wind_gust_speed, wind_speed ))
        self._report_wind(dir, wind_direction, dirStr, wind_gust_speed, wind_speed)


    def pr9F(self,  buffer):
#    log("pr9F", self.hexBuffer(buffer))
        buffer = self.toBinary(buffer)

        inside_temp = self.pd2int3(buffer[1:3]) / 10.0
        outside_temp = fromBCD(buffer[16]) / 10. + ((buffer[17] & 0xf)*10)
        
        #log("Temperature : inside %f outside %f" % (inside_temp, outside_temp))
        self._report_temperature_inout(inside_temp, outside_temp)
    
if __name__ == '__main__':
    """Main only for testing"""
    configfile = 'swpi.cfg'
    
    cfg = config.config(configfile)    
    
    globalvars.meteo_data = meteodata.MeteoData(cfg)
    ws = Sensor_WM918(cfg)
    ws.GetData()
    
