###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#     Comunication based on WFrog  
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
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
import sys
import subprocess
import globalvars
import meteodata
import sensor_thread
import sensor
import logging
import WeatherStation
import units
import array
import struct



logFile = datetime.datetime.now().strftime("log/davis_%d%m%Y.log")
logging.basicConfig(filename=logFile,filemode='wa',level=logging.DEBUG)
# logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')

def get_wind_dir_text():
	return [ 'N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW' ]



class Sensor_VantagePro2(sensor.Sensor):
    
    #port='/dev/ttyUSB0' 
    baud=19200
    loops=25
    rain_bucket = 'eu'
    
   	
    pressure_cal = 0

    logger = logging.getLogger('station.vantagepro')

    name = 'Davis VantagePro'

    # device reply commands
    WAKE_ACK = '\n\r'
    ACK      = '\x06'
    ESC      = '\x1b'
    OK       = '\n\rOK\n\r'
    
    
    
    def __init__(self,cfg ):
        
        sensor.Sensor.__init__(self,cfg )     
        
        self.port = cfg.sensor_serial_port
         
    def Detect(self):
       
        return True,"","",""
  
  
  
  
    
    def GetData(self):
             
 
        import serial

        _LoopStruct = LoopStruct(self.rain_bucket)

        assert self.rain_bucket in ['eu', 'us']
        assert self.baud in [19200, 9600, 4800, 2400, 1200]

        while True:

            seconds = datetime.datetime.now().second
            if ( seconds < 30 ):
                time.sleep(30-seconds)
            else:
                time.sleep(90-seconds)  
                    
            self._port = serial.Serial(self.port, self.baud, timeout=10)
            try:
                bad_CRC = 0 
                self._wakeup()
                self._cmd( 'LOOP', self.loops)       

                for x in xrange(self.loops):
                    raw = self._port.read( _LoopStruct.size ) # read data
                    self.logger.debug('read: ' + raw.encode('hex'))

                    crc_ok = VProCRC.verify( raw )
                    if crc_ok: 
                        bad_CRC = 0
                        self.logger.debug("CRC OK")
                        fields = _LoopStruct.unpack(raw)
                        
#                        print fields
 
                        globalvars.meteo_data.status = 0
                        
                        globalvars.meteo_data.last_measure_time = datetime.datetime.now()
                        globalvars.meteo_data.idx = datetime.datetime.now()
                        
                        globalvars.meteo_data.abs_pressure = fields['Pressure'] + self.pressure_cal
 
                        globalvars.meteo_data.temp_in = fields['TempIn']
                        globalvars.meteo_data.hum_in = fields['HumIn']
                  
                        globalvars.meteo_data.temp_out = fields['TempOut']
                        globalvars.meteo_data.hum_out = fields['HumOut']

                        globalvars.meteo_data.rain = fields['RainRate']
                        globalvars.meteo_data.rain_rate_24h = fields['RainDay']
                        globalvars.meteo_data.wind_dir = fields['WindDir']
                        globalvars.meteo_data.RainStorm = fields['RainStorm']
                        globalvars.meteo_data.RainMonth = fields['RainMonth']
                        globalvars.meteo_data.RainYear = fields['RainYear']
                        globalvars.meteo_data.StormStartDate = fields['StormStartDate']
                        globalvars.meteo_data.BatteryVolts = fields['BatteryVolts']


                        globalvars.meteo_data.wind_gust = float(fields['WindSpeed']) *self.cfg.windspeed_gain + self.cfg.windspeed_offset
                        globalvars.meteo_data.wind_ave = float(fields['WindSpeed10Min']) *self.cfg.windspeed_gain + self.cfg.windspeed_offset
 
                        
                        wind_dir = fields['WindDir']
                        val=int((wind_dir/22.5)+0.5)
                        globalvars.meteo_data.wind_dir_code = get_wind_dir_text()[val]
  
  
                        #log_txt +=  "Wind:%.3fm/s %d " % (fields['WindSpeed'], fields['WindDir'])

                        # UV sensor
                        if fields['UV'] is not None:
                            globalvars.meteo_data.uv =  fields['UV']

                        # Solar radiation sensor
                        if fields['SolarRad'] is not None:
                            globalvars.meteo_data.illuminance = fields['SolarRad']
                            

                        sensor.Sensor.GetData(self)
                        
                                   
                                     
                    else:
                        self.logger.info("CRC Bad")
                        bad_CRC += 1 
                        # Two consecutive CRC errors => exception & abort LOOP command
                        if bad_CRC > 1:
                            raise Exception("CRC error")
                time.sleep(2)

            except Exception, e:
                self.logger.error(e)
                time.sleep(self.loops * 2)
            finally:
                self._port.close()
                self._port = None
        
 
    




    def _wakeup(self):
        '''
        issue wakeup command to device to take out of standby mode.
        '''
        self.logger.debug("send: WAKEUP")
        for i in xrange(3):
            self._port.write('\n')                    # wakeup device
            ack = self._port.read(len(self.WAKE_ACK)) # read wakeup string
            self.logger.debug('read: ' + ack.encode('hex'))
            if ack == self.WAKE_ACK:
                return
        raise Exception('Cannot access weather station (WAKEUP)')


    def _cmd(self,cmd,*args,**kw):
        '''
        write a single command, with variable number of arguments. after the
        command, the device must return ACK
        '''
        ok = kw.setdefault('ok',False)

        if args:
            cmd = "%s %s" % (cmd, ' '.join(str(a) for a in args))
        self.logger.debug('send: ' + cmd)
        for i in xrange(3):
            self._port.write( cmd + '\n')
            if ok:
                ack = self._port.read(len(self.OK))  # read OK
                self.logger.debug('read: ' + ack.encode('hex'))
                if ack == self.OK:
                    return
            else:
                ack = self._port.read(len(self.ACK))  # read ACK
                self.logger.debug('read: ' + ack.encode('hex'))
                if ack == self.ACK:
                    return
        raise Exception('Cannot access weather station (%s)' % cmd)



# --------------------------------------------------------------------------- #

class NoDeviceException(Exception): pass

# --------------------------------------------------------------------------- #

class VProCRC(object):
    '''
    Implements CRC algorithm, necessary for encoding and verifying data from
    the Davis Vantage Pro unit.
    '''

    CRC_TABLE = (
        0x0, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
        0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
        0x1231, 0x210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
        0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
        0x2462, 0x3443, 0x420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
        0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
        0x3653, 0x2672, 0x1611, 0x630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
        0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
        0x48c4, 0x58e5, 0x6886, 0x78a7, 0x840, 0x1861, 0x2802, 0x3823,
        0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
        0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0xa50, 0x3a33, 0x2a12,
        0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
        0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0xc60, 0x1c41,
        0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
        0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0xe70,
        0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
        0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
        0x1080, 0xa1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
        0x2b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
        0x34e2, 0x24c3, 0x14a0, 0x481, 0x7466, 0x6447, 0x5424, 0x4405,
        0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
        0x26d3, 0x36f2, 0x691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
        0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x8e1, 0x3882, 0x28a3,
        0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
        0x4a75, 0x5a54, 0x6a37, 0x7a16, 0xaf1, 0x1ad0, 0x2ab3, 0x3a92,
        0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
        0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0xcc1,
        0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
        0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0xed1, 0x1ef0,
      )


    @staticmethod
    def get(data):
        '''
        return CRC calc value from raw serial data
        '''
        crc = 0
        for byte in array.array('B',data):
            crc = (VProCRC.CRC_TABLE[ (crc>>8) ^ byte ] ^ ((crc&0xFF) << 8))
        return crc


    @staticmethod
    def verify(data):
        '''
        perform CRC check on raw serial data, return true if valid.
        a valid CRC == 0.
        '''
        if len(data) == 0:
            return False
        crc = VProCRC.get(data)
        return not crc

# --------------------------------------------------------------------------- #

class myStruct( struct.Struct ):
    '''
    Implements a reusable class for working with a binary data structure. It
    provides a named fields interface, similiar to C structures.

    Usage: 1) subclass and extend _post_unpack method
           2) instantiate directly, if no 'post unpack' processing needed

    Arguments:
        See `struct.Struct` class defintion.
    '''
    def __init__(self, fmt, order='@'):
        self.fields, fmt_t = zip(*fmt)
        fmt_s = order + ''.join(fmt_t)
        super(myStruct,self).__init__( fmt_s )

    def unpack(self, buf):
        '''
        see unpack_from()
        '''
        return self.unpack_from( buf, offset=0 )


    def unpack_from(self, buf, offset=0 ):
        '''
        unpacks data from 'buf' and returns a dication of named fields. the
        fields can be post-processed by extending the _post_unpack() method.
        '''
        data = super(myStruct,self).unpack_from( buf, offset)
        items = dict(zip(self.fields,data))
        return self._post_unpack(items)


    def _post_unpack(self,items):
        '''
        perform data modification of any values, after unpacking from a buffer.
        '''
        return items

class LoopStruct( myStruct ):
    '''
    For unpacking data structure returned by the 'LOOP' command. this structure
    contains all of the real-time data that can be read from the Davis Vantage
    Pro.
    '''
    FMT = (
        ('LOO',         '3s'), ('BarTrend',    'B'),  ('PacketType',  'B'),
        ('NextRec',      'H'), ('Pressure',    'H'),  ('TempIn',      'H'),
        ('HumIn',        'B'), ('TempOut',     'H'),  ('WindSpeed',   'B'),
        ('WindSpeed10Min','B'),('WindDir',     'H'),  ('ExtraTemp1',  'B'),
        ('ExtraTemp2',   'B'), ('ExtraTemp3',  'B'),  ('ExtraTemp4',  'B'),
        ('ExtraTemp5',   'B'), ('ExtraTemp6',  'B'),  ('ExtraTemp7',  'B'),
        ('SoilTemps',   '4s'), ('LeafTemps',  '4s'),  ('HumOut',      'B'),
        ('ExtraHum1',    'B'), ('ExtraHum2',   'B'),  ('ExtraHum3',   'B'), 
        ('ExtraHum4',    'B'), ('ExtraHum5',   'B'),  ('ExtraHum6',   'B'),
        ('ExtraHum7',    'B'), ('RainRate',    'H'),  ('UV',          'B'),
        ('SolarRad',     'H'), ('RainStorm',   'H'),  ('StormStartDate','H'),
        ('RainDay',      'H'), ('RainMonth',   'H'),  ('RainYear',    'H'),
        ('ETDay',        'H'), ('ETMonth',     'H'),  ('ETYear',      'H'),
        ('SoilMoist',   '4s'), ('LeafWetness','4s'),  ('AlarmIn',     'B'),
        ('AlarmRain',    'B'), ('AlarmOut' ,  '2s'),  ('AlarmExTempHum','8s'),
        ('AlarmSoilLeaf','4s'),('BatteryStatus','B'), ('BatteryVolts','H'),
        ('ForecastIcon','B'),  ('ForecastRuleNo','B'),('SunRise',     'H'),
        ('SunSet',      'H'),  ('EOL',         '2s'), ('CRC',         'H'),
      )

    def __init__(self, rain_bucket):
        super(LoopStruct,self).__init__(self.FMT,'=')
        self.rain_bucket = rain_bucket

    def _post_unpack(self,items):
        # Pressure
        items['Pressure'] = units.InHgToHPa(items['Pressure'] / 1000.0)
        # Temperature
        items['TempIn'] = units.FToC(items['TempIn'] / 10.0)
        items['TempOut'] = units.FToC(items['TempOut'] / 10.0)
        items['ExtraTemp1'] = units.FToC(items['ExtraTemp1'] / 10.0) if items['ExtraTemp1'] != 255 else None
        items['ExtraTemp2'] = units.FToC(items['ExtraTemp2'] / 10.0) if items['ExtraTemp2'] != 255 else None
        items['ExtraTemp3'] = units.FToC(items['ExtraTemp3'] / 10.0) if items['ExtraTemp3'] != 255 else None
        items['ExtraTemp4'] = units.FToC(items['ExtraTemp4'] / 10.0) if items['ExtraTemp4'] != 255 else None
        items['ExtraTemp5'] = units.FToC(items['ExtraTemp5'] / 10.0) if items['ExtraTemp5'] != 255 else None
        items['ExtraTemp6'] = units.FToC(items['ExtraTemp6'] / 10.0) if items['ExtraTemp6'] != 255 else None
        items['ExtraTemp7'] = units.FToC(items['ExtraTemp7'] / 10.0) if items['ExtraTemp7'] != 255 else None
        # Humidity
        items['ExtraHum1'] = items['ExtraHum1'] if items['ExtraHum1'] != 255 else None
        items['ExtraHum2'] = items['ExtraHum2'] if items['ExtraHum2'] != 255 else None
        items['ExtraHum3'] = items['ExtraHum3'] if items['ExtraHum3'] != 255 else None
        items['ExtraHum4'] = items['ExtraHum4'] if items['ExtraHum4'] != 255 else None
        items['ExtraHum5'] = items['ExtraHum5'] if items['ExtraHum5'] != 255 else None
        items['ExtraHum6'] = items['ExtraHum6'] if items['ExtraHum6'] != 255 else None
        items['ExtraHum7'] = items['ExtraHum7'] if items['ExtraHum7'] != 255 else None
        
        # Wind
        #items['WindSpeed'] = units.MphToMps(items['WindSpeed'])
        #items['WindSpeed10Min'] = units.MphToMps(items['WindSpeed10Min'])
        # Rain / European version => each bucket tip ~ 0.2mm
        if self.rain_bucket == 'eu':  
            items['RainRate'] = items['RainRate'] / 5.0 
            items['RainStorm'] = items['RainStorm'] / 5.0
            items['RainDay'] = items['RainDay'] / 5.0
            items['RainMonth'] = items['RainMonth'] / 5.0
            items['RainYear'] = items['RainYear'] / 5.0
        # Rain / US version => each bucket tip ~ 0.01 inches. Conversion to mm needed.
        elif self.rain_bucket == 'us': 
	    tems['WindSpeed'] = units.MphToMps(items['WindSpeed'])
            items['WindSpeed10Min'] = units.MphToMps(items['WindSpeed10Min'])         
            items['RainRate'] = units.InToMm(items['RainRate'] / 100.0)
            items['RainStorm'] = units.InToMm(items['RainStorm'] / 100.0)
            items['RainDay'] = units.InToMm(items['RainDay'] / 100.0)
            items['RainMonth'] = units.InToMm(items['RainMonth'] / 100.0)
            items['RainYear'] = units.InToMm(items['RainYear'] / 100.0)
        items['StormStartDate'] = self._unpack_storm_date(items['StormStartDate'])
        
            # UV
        items['UV'] = (items['UV'] / 10.0) if items['UV'] != 255 else None
            # SolarRad
        items['SolarRad'] = items['SolarRad'] if items['SolarRad'] != 32767 else None
        # evapotranspiration totals
        items['ETDay'] = items['ETDay'] / 1000.0
        items['ETMonth'] = items['ETMonth'] / 100.0
        items['ETYear'] = items['ETYear'] / 100.0
        #soil moisture + leaf wetness
        items['SoilMoist'] = struct.unpack('4B',items['SoilMoist'])
        items['LeafWetness'] = struct.unpack('4B',items['LeafWetness'])
        # battery statistics
        items['BatteryVolts'] = items['BatteryVolts'] * 300 / 512.0 / 100.0
        # sunrise / sunset
        items['SunRise'] = self._unpack_time( items['SunRise'] )
        items['SunSet'] = self._unpack_time( items['SunSet'] )

        return items


    @staticmethod
    def _unpack_time( val ):
        '''
        given a packed time field, unpack and return "HH:MM" string.
        '''
        # format: HHMM, and space padded on the left.ex: "601" is 6:01 AM
        return "%02d:%02d" % divmod(val,100)  # covert to "06:01"


    @staticmethod
    def _unpack_storm_date( date ):
        '''
        given a packed storm date field, unpack and return 'YYYY-MM-DD' string.
        '''
        year  = (date & 0x7f) + 2000        # 7 bits
        day   = (date >> 7) & 0x01f         # 5 bits
        month = (date >> 12) & 0x0f         # 4 bits
        return "%s-%s-%s" % (year, month, day)


if __name__ == '__main__':
    """Main only for testing"""
    configfile = 'swpi.cfg'
    
    cfg = config.config(configfile)    
    
    globalvars.meteo_data = meteodata.MeteoData(cfg)
    ws = Sensor_VantagePro2(cfg)
    ws.GetData()


