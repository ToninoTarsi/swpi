###########################################################################
#	 Sint Wind PI
#	 Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#	 Please refer to the LICENSE file for conditions 
#	 Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""This module defines the WH3080_RTL-SDR sensor."""
# By Nicola Quiriti ('Seven') - 03/2017

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
import json
DEBUG = False

def log(message):
    print datetime.datetime.now().strftime('[%d/%m/%Y-%H:%M:%S]'), message


def modification_date(filename):
    try:
        t = os.path.getmtime(filename)
        return datetime.datetime.fromtimestamp(t)
    except:
        return None


def getrevision():
    myrevision = '0000'
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:8] == 'Revision':
                myrevision = line[11:-1]

        f.close()
    except:
        myrevision = '0000'

    return myrevision


class Sensor_WH3080RTLSDR(sensor.Sensor):

    def __init__(self, cfg):
        ret = self.Detect()
        if not ret:
            log('*************************************************************')
            log('*                                                           *')
            log('*   ERROR : No RTL-SDR compatible USB DVB-T dongle found!   *')
            log('*                  SWPI execution aborted.                  *')
            log('*                                                           *')
            log('*************************************************************')
            os.system('sudo ./killswpi.sh')
        else:
            log('RTL-SDR-compatible USB DVB-T dongle detected.')
            time.sleep(5)
        threading.Thread.__init__(self)
        sensor.Sensor.__init__(self, cfg)
        self.cfg = cfg
        try:
            os.remove('/dev/shm/wh1080-rtl_433.txt')
        except:
            log('Warning could not delete wh1080-rtl_433.txt file')

        try:
            os.remove('/dev/shm/wh3080-rtl_433.txt')
        except:
            log('Warning could not delete wh3080-rtl_433.txt file')

        self.active = True
        self.start()

    def readfreq(self):
        if self.cfg.rtlsdr_frequency == 433:
            return '433920000'
        if self.cfg.rtlsdr_frequency == 868:
            return '868200000'
        if self.cfg.rtlsdr_frequency == 915:
            return '915000000'

    def startRFListenig(self):
        freq = self.readfreq()
        bdl = str(self.cfg.rtlsdr_bdl)
        ppm = str(self.cfg.rtlsdr_ppm)
        cmd = '/usr/local/bin/rtl_433 -q -f %s -R 32 -l %s -p %s  > /dev/null' % (freq, bdl, ppm)
        os.system(cmd)

    def run(self):
        freq = self.readfreq()
        bdl = str(self.cfg.rtlsdr_bdl)
        ppm = str(self.cfg.rtlsdr_ppm)
        myrevision = getrevision()
        if myrevision == '0002' or myrevision == '0003':
            s = 1
        else:
            s = 2
        log('Starting RF listening')
        cmd = '/usr/local/bin/rtl_433 -q -f %s -R 32 -l %s -p %s  > /dev/null' % (freq, bdl, ppm)
        os.system(cmd)
        log('Something went wrong with RF ... restarting')

    def Detect(self):
        p = subprocess.Popen('/usr/local/bin/rtl_eeprom', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if stderr.find('Found') != -1:
            return True
        else:
            return False

    def ReadData(self):
        with file('/dev/shm/wh1080-rtl_433.txt') as f:
            data_file = f.read()
            try:
                line = json.loads(data_file)
                if str(line['msg_type']) == '0':
                    try:
                        station_id = str(line['station_id'])
                        if station_id == 'None':
                            return ('None', 0, 0, 0, 0, '', 0, 0, None, None)
                        temp = float(round(line['temperature'], 1))
                        hum = line['humidity']
                        Wind_speed = line['wind_speed'] * self.cfg.windspeed_gain + self.cfg.windspeed_offset
                        Gust_Speed = line['wind_gust'] * self.cfg.windspeed_gain + self.cfg.windspeed_offset
                        dir_code = str(line['wind_dir_str'])
                        dire = float(line['wind_dir_deg'])
                        rain = round(line['total_rain'], 2)
                    except:
                        log('Error while decoding json data!')

                elif str(line['msg_type']) == '1':
                    if str(self.cfg.rtlsdr_timesync) == 'True':
                        print '\n'
                        log('Setting system time...')
                        try:
                            t_year = str(line['year'])
                            t_month = str(line['month'])
                            if len(t_month) == 1:
                                t_month = '0' + t_month
                            t_day = str(line['day'])
                            if len(t_day) == 1:
                                t_day = '0' + t_day
                            t_hours = str(line['hours'])
                            if len(t_hours) == 1:
                                t_hours = '0' + t_hours
                            t_minutes = str(line['minutes'])
                            if len(t_minutes) == 1:
                                t_minutes = '0' + t_minutes
                            t_seconds = str(line['seconds'])
                            if len(t_seconds) == 1:
                                t_seconds = '0' + t_seconds
                            time_to_set = t_year + '-' + t_month + '-' + t_day + ' ' + t_hours + ':' + t_minutes + ':' + t_seconds
                            os.system("sudo date --s '%s'" % time_to_set)
                            log('System time adjusted from WH3080_RTL-SDR.')
                            return ('Time', 0, 0, 0, 0, '', 0, 0, None, None)
                        except:
                            log('Error adjusting system time from WH3080_RTL-SDR')

                    else:
                        log('WH3080_RTL-SDR: rtlsdr_timesync is disabled.')
                        return ('Time', 0, 0, 0, 0, '', 0, 0, None, None)
            except:
                log('Received data are not in json format. Dropped...')
                return ('None', 0, 0, 0, 0, '', 0, 0, None, None)

        try:
            with file('/dev/shm/wh3080-rtl_433.txt') as f2:
                data_file2 = f2.read()
                try:
                    line2 = json.loads(data_file2)
                    if str(line2['msg_type']) == '2':
                        try:
                            uv_sensor_id = str(line2['uv_sensor_id'])
                            uv_status = str(line2['uv_status'])
                            uv_index = line2['uv_index']
                            lux = line2['lux']
                            watts_sqmeter = line2['wm']
                        except:
                            log('Error while decoding json (UV) data, or data not available yet.')
                            uv_index = 0
                            watts_sqmeter = 0

                except:
                    log('Invalid UV/light data, or data not available yet.')
                    uv_index = None
                    watts_sqmeter = None

        except:
            log('Invalid UV/light data, or data not available yet.')
            uv_index = None
            watts_sqmeter = None

        return (station_id,
         temp,
         hum,
         Wind_speed,
         Gust_Speed,
         dir_code,
         dire,
         rain,
         uv_index,
         watts_sqmeter)

    def GetData(self):
        good_data = False
        while not os.path.exists('/dev/shm/wh1080-rtl_433.txt'):
            if DEBUG:
                print 'DEBUG - /dev/shm/wh1080-rtl_433.txt does not exist.'
            time.sleep(5)
	while not os.path.exists('/dev/shm/wh1080-rtl_433.txt'):
            if DEBUG:
                print 'DEBUG - /dev/shm/wh3080-rtl_433.txt does not exist.'
            time.sleep(5)

        while not good_data:
            station_id, temp, hum, Wind_speed, Gust_Speed, dir_code, dire, rain, uv_index, watts_sqmeter = self.ReadData()
            if station_id != 'None' and station_id != 'Time':
                good_data = True
            elif station_id == 'Time':
                log('Datetime data received from WH3080_RTL-SDR. Waiting for weather data...')
                time.sleep(48)
            else:
                log('Bad data received from WH3080_RTL-SDR')
                time.sleep(48)

        log('First data received from WH3080_RTL-SDR, station %s. Processing...' % station_id)
        last_data_time = modification_date('/dev/shm/wh1080-rtl_433.txt')
        while 1:
            if station_id != 'None' and station_id != 'Time':
                globalvars.meteo_data.status = 0
                globalvars.meteo_data.last_measure_time = last_data_time
                globalvars.meteo_data.idx = globalvars.meteo_data.last_measure_time
                globalvars.meteo_data.hum_out = hum
                globalvars.meteo_data.temp_out = temp
                globalvars.meteo_data.wind_ave = Wind_speed
                globalvars.meteo_data.wind_gust = Gust_Speed
                globalvars.meteo_data.wind_dir = dire
                globalvars.meteo_data.wind_dir_code = dir_code
                globalvars.meteo_data.rain = rain
                globalvars.meteo_data.uv = uv_index
                globalvars.meteo_data.illuminance = watts_sqmeter
                sensor.Sensor.GetData(self)
            tosleep = 50 - (datetime.datetime.now() - last_data_time).seconds
            if DEBUG:
                print 'Sleeping  ', tosleep
            if tosleep > 0 and tosleep < 50:
                time.sleep(tosleep)
            else:
                time.sleep(50)
            new_last_data_time = modification_date('/dev/shm/wh1080-rtl_433.txt')
            while new_last_data_time == None or new_last_data_time == last_data_time:
                time.sleep(10)
                new_last_data_time = modification_date('/dev/shm/wh1080-rtl_433.txt')

            if station_id != 'Time':
                log('New data received from WH3080_RTL-SDR station %s. Processing...' % station_id)
            else:
                log('Datetime signal received from WH3080_RTL-SDR station. Processing...')
            last_data_time = new_last_data_time
            station_id, temp, hum, Wind_speed, Gust_Speed, dir_code, dire, rain, uv_index, watts_sqmeter = self.ReadData()
            if station_id == 'Time':
                log('Sleeping while waiting for weather data...')
                tosleep = 50 - (datetime.datetime.now() - last_data_time).seconds
                if DEBUG:
                    print 'Sleeping  ', tosleep
                if tosleep > 0 and tosleep < 50:
                    time.sleep(tosleep)
                else:
                    time.sleep(50)
            if station_id == 'None':
                log('Bad data received from WH3080_RTL-SDR')


if __name__ == '__main__':
    configfile = 'swpi.cfg'
    cfg = config.config(configfile)
    globalvars.meteo_data = meteodata.MeteoData(cfg)
    ss = Sensor_WH3080RTLSDR
    while 1:
        ss.GetData()