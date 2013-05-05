#!/usr/bin/python -W default
#
# ws2300
# ------
#
#   Interface to the LaCrosse WS2300 weather station.  Can be used as a library
#   or a program.
#
#   Author: Russell Stuart, russell-ws2300@stuart.id.au, 2007-09-14
#
# License
# -------
#
#   Copyright (c) 2007,2008,2010,2011,2012 Russell Stuart.
#
#   ws2300.py is part of the Ws2300 driver.
#
#   The WS2300 driver is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or (at
#   your option) any later version.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import warnings; warnings.simplefilter('default')
import cStringIO
import datetime
import errno
import fcntl
import re
import math
import optparse
import os
import select
import signal
import socket
import stat
import string
import struct
import sys
import syslog
import termios
import traceback
import time
import tty
import serial


try:
  import subprocess
  def run(cmd):
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, close_fds=True)
    return p.stdin
except ImportError:
  import popen2
  def run(cmd):
    stdout, stdin = popen2.popen2(' '.join(cmd))
    stdout.close()
    return stdin

VERSION		= "1.7 2012-04-13"

#
# Debug options.
#
DEBUG_SERIAL	= False
DEBUG_VALUE	= False
DEBUG_TRACE	= False
DISABLE_WRITE	= False

#
# A fatal error.
#
class FatalError(StandardError):
  source =		None
  message =		None
  cause	= 		None
  def __init__(self, source, message, cause=None):
    self.source = source
    self.message = message
    self.cause = cause
    StandardError.__init__(self, message)

#
# For debugging.
#
trace_eol = True
trace_file_handle = None
def trace(l, *args):
  if not DEBUG_TRACE:
    return
  global trace_file_handle, trace_eol
  if trace_file_handle == None:
    if DEBUG_TRACE == True:
      trace_file_handle = open("/tmp/ws2300.trace", "w")
    elif type(DEBUG_TRACE) in (type(""), type(u"")):
      trace_file_handle = open(DEBUG_TRACE, "w")
    else:
      trace_file_handle = DEBUG_TRACE
  args = tuple([repr(a) for a in args])
  msg = l % args
  if msg and trace_eol:
    trace_file_handle.write(time.strftime("%d %H:%M:%S "))
    trace_eol = False
  if msg and msg[-1] == '\n':
    trace_eol = True
  trace_file_handle.write(msg)
  trace_file_handle.flush()

#
# The serial port interface.  We can talk to the Ws2300 over anything
# that implements this interface.
#
class SerialPort(object):
  #
#  def open(self): raise NotImplementedError()
  #.
  # Discard all characters waiting to be read.
  #
  def clear(self): raise NotImplementedError()
  #
  # Close the serial port.
  #
  def close(self): raise NotImplementedError()
  #
  # Wait for all characters to be sent.
  #
  def flush(self): raise NotImplementedError()
  #
  # Read a character, waiting for a most timeout seconds.  Return the
  # character read, or None if the timeout occurred.
  #
  def read_byte(self, timeout): raise NotImplementedError()
  #
  # Release the serial port.  Closes it until it is used again, when
  # it is automatically re-opened.  It need not be implemented.
  #
  def release(self): pass
  #
  # Write characters to the serial port.
  #
  def write(self, data): raise NotImplementedError()

#
# A Linux Serial port.  Implements the Serial interface on Linux.
#

class myPySerialPort(SerialPort):
    
    def __init__(self,device):
        self.port =   device
        self.ser = serial.Serial()
        self.ser.setBaudrate(2400)
        self.ser.setParity(serial.PARITY_NONE)
        self.ser.setByteSize(serial.EIGHTBITS)
        self.ser.setStopbits(serial.STOPBITS_ONE)
        self.ser.setPort(self.port)
        self.ser.setTimeout(60)  # 60s timeout
        self.ser.open()
        self.ser.setDTR(False)
        self.ser.setRTS(True)
        
    def close(self):
        self.ser.close()
        
    def read_byte(self, timeout):
        buf = self.ser.read(1)
        if  len(buf)== 0:
            return None
        return buf        
    
    def write(self, data):
        self.ser.write(data)
        
    def clear(self):
        self.ser.flush()
        #tty.tcflush(self.serial_port, tty.TCIFLUSH)

    def flush(self):
        self.ser.flush()
        #tty.tcdrain(self.serial_port)        

class LinuxSerialPort(SerialPort):
  SERIAL_CSIZE  = {
      "7":	tty.CS7,
      "8":	tty.CS8, }
  SERIAL_PARITIES= {
      "e":	tty.PARENB,
      "n":	0,
      "o":	tty.PARENB|tty.PARODD, }
  SERIAL_SPEEDS = {
      "300":	tty.B300,
      "600":	tty.B600,
      "1200":	tty.B1200,
      "2400":	tty.B2400,
      "4800":	tty.B4800,
      "9600":	tty.B9600,
      "19200":	tty.B19200,
      "38400":	tty.B38400,
      "57600":	tty.B57600,
      "115200":	tty.B115200, }
  SERIAL_SETTINGS = "2400,n,8,1"
  device	= None		# string, the device name.
  orig_settings = None		# class,  the original ports settings.
  select_list	= None		# list,   The serial ports
  serial_port	= None		# int,    OS handle to device.
  settings	= None		# string, the settings on the command line.
  #
  # Initialise ourselves.
  #
  def __init__(self,device,settings=SERIAL_SETTINGS):
    self.device = device
    self.settings = settings.split(",")
    self.settings.extend([None,None,None])
    self.settings[0] = self.__class__.SERIAL_SPEEDS.get(self.settings[0], None)
    self.settings[1] = self.__class__.SERIAL_PARITIES.get(self.settings[1].lower(), None)
    self.settings[2] = self.__class__.SERIAL_CSIZE.get(self.settings[2], None)
    if len(self.settings) != 7 or None in self.settings[:3]:
      raise FatalError(self.device, 'Bad serial settings "%s".' % settings)
    self.settings = self.settings[:4]
    #
    # Open the port.
    #
    try:
      self.serial_port = os.open(self.device, os.O_RDWR)
    except EnvironmentError, e:
      raise FatalError(self.device, "can't open tty device - %s." % str(e))
    try:
      fcntl.flock(self.serial_port, fcntl.LOCK_EX)
      self.orig_settings = tty.tcgetattr(self.serial_port)
      setup = self.orig_settings[:]
      setup[0] = tty.INPCK
      setup[1] = 0
      setup[2] = tty.CREAD|tty.HUPCL|tty.CLOCAL|reduce(lambda x,y: x|y, self.settings[:3])
      setup[3] = 0		# tty.ICANON
      setup[4] = self.settings[0]
      setup[5] = self.settings[0]
      setup[6] = ['\000']*len(setup[6])
      setup[6][tty.VMIN] = 1
      setup[6][tty.VTIME] = 0
      tty.tcflush(self.serial_port, tty.TCIOFLUSH)
      #
      # Restart IO if stopped using software flow control (^S/^Q).  This
      # doesn't work on FreeBSD.
      #
      try:
        tty.tcflow(self.serial_port, tty.TCOON|tty.TCION)
      except termios.error:
        pass
      tty.tcsetattr(self.serial_port, tty.TCSAFLUSH, setup)
      #
      # Set DTR low and RTS high and leave other control lines untouched.
      #
      arg = struct.pack('I', 0)
      arg = fcntl.ioctl(self.serial_port, tty.TIOCMGET, arg)
      portstatus = struct.unpack('I', arg)[0]
      portstatus = portstatus & ~tty.TIOCM_DTR | tty.TIOCM_RTS
      arg = struct.pack('I', portstatus)
      fcntl.ioctl(self.serial_port, tty.TIOCMSET, arg)
      self.select_list = [self.serial_port]
    except Exception:
      os.close(self.serial_port)
      raise
  def close(self):
    if self.orig_settings:
      tty.tcsetattr(self.serial_port, tty.TCSANOW, self.orig_settings)
      os.close(self.serial_port)
  def read_byte(self, timeout):
    ready = select.select(self.select_list, [], [], timeout)
    if not ready[0]:
      return None
    return os.read(self.serial_port, 1)
  #
  # Write a string to the port.
  #
  def write(self, data):
    os.write(self.serial_port, data)
  #
  # Flush the input buffer.
  #
  def clear(self):
    tty.tcflush(self.serial_port, tty.TCIFLUSH)
  #
  # Flush the output buffer.
  #
  def flush(self):
    tty.tcdrain(self.serial_port)

#
# This class reads and writes bytes to a Ws2300.  It is passed something
# that implements the Serial interface.  The major routines are:
#
# Ws2300()	- Create one of these objects that talks over the serial port
#		  passed.
# read_batch()	- Reads data from the device using an scatter/gather interface.
# write_safe()	- Writes data to the device.
#


class Ws2300(object):
  #
  # An exception for us.
  #
  class Ws2300Exception(StandardError):
    def __init__(self, *args):
      StandardError.__init__(self, *args)
  #
  # Constants we use.
  #
  MAXBLOCK	= 30
  MAXRETRIES	= 50
  MAXWINDRETRIES= 20
  WRITENIB	= 0x42
  SETBIT	= 0x12
  UNSETBIT	= 0x32
  WRITEACK	= 0x10
  SETACK	= 0x04
  UNSETACK	= 0x0C
  RESET_MIN	= 0x01
  RESET_MAX	= 0x02
  MAX_RESETS	= 100
  #
  # Instance data.
  #
  log_buffer	= None	# list,   action log
  log_mode	= None	# string, Log mode
  long_nest	= None	# int,    Nesting of log actions
  serial_port	= None	# string, SerialPort port to use
  #
  # Initialise ourselves.
  #
  def __init__(self,serial_port):
    self.log_buffer = []
    self.log_nest = 0
    self.serial_port = serial_port
  #
  # Write data to the device.
  #
  def write_byte(self,data):
    if self.log_mode != 'w':
      if self.log_mode != 'e':
	self.log(' ')
      self.log_mode = 'w'
    self.log("%02x" % ord(data))
    self.serial_port.write(data)
  #
  # Read a byte from the device.
  #
  def read_byte(self, timeout=1.0):
    if self.log_mode != 'r':
      self.log_mode = 'r'
      self.log(':')
    result = self.serial_port.read_byte(timeout)
    if result == None:
      self.log("--")
    else:
      self.log("%02x" % ord(result))
    return result
  #
  # Remove all pending incoming characters.
  #
  def clear_device(self):
    if self.log_mode != 'e':
      self.log(' ')
    self.log_mode = 'c'
    self.log("C")
    self.serial_port.clear()
  #
  # Write a reset string and wait for a reply.
  #
  def reset_06(self):
    self.log_enter("re")
    try:
      for retry in range(self.__class__.MAX_RESETS):
	self.clear_device()
	self.write_byte('\x06')
	#
	# Occasionally 0, then 2 is returned.  If 0 comes back,
	# continue reading as this is more efficient than sending
	# an out-of sync reset and letting the data reads restore
	# synchronization.  Occasionally, multiple 2's are returned.
	# Read with a fast timeout until all data is exhausted, if
	# we got a 2 back at all, we consider it a success.
	#
	success = False
	answer = self.read_byte()
	while answer != None:
	  if answer == '\x02':
	    success = True
	  answer = self.read_byte(0.05)
	if success:
	  return
      msg = "Reset failed, %d retries, no response" % self.__class__.MAX_RESETS
      raise self.Ws2300Exception(msg)
    finally:
      self.log_exit()
  #
  # Encode the address.
  #
  def write_address(self,address):
    for digit in range(4):
      byte = chr((address >> (4 * (3-digit)) & 0xF) * 4 + 0x82)
      self.write_byte(byte)
      ack = chr(digit * 16 + (ord(byte) - 0x82) // 4)
      answer = self.read_byte()
      if ack != answer:
	self.log("??")
	return False
    return True
  #
  # Write data, checking the reply.
  #
  def write_data(self,nybble_address,nybbles,encode_constant=None):
    self.log_enter("wd")
    try:
      if not self.write_address(nybble_address):
	return None
      if encode_constant == None:
	encode_constant = self.WRITENIB
      encoded_data = ''.join([
	  chr(nybbles[i]*4 + encode_constant)
	  for i in range(len(nybbles))])
      ack_constant = {
	    self.SETBIT:	self.SETACK,
	    self.UNSETBIT:	self.UNSETACK,
	    self.WRITENIB:	self.WRITEACK
	  }[encode_constant]
      self.log(",")
      for i in range(len(encoded_data)):
	self.write_byte(encoded_data[i])
	answer = self.read_byte()
	if chr(nybbles[i] + ack_constant) != answer:
	  self.log("??")
	  return None
      return True
    finally:
      self.log_exit()
  #
  # Reset the device and write a command, verifing it was written correctly.
  #
  def write_safe(self,nybble_address,nybbles,encode_constant=None):
    self.log_enter("ws")
    try:
      for retry in range(self.MAXRETRIES):
	self.reset_06()
	command_data = self.write_data(nybble_address,nybbles,encode_constant)
	if command_data != None:
	  return command_data
      raise self.Ws2300Exception("write_safe failed, retries exceeded")
    finally:
      self.log_exit()
  #
  # A total kuldge this, but its the easiest way to force the 'computer
  # time' to look like a normal ws2300 variable, which it most definitely
  # isn't, of course.
  #
  def read_computer_time(self,nybble_address,nybble_count):
    now = time.time()
    tm = time.localtime(now)
    tu = time.gmtime(now)
    year2 = tm[0] % 100
    datetime_data = (
      tu[5]%10, tu[5]//10, tu[4]%10, tu[4]//10, tu[3]%10, tu[3]//10,
      tm[5]%10, tm[5]//10, tm[4]%10, tm[4]//10, tm[3]%10, tm[3]//10,
      tm[2]%10, tm[2]//10, tm[1]%10, tm[1]//10, year2%10, year2//10)
    address = nybble_address+18
    return datetime_data[address:address+nybble_count]
  #
  # Read 'length' nybbles at address.  Returns: (nybble_at_address, ...).
  # Can't read more than MAXBLOCK nybbles at a time.
  #
  def read_data(self,nybble_address,nybble_count):
    if nybble_address < 0:
      return self.read_computer_time(nybble_address,nybble_count)
    self.log_enter("rd")
    try:
      if nybble_count < 1 or nybble_count > self.MAXBLOCK:
	StatdardError("Too many nybbles requested")
      bytes = (nybble_count + 1) // 2
      if not self.write_address(nybble_address):
	return None
      #
      # Write the number bytes we want to read.
      #
      encoded_data = chr(0xC2 + bytes*4)
      self.write_byte(encoded_data)
      answer = self.read_byte()
      check = chr(0x30 + bytes)
      if answer != check:
	self.log("??")
	return None
      #
      # Read the response.
      #
      self.log(", :")
      response = ""
      for i in range(bytes):
	answer = self.read_byte()
	if answer == None:
	  return None
	response += answer
      #
      # Read and verify checksum
      #
      answer = self.read_byte()
      checksum = sum([ord(b) for b in response]) % 256
      if chr(checksum) != answer:
	self.log("??")
	return None
      flatten = lambda a,b: a + (ord(b) % 16, ord(b) / 16)
      return reduce(flatten, response, ())[:nybble_count]
    finally:
      self.log_exit()
  #
  # Read a batch of blocks.  Batches is a list of data to be read:
  #  [(address_of_first_nybble, length_in_nybbles), ...]
  # returns:
  #  [(nybble_at_address, ...), ...]
  #
  def read_batch(self,batches):
    self.log_enter("rb start")
    self.log_exit()
    try:
      if [b for b in batches if b[0] >= 0]:
	self.reset_06()
      result = []
      for batch in batches:
	address = batch[0]
	data = ()
	for start_pos in range(0,batch[1],self.MAXBLOCK):
	  for retry in range(self.MAXRETRIES):
	    bytes = min(self.MAXBLOCK, batch[1]-start_pos)
	    response = self.read_data(address + start_pos, bytes)
	    if response != None:
	      break
	    self.reset_06()
	  if response == None:
	    raise self.Ws2300Exception("read failed, retries exceeded")
	  data += response
	result.append(data)
      return result
    finally:
      self.log_enter("rb end")
      self.log_exit()
  #
  # Reset the device, read a block of nybbles at the passed address.
  #
  def read_safe(self,nybble_address,nybble_count):
    self.log_enter("rs")
    try:
      return self.read_batch([(nybble_address,nybble_count)])[0]
    finally:
      self.log_exit()
  #
  # Debug logging of serial IO.
  #
  def log(self, str):
    if not DEBUG_SERIAL:
      return
    self.log_buffer[-1] = self.log_buffer[-1] + str
  def log_enter(self, action):
    if not DEBUG_SERIAL:
      return
    self.log_nest += 1
    if self.log_nest == 1:
      if len(self.log_buffer) > 1000:
        del self.log_buffer[0]
      self.log_buffer.append("%5.2f %s " % (time.time() % 100, action))
      self.log_mode = 'e'
  def log_exit(self):
    if not DEBUG_SERIAL:
      return
    self.log_nest -= 1

#
# SerialClient.
#
class SerialClient(SerialPort):
  host			= None
  port			= None
  read_buf		= None
  soc			= None
  source		= None
  #
  # Initialise ourselves.
  #
  def __init__(self, source, host, port):
    self.host = host
    self.port = port
    self.source = source
    self.read_buf = ""
    self.open()
    self.release()
  #
  # Open if not already opened.
  #
  def open(self):
    if self.soc != None:
      return
    self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
      self.soc.connect((self.host, self.port))
    except socket.error, e:
      self.close()
      raise FatalError(self.source, "Can't connect to serial port server", e)
  #
  # Read a line.
  #
  def readline(self):
    line = ''
    char = self.soc.recv(1)
    while not char in ('', '\n'):
      line += char
      char = self.soc.recv(1)
    return line + char
  #
  # Clear incoming characters.
  #
  def clear(self):
    self.open()
    self.soc.send('c\n')
    self.read_buf = ""
  #
  # Close us.
  #
  def close(self):
    if self.soc == None:
      return
    self.read_buf = None
    soc = self.soc
    self.soc = None
    soc.close()
  #
  # Return when all characters have been written.
  #
  def flush(self):
    self.soc.send('f\n')
    line = self.readline()
    while '\n' in line and not line != 'F\n':
      line = self.readline()
  #
  # Read 1 byte with a timeout.
  #
  def read_byte(self, timeout):
    self.open()
    if not self.read_buf:
      self.soc.send('r %.2f\n' % timeout)
      line = self.readline()
      while '\n' in line and not line[0] == 'R':
	line = self.readline()
      if line == 'R\n':
	return None
      bytes = int(line[1:])
      while len(self.read_buf) < bytes:
	data = self.soc.recv(bytes - len(self.read_buf))
	if not data:
	  return None
	self.read_buf += data
    result = self.read_buf[0]
    self.read_buf = self.read_buf[1:]
    return result
  #
  # Release the port.
  #
  def release(self):
    if not self.soc:
      return
    soc = self.soc
    self.soc = None
    soc.close()
  #
  # Write data to the port.
  #
  def write(self, data):
    self.open()
    self.soc.send("w %d\n%s" % (len(data), data))

#
# A Serial server
#
class SerialServer(object):
  listen_soc		= None
  ws2300		= None
  #
  # Create one of us.
  #
  def __init__(self, source, ws2300, port):
    self.ws2300 = ws2300
    try:
      listen_port = int(port, 10)
      if listen_port <= 0 or listen_port >= 65536:
        raise ValueError()
    except ValueError:
      usage(source, 'Bad port "%s"' % port)
    self.listen_soc = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    self.listen_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
      self.listen_soc.bind(('', listen_port))
    except socket.error, e:
      raise FatalError(source, "Can't bind to %s" % listen_port, e)
    self.listen_soc.listen(5)
  #
  # Send a response.
  #
  def send(self, client, response):
    client.send(response)
  #
  # Commands we handle.
  #
  def cmd_c(self, client, line):
    self.ws2300.serial_port.clear()
  def cmd_f(self, client, line):
    self.ws2300.serial_port.flush()
    self.send(client, "F\n")
  def cmd_r(self, client, line):
    timeout = float(line)
    byte = self.ws2300.serial_port.read_byte(timeout)
    if byte == None:
      self.send(client, 'R\n')
    else:
      data = ""
      while byte != None:
        data += byte
	byte = self.ws2300.serial_port.read_byte(0.1)
      self.send(client, 'R %d\n%s' % (len(data), data))
  def cmd_w(self, client, line):
    bytes = int(line)
    data = ""
    while len(data) < bytes:
      recvd = client.recv(bytes - len(data))
      if not recvd:
        return
      data += recvd
    self.ws2300.serial_port.write(data)
  cmds = {
      'c':	cmd_c,
      'f':	cmd_f,
      'r':	cmd_r,
      'w':	cmd_w,
    }
  #
  # Listen for requests for a while.
  #
  def run(self, time_to_sleep):
    ready = select.select([self.listen_soc], [], [], time_to_sleep)
    if not ready[0]:
      return
    client = None
    def readline():
      line = ""
      char = client.recv(1)
      while not char in ('', '\n'):
	line += char
	char = client.recv(1)
      return line + char
    try:
      client = self.listen_soc.accept()[0]
      line = readline()
      while '\n' in line:
	cmd = self.__class__.cmds.get(line[0], None)
	if not cmd:
	  break
	cmd(self, client, line[1:].strip())
	line = readline()
    except socket.error:
      try:
	if client:
	  client.close()
      except socket.error:
        pass

#
# Print a data block.
#
def bcd2num(nybbles):
  digits = list(nybbles)[:]
  digits.reverse()
  return reduce(lambda a,b: a*10 + b, digits, 0)

def num2bcd(number, nybble_count):
  result = []
  for i in range(nybble_count):
    result.append(int(number % 10))
    number //= 10
  return tuple(result)

def bin2num(nybbles):
  digits = list(nybbles)
  digits.reverse()
  return reduce(lambda a,b: a*16 + b, digits, 0)

def num2bin(number, nybble_count):
  result = []
  number = int(number)
  for i in range(nybble_count):
    result.append(number % 16)
    number //= 16
  return tuple(result)

#
# A "Conversion" encapsulates a unit of measurement on the Ws2300.  Eg
# temperature, or wind speed.
#
class Conversion(object):
  description	= None		# Description of the units.
  nybble_count	= None		# Number of nybbles used on the WS2300
  units		= None		# Units name (eg hPa).
  #
  # Initialise ourselves.
  #  units	 - text description of the units.
  #  nybble_count- Size of stored value on ws2300 in nybbles
  #  description - Description of the units
  #
  def __init__(self, units, nybble_count, description):
    self.description = description
    self.nybble_count = nybble_count
    self.units = units
  #
  # Convert the nybbles read from the ws2300 to our internal value.
  #
  def binary2value(self, data): raise NotImplementedError()
  #
  # Convert our internal value to nybbles that can be written to the ws2300.
  #
  def value2binary(self, value): raise NotImplementedError()
  #
  # Print value.
  #
  def str(self, value): raise NotImplementedError()
  #
  # Convert the string produced by "str()" back to the value.
  #
  def parse(self, str): raise NotImplementedError()
  #
  # Transform data into something that can be written.  Returns:
  #  (new_bytes, ws2300.write_safe_args, ...)
  # This only becomes tricky when less than a nybble is written.
  #
  def write(self, data, nybble):
    return (data, data)
  #
  # Test if the nybbles read from the Ws2300 is sensible.  Sometimes a
  # communications error will make it past the weak checksums the Ws2300
  # uses.  This optional function implements another layer of checking -
  # does the value returned make sense.  Returns True if the value looks
  # like garbage.
  #
  def garbage(self, data):
    return False

#
# For values stores as binary numbers.
#
class BinConversion(Conversion):
  mult		= None
  scale		= None
  units		= None
  def __init__(self, units, nybble_count, scale, description, mult=1, check=None):
    Conversion.__init__(self, units, nybble_count, description)
    self.mult    = mult
    self.scale	= scale
    self.units	= units
  def binary2value(self, data):
    return (bin2num(data) * self.mult) / 10.0**self.scale
  def value2binary(self, value):
    return num2bin(int(value * 10**self.scale) // self.mult, self.nybble_count)
  def str(self, value):
    return "%.*f" % (self.scale, value)
  def parse(self, str):
    return float(str)

#
# For values stored as BCD numbers.
#
class BcdConversion(Conversion):
  offset	= None
  scale		= None
  units		= None
  def __init__(self, units, nybble_count, scale, description, offset=0):
    Conversion.__init__(self, units, nybble_count, description)
    self.offset  = offset
    self.scale	= scale
    self.units	= units
  def binary2value(self, data):
    num = bcd2num(data) % 10**self.nybble_count + self.offset
    return float(num) / 10**self.scale
  def value2binary(self, value):
    return num2bcd(int(value * 10**self.scale) - self.offset, self.nybble_count)
  def str(self, value):
    return "%.*f" % (self.scale, value)
  def parse(self, str):
    return float(str)

#
# For pressures.  Add a garbage check.
#
class PressureConversion(BcdConversion):
  def __init__(self):
    BcdConversion.__init__(self, "hPa", 5, 1, "pressure")
  def garbage(self, data):
    value = self.binary2value(data)
    return value < 900 or value > 1200

#
# For values the represent a date.
#
class ConversionDate(Conversion):
  format	= None
  def __init__(self, nybble_count, format):
    description =  format
    for xlate in "%Y:yyyy,%m:mm,%d:dd,%H:hh,%M:mm,%S:ss".split(","):
      description = description.replace(*xlate.split(":"))
    Conversion.__init__(self, "", nybble_count, description)
    self.format = format
  def str(self, value):
    return time.strftime(self.format, time.localtime(value))
  def parse(self, str):
    return time.mktime(time.strptime(str, self.format))

class DateConversion(ConversionDate):
  def __init__(self):
    ConversionDate.__init__(self, 6, "%Y-%m-%d")
  def binary2value(self, data):
    x = bcd2num(data)
    return time.mktime((
	x //     10000 % 100,
	x //       100 % 100,
        x              % 100,
	0,
	0,
	0,
	0,
	0,
	0))
  def value2binary(self, value):
    tm = time.localtime(value)
    dt = tm[2] +  tm[1] * 100 + (tm[0]-2000) * 10000
    return num2bcd(dt, self.nybble_count)

class DatetimeConversion(ConversionDate):
  def __init__(self):
    ConversionDate.__init__(self, 11, "%Y-%m-%d %H:%M")
  def binary2value(self, data):
    x = bcd2num(data)
    return time.mktime((
	x // 1000000000 % 100 + 2000,
	x //   10000000 % 100,
	x //     100000 % 100,
	x //        100 % 100,
        x               % 100,
	0,
	0,
	0,
	0))
  def value2binary(self, value):
    tm = time.localtime(value)
    dow = tm[6] + 1
    dt = tm[4]+(tm[3]+(dow+(tm[2]+(tm[1]+(tm[0]-2000)*100)*100)*10)*100)*100
    return num2bcd(dt, self.nybble_count)

class UnixtimeConversion(ConversionDate):
  def __init__(self):
    ConversionDate.__init__(self, 12, "%Y-%m-%d %H:%M:%S")
  def binary2value(self, data):
    x = bcd2num(data)
    return time.mktime((
	x //10000000000 % 100 + 2000,
	x //  100000000 % 100,
	x //    1000000 % 100,
	x //      10000 % 100,
	x //        100 % 100,
        x               % 100,
	0,
	0,
	0))
  def value2binary(self, value):
    tm = time.localtime(value)
    dt = tm[5]+(tm[4]+(tm[3]+(tm[2]+(tm[1]+(tm[0]-2000)*100)*100)*100)*100)*100
    return num2bcd(dt, self.nybble_count)

class TimestampConversion(ConversionDate):
  def __init__(self):
    ConversionDate.__init__(self, 10, "%Y-%m-%d %H:%M")
  def binary2value(self, data):
    x = bcd2num(data)
    return time.mktime((
	x // 100000000 % 100 + 2000,
	x //   1000000 % 100,
	x //     10000 % 100,
	x //       100 % 100,
        x              % 100,
	0,
	0,
	0,
	0))
  def value2binary(self, value):
    tm = time.localtime(value)
    dt = tm[4] + (tm[3] + (tm[2] + (tm[1] +  (tm[0]-2000)*100)*100)*100)*100
    return num2bcd(dt, self.nybble_count)

class TimeConversion(ConversionDate):
  def __init__(self):
    ConversionDate.__init__(self, 6, "%H:%M:%S")
  def binary2value(self, data):
    x = bcd2num(data)
    return time.mktime((
	0,
	0,
	0,
	x //     10000 % 100,
	x //       100 % 100,
        x              % 100,
	0,
	0,
	0)) - time.timezone
  def value2binary(self, value):
    tm = time.localtime(value)
    dt = tm[5] + tm[4]*100 + tm[3]*10000
    return num2bcd(dt, self.nybble_count)
  def parse(self, str):
    return time.mktime((0,0,0) + time.strptime(str, self.format)[3:]) + time.timezone

class WindDirectionConversion(Conversion):
  def __init__(self):
    Conversion.__init__(self, "deg", 1, "North=0 clockwise")
  def binary2value(self, data):
    return data[0] * 22.5
  def value2binary(self, value):
    return (int((value + 11.25) / 22.5),)
  def str(self, value):
    return "%g" % value
  def parse(self, str):
    return float(str)

class WindVelocityConversion(Conversion):
  def __init__(self):
    Conversion.__init__(self, "ms,d", 4, "wind speed and direction")
  def binary2value(self, data):
    return (bcd2num(data[:3])/10.0, bin2num(data[3:4]) * 22.5)
  def value2binary(self, value):
    return num2bcd(value[0]*10, 3) + num2bin((value[1] + 11.5) / 22.5, 1)
  def str(self, value):
    return "%.1f,%g" % value
  def parse(self, str):
    return tuple([float(x) for x in str.split(",")])

#
# For non-numerical values.
#
class TextConversion(Conversion):
  constants = None
  def __init__(self, constants):
    items = constants.items()[:]
    items.sort()
    fullname = ",".join([c[1]+"="+str(c[0]) for c in items]) + ",unknown-X"
    Conversion.__init__(self, "", 1, fullname)
    self.constants = constants
  def binary2value(self, data):
    return data[0]
  def value2binary(self, value):
    return (value,)
  def str(self, value):
    result = self.constants.get(value, None)
    if result != None:
      return result
    return "unknown-%d" % value
  def parse(self, str):
    result = [c[0] for c in self.constants.items() if c[1] == str]
    if result:
      return result[0]
    return int(value[8:],16)

#
# For values that are represented by one bit.
#
class ConversionBit(Conversion):
  bit		= None
  desc		= None
  def __init__(self, bit, desc):
    self.bit = bit
    self.desc = desc
    Conversion.__init__(self, "", 1, desc[0] + "=0," + desc[1] + "=1")
  def binary2value(self, data):
    return data[0] & (1 << self.bit) and 1 or 0
  def value2binary(self, value):
    return (value << self.bit,)
  def str(self, value):
    return self.desc[value]
  def parse(self, str):
    return [c[0] for c in self.desc.items() if c[1] == str][0]

class BitConversion(ConversionBit):
  def __init__(self, bit, desc):
    ConversionBit.__init__(self, bit, desc)
  #
  # Since Ws2300.write_safe() only writes nybbles and we have just one bit,
  # we have to insert that bit into the data_read so it can be written as
  # a nybble.
  #
  def write(self, data, nybble):
    data = (nybble & ~(1 << self.bit) | data[0],)
    return (data, data)

class AlarmSetConversion(BitConversion):
  bit		= None
  desc		= None
  def __init__(self, bit):
    BitConversion.__init__(self, bit, {0:"off", 1:"on"})

class AlarmActiveConversion(BitConversion):
  bit		= None
  desc		= None
  def __init__(self, bit):
    BitConversion.__init__(self, bit, {0:"inactive", 1:"active"})

#
# For values that are represented by one bit, and must be written as
# a single bit.
#
class SetresetConversion(ConversionBit):
  bit		= None
  def __init__(self, bit, desc):
    ConversionBit.__init__(self, bit, desc)
  #
  # Setreset bits use a special write mode.
  #
  def write(self, data, nybble):
    if data[0] == 0:
      operation = Ws2300.UNSETBIT
    else:
      operation = Ws2300.SETBIT
    return ((nybble & ~(1 << self.bit) | data[0],), [self.bit], operation)

#
# Conversion for history.  This kludge makes history fit into the framework
# used for all the other measures.
#
class HistoryConversion(Conversion):
  class HistoryRecord(object):
    temp_indoor		= None
    temp_outdoor	= None
    pressure_absolute	= None
    humidity_indoor	= None
    humidity_outdoor	= None
    rain		= None
    wind_speed		= None
    wind_direction	= None
    def __str__(self):
      return "%4.1fc %2d%% %4.1fc %2d%% %6.1fhPa %6.1fmm %2dm/s %5g" % (
	self.temp_indoor, self.humidity_indoor,
	self.temp_outdoor, self.humidity_outdoor, 
	self.pressure_absolute, self.rain,
	self.wind_speed, self.wind_direction)
    def parse(cls, str):
      rec = cls()
      toks = [tok.rstrip(string.ascii_letters + "%/") for tok in str.split()]
      rec.temp_indoor		= float(toks[0])
      rec.humidity_indoor	= int(toks[1])
      rec.temp_outdoor		= float(toks[2])
      rec.humidity_outdoor	= int(toks[3])
      rec.pressure_absolute	= float(toks[4])
      rec.rain			= float(toks[5])
      rec.wind_speed		= int(toks[6])
      rec.wind_direction	= int((float(toks[7]) + 11.25) / 22.5) % 16
      return rec
    parse = classmethod(parse)
  def __init__(self):
    Conversion.__init__(self, "", 19, "history")
  def binary2value(self, data):
    value = self.__class__.HistoryRecord()
    n = bin2num(data[0:5])
    value.temp_indoor = (n % 1000) / 10.0 - 30
    value.temp_outdoor = (n - (n % 1000)) / 10000.0 - 30
    n = bin2num(data[5:10])
    value.pressure_absolute = (n % 10000) / 10.0
    if value.pressure_absolute < 500:
      value.pressure_absolute += 1000
    value.humidity_indoor = (n - (n % 10000)) / 10000.0
    value.humidity_outdoor = bcd2num(data[10:12])
    value.rain = bin2num(data[12:15]) * 0.518
    value.wind_speed = bin2num(data[15:18])
    value.wind_direction = bin2num(data[18:19]) * 22.5
    return value
  def value2binary(self, value):
    result = ()
    n = int((value.temp_indoor + 30) * 10.0 + (value.temp_outdoor + 30) * 10000.0 + 0.5)
    result = result + num2bin(n, 5)
    n = value.pressure_absolute % 1000
    n = int(n * 10.0 + value.humidity_indoor * 10000.0 + 0.5)
    result = result + num2bin(n, 5)
    result = result + num2bcd(value.humidity_outdoor, 2)
    result = result + num2bin(int((value.rain + 0.518/2) / 0.518), 3)
    result = result + num2bin(value.wind_speed, 3)
    result = result + num2bin(value.wind_direction, 1)
    return result
  #
  # Print value.
  #
  def str(self, value):
    return str(value)
  #
  # Convert the string produced by "str()" back to the value.
  #
  def parse(self, str):
    return self.__class__.HistoryRecord.parse(str)

#
# Various conversions we know about.
#
conv_ala0	= AlarmActiveConversion(0)
conv_ala1	= AlarmActiveConversion(1)
conv_ala2	= AlarmActiveConversion(2)
conv_ala3	= AlarmActiveConversion(3)
conv_als0	= AlarmSetConversion(0)
conv_als1	= AlarmSetConversion(1)
conv_als2	= AlarmSetConversion(2)
conv_als3	= AlarmSetConversion(3)
conv_buzz	= SetresetConversion(3, {0:'on', 1:'off'})
conv_lbck	= SetresetConversion(0, {0:'off', 1:'on'})
conv_date	= DateConversion()
conv_dtme	= DatetimeConversion()
conv_utme	= UnixtimeConversion()
conv_hist	= HistoryConversion()
conv_stmp	= TimestampConversion()
conv_time	= TimeConversion()
conv_wdir	= WindDirectionConversion()
conv_wvel	= WindVelocityConversion()
conv_conn	= TextConversion({0:"cable", 3:"lost", 15:"wireless"})
conv_fore	= TextConversion({0:"rainy", 1:"cloudy", 2:"sunny"})
conv_spdu	= TextConversion({0:"m/s", 1:"knots", 2:"beaufort", 3:"km/h", 4:"mph"})
conv_tend	= TextConversion({0:"steady", 1:"rising", 2:"falling"})
conv_wovr	= TextConversion({0:"no", 1:"overflow"})
conv_wvld	= TextConversion({0:"ok", 1:"invalid", 2:"overflow"})
conv_lcon	= BinConversion("",    1, 0, "contrast")
conv_rec2	= BinConversion("",    2, 0, "record number")
conv_humi	= BcdConversion("%",   2, 0, "humidity")
conv_pres	= PressureConversion()
conv_rain	= BcdConversion("mm",  6, 2, "rain")
conv_temp	= BcdConversion("C",   4, 2, "temperature",   -3000)
conv_per2	= BinConversion("s",   2, 1, "time interval",  5)
conv_per3	= BinConversion("min", 3, 0, "time interval")
conv_wspd	= BcdConversion("m/s", 3, 1, "speed")

#
# Define a measurement on the Ws2300.  This encapsulates:
#  - The names (abbrev and long) of the thing being measured, eg wind speed.
#  - The location it can be found at in the Ws2300's memory map.
#  - The Conversion used to represent the figure.
#
class Measure(object):
  IDS		= {}		# map,    Measures defined. {id: Measure, ...}
  NAMES		= {}		# map,    Measures defined. {name: Measure, ...}
  address	= None		# int,    Nybble address in the Ws2300
  conv		= None		# object, Type of value
  id		= None		# string, Short name
  name		= None		# string, Long name
  reset		= None		# string, Id of measure used to reset this one
  def __init__(self, address, id, conv, name, reset=None):
    self.address = address
    self.conv = conv
    self.reset = reset
    if id != None:
      self.id = id
      assert not id in self.__class__.IDS
      self.__class__.IDS[id] = self
    if name != None:
      self.name = name
      assert not name in self.__class__.NAMES
      self.__class__.NAMES[name] = self
  def __hash__(self):
    return hash(self.id)
  def __cmp__(self, other):
    if isinstance(other, Measure):
      return cmp(self.id, other.id)
    return cmp(type(self), type(other))


#
# Conversion for raw Hex data.  These are created as needed.
#
class HexConversion(Conversion):
  def __init__(self, nybble_count):
    Conversion.__init__(self, "", nybble_count, "hex data")
  def binary2value(self, data):
    return data
  def value2binary(self, value):
    return value
  def str(self, value):
    return ",".join(["%x" % nybble for nybble in value])
  def parse(self, str):
    toks = str.replace(","," ").split()
    for i in range(len(toks)):
      s = list(toks[i])
      s.reverse()
      toks[i] = ''.join(s)
    list_str = list(''.join(toks))
    self.nybble_count = len(list_str)
    return tuple([int(nybble) for nybble in list_str])

#
# The raw nybble measure.
#
class HexMeasure(Measure):
  def __init__(self, address, id, conv, name):
    self.address = address
    self.name = name
    self.conv = conv

#
# A History record.  Again a kludge to make history fit into the framework
# developed for the other measurements.  History records are identified
# by their record number.  Record number 0 is the most recently written
# record, record number 1 is the next most recently written and so on.
#
class HistoryMeasure(Measure):
  HISTORY_BUFFER_ADDR	= 0x6c6	# int,    Address of the first history record
  MAX_HISTORY_RECORDS	= 0xaf	# string, Max number of history records stored
  LAST_POINTER		= None	# int,    Pointer to last record
  RECORD_COUNT		= None	# int,    Number of records in use
  HISTORY_WANTED	= False	# bool,   Set to True if history is in use
  recno			= None	# int,    The record number this represents
  conv			= conv_hist
  def __init__(self, recno):
    self.__class__.HISTORY_WANTED = True
    self.recno = recno
  def set_constants(cls, ws2300):
    if not cls.HISTORY_WANTED:
      return
    measures = [Measure.IDS["hp"], Measure.IDS["hn"]]
    data = read_measurements(ws2300, measures)
    cls.LAST_POINTER = int(measures[0].conv.binary2value(data[0]))
    cls.RECORD_COUNT = int(measures[1].conv.binary2value(data[1]))
  set_constants = classmethod(set_constants)
  def id(self):
    return "h%03d" % self.recno
  id = property(id)
  def name(self):
    return "history record %d" % self.recno
  name = property(name)
  def offset(self):
    return (self.LAST_POINTER - self.recno) % self.MAX_HISTORY_RECORDS
  offset = property(offset)
  def address(self):
    return self.HISTORY_BUFFER_ADDR + self.conv.nybble_count * self.offset
  address = property(address)

#
# The measurements we know about.  This is all of them documented in
# memory_map_2300.txt, bar the history.  History is handled specially.
# And of course, the "c?"'s aren't real measures at all - its the current
# time on this machine.
#
Measure(  -18, "ct",   conv_time, "this computer's time")
Measure(  -12, "cw",   conv_utme, "this computer's date time")
Measure(   -6, "cd",   conv_date, "this computer's date")
Measure(0x006, "bz",   conv_buzz, "buzzer")
Measure(0x00f, "wsu",  conv_spdu, "wind speed units")
Measure(0x016, "lb",   conv_lbck, "lcd backlight")
Measure(0x019, "sss",  conv_als2, "storm warn alarm set")
Measure(0x019, "sts",  conv_als0, "station time alarm set")
Measure(0x01a, "phs",  conv_als3, "pressure max alarm set")
Measure(0x01a, "pls",  conv_als2, "pressure min alarm set")
Measure(0x01b, "oths", conv_als3, "out temp max alarm set")
Measure(0x01b, "otls", conv_als2, "out temp min alarm set")
Measure(0x01b, "iths", conv_als1, "in temp max alarm set")
Measure(0x01b, "itls", conv_als0, "in temp min alarm set")
Measure(0x01c, "dphs", conv_als3, "dew point max alarm set")
Measure(0x01c, "dpls", conv_als2, "dew point min alarm set")
Measure(0x01c, "wchs", conv_als1, "wind chill max alarm set")
Measure(0x01c, "wcls", conv_als0, "wind chill min alarm set")
Measure(0x01d, "ihhs", conv_als3, "in humidity max alarm set")
Measure(0x01d, "ihls", conv_als2, "in humidity min alarm set")
Measure(0x01d, "ohhs", conv_als1, "out humidity max alarm set")
Measure(0x01d, "ohls", conv_als0, "out humidity min alarm set")
Measure(0x01e, "rhhs", conv_als1, "rain 1h alarm set")
Measure(0x01e, "rdhs", conv_als0, "rain 24h alarm set")
Measure(0x01f, "wds",  conv_als2, "wind direction alarm set")
Measure(0x01f, "wshs", conv_als1, "wind speed max alarm set")
Measure(0x01f, "wsls", conv_als0, "wind speed min alarm set")
Measure(0x020, "siv",  conv_ala2, "icon alarm active")
Measure(0x020, "stv",  conv_ala0, "station time alarm active")
Measure(0x021, "phv",  conv_ala3, "pressure max alarm active")
Measure(0x021, "plv",  conv_ala2, "pressure min alarm active")
Measure(0x022, "othv", conv_ala3, "out temp max alarm active")
Measure(0x022, "otlv", conv_ala2, "out temp min alarm active")
Measure(0x022, "ithv", conv_ala1, "in temp max alarm active")
Measure(0x022, "itlv", conv_ala0, "in temp min alarm active")
Measure(0x023, "dphv", conv_ala3, "dew point max alarm active")
Measure(0x023, "dplv", conv_ala2, "dew point min alarm active")
Measure(0x023, "wchv", conv_ala1, "wind chill max alarm active")
Measure(0x023, "wclv", conv_ala0, "wind chill min alarm active")
Measure(0x024, "ihhv", conv_ala3, "in humidity max alarm active")
Measure(0x024, "ihlv", conv_ala2, "in humidity min alarm active")
Measure(0x024, "ohhv", conv_ala1, "out humidity max alarm active")
Measure(0x024, "ohlv", conv_ala0, "out humidity min alarm active")
Measure(0x025, "rhhv", conv_ala1, "rain 1h alarm active")
Measure(0x025, "rdhv", conv_ala0, "rain 24h alarm active")
Measure(0x026, "wdv",  conv_ala2, "wind direction alarm active")
Measure(0x026, "wshv", conv_ala1, "wind speed max alarm active")
Measure(0x026, "wslv", conv_ala0, "wind speed min alarm active")
Measure(0x027, None,   conv_ala3, "pressure max alarm active alias")
Measure(0x027, None,   conv_ala2, "pressure min alarm active alias")
Measure(0x028, None,   conv_ala3, "out temp max alarm active alias")
Measure(0x028, None,   conv_ala2, "out temp min alarm active alias")
Measure(0x028, None,   conv_ala1, "in temp max alarm active alias")
Measure(0x028, None,   conv_ala0, "in temp min alarm active alias")
Measure(0x029, None,   conv_ala3, "dew point max alarm active alias")
Measure(0x029, None,   conv_ala2, "dew point min alarm active alias")
Measure(0x029, None,   conv_ala1, "wind chill max alarm active alias")
Measure(0x029, None,   conv_ala0, "wind chill min alarm active alias")
Measure(0x02a, None,   conv_ala3, "in humidity max alarm active alias")
Measure(0x02a, None,   conv_ala2, "in humidity min alarm active alias")
Measure(0x02a, None,   conv_ala1, "out humidity max alarm active alias")
Measure(0x02a, None,   conv_ala0, "out humidity min alarm active alias")
Measure(0x02b, None,   conv_ala1, "rain 1h alarm active alias")
Measure(0x02b, None,   conv_ala0, "rain 24h alarm active alias")
Measure(0x02c, None,   conv_ala2, "wind direction alarm active alias")
Measure(0x02c, None,   conv_ala2, "wind speed max alarm active alias")
Measure(0x02c, None,   conv_ala2, "wind speed min alarm active alias")
Measure(0x200, "st",   conv_time, "station set time",		reset="ct")
Measure(0x23b, "sw",   conv_dtme, "station current date time")
Measure(0x24d, "sd",   conv_date, "station set date",		reset="cd")
Measure(0x266, "lc",   conv_lcon, "lcd contrast (ro)")
Measure(0x26b, "for",  conv_fore, "forecast")
Measure(0x26c, "ten",  conv_tend, "tendency")
Measure(0x346, "it",   conv_temp, "in temp")
Measure(0x34b, "itl",  conv_temp, "in temp min",		reset="it")
Measure(0x350, "ith",  conv_temp, "in temp max",		reset="it")
Measure(0x354, "itlw", conv_stmp, "in temp min when",		reset="sw")
Measure(0x35e, "ithw", conv_stmp, "in temp max when",		reset="sw")
Measure(0x369, "itla", conv_temp, "in temp min alarm")
Measure(0x36e, "itha", conv_temp, "in temp max alarm")
Measure(0x373, "ot",   conv_temp, "out temp")
Measure(0x378, "otl",  conv_temp, "out temp min",		reset="ot")
Measure(0x37d, "oth",  conv_temp, "out temp max",		reset="ot")
Measure(0x381, "otlw", conv_stmp, "out temp min when",		reset="sw")
Measure(0x38b, "othw", conv_stmp, "out temp max when",		reset="sw")
Measure(0x396, "otla", conv_temp, "out temp min alarm")
Measure(0x39b, "otha", conv_temp, "out temp max alarm")
Measure(0x3a0, "wc",   conv_temp, "wind chill")
Measure(0x3a5, "wcl",  conv_temp, "wind chill min",		reset="wc")
Measure(0x3aa, "wch",  conv_temp, "wind chill max",		reset="wc")
Measure(0x3ae, "wclw", conv_stmp, "wind chill min when",	reset="sw")
Measure(0x3b8, "wchw", conv_stmp, "wind chill max when",	reset="sw")
Measure(0x3c3, "wcla", conv_temp, "wind chill min alarm")
Measure(0x3c8, "wcha", conv_temp, "wind chill max alarm")
Measure(0x3ce, "dp",   conv_temp, "dew point")
Measure(0x3d3, "dpl",  conv_temp, "dew point min",		reset="dp")
Measure(0x3d8, "dph",  conv_temp, "dew point max",		reset="dp")
Measure(0x3dc, "dplw", conv_stmp, "dew point min when",		reset="sw")
Measure(0x3e6, "dphw", conv_stmp, "dew point max when",		reset="sw")
Measure(0x3f1, "dpla", conv_temp, "dew point min alarm")
Measure(0x3f6, "dpha", conv_temp, "dew point max alarm")
Measure(0x3fb, "ih",   conv_humi, "in humidity")
Measure(0x3fd, "ihl",  conv_humi, "in humidity min",		reset="ih")
Measure(0x3ff, "ihh",  conv_humi, "in humidity max",		reset="ih")
Measure(0x401, "ihlw", conv_stmp, "in humidity min when",	reset="sw")
Measure(0x40b, "ihhw", conv_stmp, "in humidity max when",	reset="sw")
Measure(0x415, "ihla", conv_humi, "in humidity min alarm")
Measure(0x417, "ihha", conv_humi, "in humidity max alarm")
Measure(0x419, "oh",   conv_humi, "out humidity")
Measure(0x41b, "ohl",  conv_humi, "out humidity min",		reset="oh")
Measure(0x41d, "ohh",  conv_humi, "out humidity max",		reset="oh")
Measure(0x41f, "ohlw", conv_stmp, "out humidity min when",	reset="sw")
Measure(0x429, "ohhw", conv_stmp, "out humidity max when",	reset="sw")
Measure(0x433, "ohla", conv_humi, "out humidity min alarm")
Measure(0x435, "ohha", conv_humi, "out humidity max alarm")
Measure(0x497, "rd",   conv_rain, "rain 24h")
Measure(0x49d, "rdh",  conv_rain, "rain 24h max",		reset="rd")
Measure(0x4a3, "rdhw", conv_stmp, "rain 24h max when",		reset="sw")
Measure(0x4ae, "rdha", conv_rain, "rain 24h max alarm")
Measure(0x4b4, "rh",   conv_rain, "rain 1h")
Measure(0x4ba, "rhh",  conv_rain, "rain 1h max",		reset="rh")
Measure(0x4c0, "rhhw", conv_stmp, "rain 1h max when",		reset="sw")
Measure(0x4cb, "rhha", conv_rain, "rain 1h max alarm")
Measure(0x4d2, "rt",   conv_rain, "rain total",			reset=0)
Measure(0x4d8, "rtrw", conv_stmp, "rain total reset when",	reset="sw")
Measure(0x4ee, "wsl",  conv_wspd, "wind speed min",		reset="ws")
Measure(0x4f4, "wsh",  conv_wspd, "wind speed max",		reset="ws")
Measure(0x4f8, "wslw", conv_stmp, "wind speed min when",	reset="sw")
Measure(0x502, "wshw", conv_stmp, "wind speed max when",	reset="sw")
Measure(0x527, "wso",  conv_wovr, "wind speed overflow")
Measure(0x528, "wsv",  conv_wvld, "wind speed validity")
Measure(0x529, "wv",   conv_wvel, "wind velocity")
Measure(0x529, "ws",   conv_wspd, "wind speed")
Measure(0x52c, "w0",   conv_wdir, "wind direction")
Measure(0x52d, "w1",   conv_wdir, "wind direction 1")
Measure(0x52e, "w2",   conv_wdir, "wind direction 2")
Measure(0x52f, "w3",   conv_wdir, "wind direction 3")
Measure(0x530, "w4",   conv_wdir, "wind direction 4")
Measure(0x531, "w5",   conv_wdir, "wind direction 5")
Measure(0x533, "wsla", conv_wspd, "wind speed min alarm")
Measure(0x538, "wsha", conv_wspd, "wind speed max alarm")
Measure(0x54d, "cn",   conv_conn, "connection type")
Measure(0x54f, "cc",   conv_per2, "connection time till connect")
Measure(0x5d8, "pa",   conv_pres, "pressure absolute")
Measure(0x5e2, "pr",   conv_pres, "pressure relative")
Measure(0x5ec, "pc",   conv_pres, "pressure correction")
Measure(0x5f6, "pal",  conv_pres, "pressure absolute min",	reset="pa")
Measure(0x600, "prl",  conv_pres, "pressure relative min",	reset="pr")
Measure(0x60a, "pah",  conv_pres, "pressure absolute max",	reset="pa")
Measure(0x614, "prh",  conv_pres, "pressure relative max",	reset="pr")
Measure(0x61e, "plw",  conv_stmp, "pressure min when",		reset="sw")
Measure(0x628, "phw",  conv_stmp, "pressure max when",		reset="sw")
Measure(0x63c, "pla",  conv_pres, "pressure min alarm")
Measure(0x650, "pha",  conv_pres, "pressure max alarm")
Measure(0x6b2, "hi",   conv_per3, "history interval")
Measure(0x6b5, "hc",   conv_per3, "history time till sample")
Measure(0x6b8, "hw",   conv_stmp, "history last sample when")
Measure(0x6c2, "hp",   conv_rec2, "history last record pointer",reset=0)
Measure(0x6c4, "hn",   conv_rec2, "history number of records",	reset=0)

#
# Writes out csv strings.
#
class CsvDb(object):
  #
  # Append to a text file.
  #
  class TextAppender(object):
    filename	= None	# string, the name of the file to append to
    handle	= None	# string, the handle of the file to append to
    def __init__(self, filename):
      if not filename:
	self.handle = sys.stdout
      else:
	try:
	  self.handle = open(filename, "a")
	except EnvironmentError, e:
	  raise FatalError(filename, str(e), e)
    def write(self, line):
      self.handle.write(line + '\n')
      self.handle.flush()
    def close(self):
      if self.handle != sys.stdout:
	self.handle.close()
  #
  # Overwrite to text file with the data.
  #
  class TextWriter(object):
    filename	= None	# string, the name of the file to append to
    def __init__(self, filename):
      self.filename = filename
    def write(self, line):
      if not self.filename:
	handle = sys.stdout
      else:
	tmp_filename = self.filename + ".new"
	try:
	  handle = open(tmp_filename, "w")
	except EnvironmentError, e:
	  raise FatalError(tmp_filename, str(e), e)
      handle.write(line + '\n')
      if handle != sys.stdout:
	handle.close()
	try:
	  s = os.lstat(self.filename)
	  os.chmod(tmp_filename, stat.S_IMODE(s.st_mode))
	  try:
	    os.chown(tmp_filename, os.geteuid(), s.st_gid);
	    os.chown(tmp_filename, s.st_uid, s.st_gid);
	  except EnvironmentError, e:
            if e.errno != errno.EPERM:
	      raise
	except EnvironmentError, e:
	  if e.errno != errno.ENOENT:
	    raise
	os.rename(tmp_filename, self.filename)
    def close(self):
      pass
  #
  # Class that provides the essential parts of the PyDB interface.
  #
  class DummyPyDB(object):
    def Date(self, year, month, day):
      return "%04d-%02d-%02d" % (year, month, day)
    def Time(self, hour, minute, second):
      return "%02d:%02d:%02d" % (hour, minute, second)
    def Timestamp(self, year, month, day, hour, minute, second):
      return "%04d-%02d-%02dT%02d:%02d:%02d" % (
          year, month, day, hour, minute, second)
    def DateFromTicks(self, ticks):
      tm = time.gmtime(ticks)
      return "%04d-%02d-%02d" % (tm.tm_year, tm.tm_mon, tm.tm_mday)
    def TimeFromTicks(self, ticks):
      tm = time.gmtime(ticks)
      return "%02d:%02d:%02d" % (tm.tm_hour, tm.tm_min, tm.tm_sec)
    def TimestampFromTicks(self, ticks):
      tm = time.gmtime(ticks)
      return "%04d-%02d-%02dT%02d:%02d:%02d" % (
          tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec)
    def Binary(self, str):
      return str
  dbmodule	= DummyPyDB()
  separator	= None
  lines_written	= None
  read_only	= None
  textfile	= None
  def __init__(self, me, fieldcount, url):
    toks = url.split(":",1)
    self.separator = {'ssv': ' ', 'csv': ','}[toks[0].lower()]
    filename = len(toks) == 2 and toks[1]
    if toks[0].lower() != toks[0]:
      self.textfile = self.__class__.TextWriter(filename)
    else:
      self.textfile = self.__class__.TextAppender(filename)
    self.lines_written = 0
  def ws2300_write(self, fields):
    def pretty_print(field):
      return field.replace('\\','\\\\').replace('",','"\\,').replace("\n","\n\t")
    field_list = [pretty_print(str(field)) for field in fields]
    self.textfile.write(self.separator.join(field_list))
    self.lines_written += 1
  def close(self):
    self.textfile.close()
  def generator(self, table_field, where):
    return self.lines_written
  def select(self, table_field, where):
    return 0
  def connect(self):
    pass

#
# Sql DB.
#
class SqlDb(object):
  KEYWORD_RE	= re.compile("([a-z]\\w*)=((?:\"(?:[^\"]|\\\\\")*\")|(?:'(?:[^']|\\\\')*')|(?:[^\"',]+))(?:,|$)")
  RETRY_TIME	= 60		# int,    Max time to retry SQL commands
  connect_params= None		# dict,   {param_name: value, ...}
  cursor	= None		# object, a PyDB cursor
  db		= None		# object, a PyDB connection
  dbmodule	= None		# module, the PyDB database module		
  call_retry	= None		# bool,   True if self.retry() must be called
  insert_statement = None	# string, the insert statement to execite
  me		= None		# string, the program name
  operation	= None		# string, operation name for error messages
  read_only	= None		# bool,   if True don't modify the database
  #
  # Thrown when we must retry a database operation.
  #
  class RetryException(Exception):
    def __init__(self, sql, cause):
      Exception.__init__(self)
      self.sql = sql
      self.cause = cause
  #
  # Initialise outselves.
  #
  def __init__(self, me, fieldcount, url, insert_statement):
    self.me = me
    toks = url.split(":",1)
    self.insert_statement = insert_statement
    try:
      self.dbmodule = __import__(toks[0])
      for module_name in toks[0].split('.')[1:]:
	self.dbmodule = getattr(self.dbmodule, module_name)
    except ImportError, e:
      raise FatalError(self.me, 'can\'t file sql module "%s".' % toks[0], e)
    except AttributeError, e:
      raise FatalError(self.me, 'can\'t file sql module "%s".' % toks[0], e)
    params = self.__class__.KEYWORD_RE.findall(toks[1])
    self.connect_params = dict([(p[0],eval(p[1])) for p in params])
    #
    # Do a test connect now, then close the connection.  We can't connect
    # for real until we have daemonised, as some Sql drivers "kindly"
    # tell the server to shutdown the connection on a SystemExit.
    #
    self.call_retry = True
    self.connect()
    self.close()
  #
  # Connect to the database.
  #
  def connect(self):
    try:
      self.reconnect()
    except StandardError, e:
      raise self.error_object(e)
  #
  # Write a row of samples to the database.
  #
  def ws2300_write(self, fields):
    if self.call_retry:
      return self.retry(self.__class__.ws2300_write, fields)
    self.execute(self.insert_statement, fields)
    self.db.commit()
  #
  # Get the value of a generator.
  #
  def generator(self, table_field, where):
    if self.call_retry:
      return self.retry(self.__class__.generator, table_field, where)
    value = self.select(table_field, where)
    table, field = table_field.split(".")
    if not read_only:
      self.execute("update %s set %s = %s+1 where %s" % (table, field, field, where))
    self.db.commit()
    return value
  #
  # Execute a select query.
  #
  def select(self, table_field, where):
    if self.call_retry:
      return self.retry(self.__class__.select, table_field, where)
    table, field = table_field.split(".")
    self.execute("select %s from %s where %s" % (field, table, where))
    row = self.cursor.fetchone()
    if not row:
      raise FatalError(self.me, 'select("%s","%s") did not return a row.' % (table_field, where))
    return row[0]
  #
  # Close the database.
  #
  def close(self):
    if self.cursor != None:
      cursor = self.cursor
      self.cursor = None
      cursor.close()
    if self.db != None:
      db = self.db
      self.db = None
      db.close()
  #
  # Execute a sql statement.
  #
  def execute(self, sql, *args):
    self.operation = sql
    return self.cursor.execute(sql, *args)
  #
  # (Re)-connect to the database.
  #
  def reconnect(self):
    if self.cursor != None:
      return
    self.operation = "connect"
    self.db = self.dbmodule.connect(**self.connect_params)
    self.cursor = self.db.cursor()
  #
  # If a database operation fails for what look likes a transient error
  # retry for a time.
  #
  def retry(self, function, *args):
    self.call_retry = False
    try:
      start_time = time.time()
      while True:
	try:
	  try:
	    if self.cursor == None:
	      self.reconnect()
	    return function(self, *args)
	  except (self.dbmodule.OperationalError,self.dbmodule.InternalError), e:
	    if time.time() - start_time > self.__class__.RETRY_TIME:
	      raise
	except StandardError, e:
	  raise self.error_object(e)
	try:
	  self.close()
	except (self.dbmodule.OperationalError, self.dbmodule.InternalError), e:
	  pass
    finally:
      self.call_retry = True
  #
  # Create an exception object for raising.
  #
  def error_object(self, e):
    message = "%s - %s: %s" % (self.operation, e.__class__.__name__, str(e))
    return FatalError(self.me, message, e)

#
# A Ws2300 measure that will be logged.
#
class Field(object):
  values	= [0]
  _id		= None
  _measure	= None
  def __init__(self, me, id):
    self._id = id
    self._measure = Measure.IDS.get(id, None)
    if self._measure == None:
      raise FatalError(me, 'unknown measure "%s".' % id)
  #
  # field[index] returns the sample at index.
  #
  def __getitem__(self, index):
    return self.values[index]
  #
  # Discard all samples.
  #
  def _reset(self):
    self.values = []
  #
  # Record a new sample.
  #
  def _sample(self, value):
    self.values.append(value)
  #
  # Convert radians to degrees, making sure the result lies in (0,360].
  #
  def _deg(self, rad):
    return math.degrees(rad) % 360.0
  #
  # Get rid of unwanted rounding errors.
  #
  def _filter(self, val):
    return math.floor(val * 1000.0 + 0.5) / 1000.0
  #
  # Comupte the average of a function.
  #
  def _avg(self, func):
    if not self.values:
      return 0.0
    return sum([func(v) for v in self.values]) / self.cnt
  #
  # Return the square root of a value.  If the value is a small negative
  # number it is assumed to be a rounding error, and 0 is returned.
  #
  def _sqrt(self, value):
    assert value > -0.001
    if value < 0.0:
      return 0.0
    return math.sqrt(value)
  #
  # Find the maximum of the samples.
  #
  def max(self):
    if not self.values:
      return 0
    return max(self.values)
  max = property(max)
  #
  # Find the minimum of the samples.
  #
  def median(self):
    if not self.values:
      return 0
    v = values[:]
    v.sort()
    return v[len(v)//2]
  median = property(median)
  #
  # Find the minimum of the samples.
  #
  def min(self):
    if not self.values:
      return 0
    return min(self.values)
  min = property(min)
  #
  # Find the average of the samples.
  #
  def avg(self):
    return self._filter(self._avg(lambda x: x))
  avg = property(avg)
  #
  # Find the standard deviation of the samples.
  #
  def std(self):
    xx2 = self._avg(lambda x: x*x)
    # can't use self.avg here as it may be re-defined.
    x2 = self._avg(lambda x: x) ** 2
    return self._filter(self._sqrt(xx2 - x2))
  std = property(std)
  #
  # Return the number of samples.
  #
  def cnt(self):
    return len(self.values)
  cnt = property(cnt)

#
# Directions, being a polar measure, don't have their statistics computed
# the same way linear measures do.  Instead:
#
#   max = the most common direction in all values recorded (like the mode).
#   min = the least common direction in all values recorded.
#   avg = the Cartesian average.
#   std = the Cartesian standard deviation.
#
# Formula where needed were taken from:
#   http://www.webmet.com/met_monitoring/62.html
#
class DirectionField(Field):
  def __init__(self, me, id):
    Field.__init__(me, id)
  #
  # Return the most common direction.
  #
  def max(self):
    if not self.values:
      return 0
    counts = {}
    for v in self.values:
      counts.setdefault(v, 0)
      counts[v] += 1
    m = max(list(counts.values()))
    return [v for v in counts.items() if v[1] == m][0]
  max = property(max)
  #
  # Return the least common direction.
  #
  def min(self):
    if not self.values:
      return 0
    counts = {}
    for v in self.values:
      counts.setdefault(v, 0)
      counts[v] += 1
    m = min(list(counts.values()))
    return [v for v in counts.items() if v[1] == m][0]
  min = property(min)
  #
  # Return the vector average of the direction samples.
  #
  def _diravg(self):
    avg_sin = self._avg(lambda dir: math.sin(math.radians(dir)))
    avg_cos = self._avg(lambda dir: math.cos(math.radians(dir)))
    return self._filter(self._deg(math.atan2(avg_sin, avg_cos)))
  avg = property(_diravg)
  #
  # Return the vector standard deviation of the direction samples.
  #
  def std(self):
    avg_sin = self._avg(lambda dir: math.sin(math.radians(dir)))
    avg_cos = self._avg(lambda dir: math.cos(math.radians(dir)))
    e = self._sqrt(1.0 - avg_sin**2 - avg_cos**2)
    return self._filter(self._deg(math.asin(e) * math.fabs(1.0 - 0.1547 * e**3)))
  std = property(std)

#
# Velocity is a vector quantity.  Intutitively it can imagined thus: watch
# an air molecule below blown around by the wind over a period of time.  Where
# it ends up relative to its starting point defines the average wind speed and
# direction over that time period.
#
# Thus velocity is not a field per se, but rather a combination of two fields -
# the speed the air molecule needed to travel at in a straight line from the
# origin to get to its destination, and the direction of that line.
#
# This only effects the averages.  The other statistical measures for the
# velocity direction and speed are as for their scalar versions.
#
class VelocityField(object):
  dir		= None
  speed		= None
  values	= None
  _id		= None
  _measure	= None
  #
  # A field describing the speed vector.
  #
  class VelocitySpeedField(Field):
    velocity	= None
    def __init__(self, me, id, velocity):
      Field.__init__(self, me, id)
      self._id = id + ".speed"
      self._velocity = velocity
    #
    # Return the average of the speed vectors.
    #
    def avg(self):
      values = self._velocity.values
      if not values:
	return 0.0
      vavg = lambda f: sum([f(math.radians(v[1]))*v[0] for v in values]) / self.cnt
      avg_sin = vavg(math.sin)
      avg_cos = vavg(math.cos)
      return self._filter(self._sqrt(avg_sin**2 + avg_cos**2))
    avg = property(avg)
  #
  # A field describing the direction vector (which is weighted by speed).
  #
  class VelocityDirField(DirectionField):
    _velocity	= None
    def __init__(self, me, id, velocity):
      Field.__init__(self, me, id)
      self._id = id + ".dir"
      self._velocity = velocity
    #
    # Return the average of the directions, weighted by the speed vectors.
    #
    def avg(self):
      values = self._velocity.values
      if not values:
	return 0.0
      total = sum([v[0] for v in values])
      if total == 0.0:
	return DirectionField._diravg(self)
      vavg = lambda f: sum([f(math.radians(v[1]))*v[0] for v in values]) / total
      avg_sin = vavg(math.sin)
      avg_cos = vavg(math.cos)
      return self._filter(self._deg(math.atan2(avg_sin, avg_cos)))
    avg = property(avg)
  def __init__(self, me, id):
    self._id = id
    self.dir = self.__class__.VelocityDirField(me, id, self)
    self.direction = self.dir
    self.speed = self.__class__.VelocitySpeedField(me, id, self)
    self._measure = Measure.IDS[id]
    self._reset()
  def _reset(self):
    self.values = []
    self.dir._reset()
    self.speed._reset()
  def _sample(self, value):
    self.values.append(value)
    self.speed._sample(value[0])
    self.dir._sample(value[1])
  def cnt(self):
    return len(self.values)
  cnt = property(cnt)

#
# Record data and log it.  This structure is also the one the user
# sees when he writes ws.field in his expressions.
#
class Recorder(object):
  SECONDS_PER_DAY	= 24L * 60L * 60L
  measureRe		= re.compile("(?:^\s*|[^\w\s.]|[^.\s]\s+)ws[.]([a-z]\w*)")
  compiled_fields	= None	# list,   the compiled fields
  db			= None	# object, the database
  fields		= None	# list,   [Field, ...]
  id			= None	# string, a name
  last_write		= None	# time,   time the last write was done (or 0)
  measures		= None	# dict,   All measures used, {Measure:True, ...}
  namespace		= None	# dict,   local namespace for expressions
  next_sample		= None	# time,   the time for the next sample
  next_write		= None	# time,   the time for the next write
  sample_time		= None	# int,	  time between samoles
  save_time		= None	# int,    time between writes()
  split_fields		= None	# list,   the field names
  ws			= None	# record, the ws object
  class Ws(object):
    pass
  #
  # Parse the line.
  #
  def __init__(self, source, id, args):
    #
    # Parse our arguments.
    #
    self.id = id
    if len(args) < 1:
      usage(source)
    fields = args[0]
    url = (len(args) < 2 or not args[1]) and "csv" or args[1]
    try:
      self.sample_time = (len(args) < 3 or not args[2]) and 1.0 or float(args[2])
    except ValueError, e:
      usage(source, "illegal sample time '%s'." % args[2])
    try:
      self.save_time = (len(args) < 4 or not args[3]) and 1.0 or float(args[3])
      if self.save_time < self.sample_time:
	raise ValueError()
    except ValueError, e:
      usage(source, "illegal save time '%s'." % args[3])
    insert_statement = len(args) >= 5 and args[4]
    #
    # Compile the fields.
    #
    self.fields = []
    self.ws = self.__class__.Ws()
    self.measures = {}
    self.namespace = {"ws": self.ws}
    self.namespace.update(globals())
    self.compiled_fields = []
    self.split_fields = fields.split("!")
    for tok in self.split_fields:
      match = self.__class__.measureRe.search(tok)
      if match:
	self.add_field(source, match.group(1))
      try:
	expr = compile("lambda: " + tok, "", "eval")
	expr = eval(expr, self.namespace)
      except SyntaxError:
	usage(source, 'syntax error in field "%s".' % tok)
      self.compiled_fields.append(expr)
    #
    # Connect to the data sink.
    #
    toks = url.split(":", 1)
    if toks[0] in ("csv","ssv","CSV","SSV"):
      self.db = CsvDb(source, len(self.compiled_fields), url)
    else:
      self.db = SqlDb(source, len(self.compiled_fields), url, insert_statement)
      if not insert_statement:
	usage(source, "Insert statement required for SQL url.")
    self.namespace["db"] = self.db.dbmodule
    self.namespace["generator"] = self.db.generator
    self.namespace["select"] = self.db.select
    #
    # Verify the fields can evaluate.
    #
    self.namespace["starttime"] = time.time()
    self.namespace["endtime"] = time.time()
    old_read_only = self.db.read_only
    self.db.read_only = True
    self.eval_fields(source)
    self.db.read_only = False
    self.last_write = 0
  #
  # Add a field to record.
  #
  def add_field(self, source, id):
    if hasattr(self.ws, id):
      return
    if id == "wd":
      field = DirectionField(source, id)
    elif id == "wv":
      field = VelocityField(source, id)
    else:
      field = Field(source, id)
    self.fields.append(field)
    self.measures[field._measure] = True
    setattr(self.ws, id, field)
  #
  # Start of a recovery.
  #
  # The assumption is that only samples taken in the last save_time haven't
  # been recorded.  Ergo, the first sample we must consider is at the start
  # of that save period.  Set things up so that next_sample ends up pointing
  # there.
  #
  def recovery_init(self, last_sample):
    local_time = last_sample - time.timezone
    round = local_time % (24L * 60L * 60L) % self.save_time
    self.init(last_sample - round)
  #
  # Initialise ourselves - ie, prepare to do samples and writes.
  #
  # Set things up so the save_period starts now, and we record the next
  # sample immediately.
  #
  def init(self, utc_now):
    self.next_write = utc_now
    self.reset(utc_now)
  #
  # Reset the samples to prepare for the next round of sampling.
  #
  # Ie, the end of the last save periond becomes the start of this one,
  # and we take then next sample immediately.
  #
  def reset(self, utc_now):
    self.namespace["starttime"] = self.next_write
    self.next_sample = self.next_write
    local_now = utc_now - time.timezone
    round = local_now % (24L * 60L * 60L) % self.save_time
    self.next_write = utc_now + self.save_time - round
    for field in self.fields:
      field._reset()
  #
  # Record a sample.
  #
  def sample(self, samples, utc_now):
    results = [samples[f._measure] for f in self.fields]
    for field, result in zip(self.fields, results):
      field._sample(field._measure.conv.binary2value(result))
    while self.next_sample <= utc_now:
      self.next_sample += self.sample_time
  #
  # Write the recorded samples.
  #
  def write(self, source, utc_now):
    self.namespace["endtime"] = self.next_write
    self.db.ws2300_write(self.eval_fields(source))
    self.last_write = utc_now
    self.reset(utc_now)
  #
  # Evaluate the field expressions.
  #
  def eval_fields(self, source):
    values = []
    for field, expr in zip(self.split_fields, self.compiled_fields):
      try:
	value = expr()
	values.append(expr())
      except StandardError, e:
	raise FatalError(source, 'error in field "%s" - %s' % (field.strip(), str(e)), e)
      if isinstance(value, (Field, VelocityField)):
	raise FatalError(source, '"%s" is a field, not a value.' % field.strip())
    return values
  #
  # Shut down.
  #
  def close(self):
    self.db.close()

#
# Stuff for Recovery File handling.
#
class RecoveryFile(object):
  filename		= None	# string, The name of the recovery file
  handle		= None	# file,   The handle to the recovery file
  samples		= None	# list,   [(time, {measure:value, ...}), ...]
  #
  # Initialise outselves.
  #
  def __init__(self, filename):
    self.filename = filename
    #
    # Read in the old samples.  If the file doesn't exist thats ok.
    # 
    self.samples = []
    try:
      handle = open(self.filename)
    except EnvironmentError, e:
      if e.errno != errno.ENOENT:
	FatalError(self.filename, str(e), e)
      handle = None
    if handle != None:
      line_nr = 0
      try:
	for line in handle.readlines():
	  line_nr += 1
	  toks = line.rstrip().split()
	  dig = lambda h: tuple([int(d, 16) for d in h])
	  measure = lambda field: (Measure.IDS[field[0]], dig(field[1]))
	  measures = dict([measure(field.split('=')) for field in toks[1:]])
	  self.samples.append((int(toks[0]), measures))
	handle.close()
      except EnvironmentError, e:
	FatalError(self.filename, str(e), e)
      except (IndexError, ValueError, KeyError), e:
	raise FatalError(
	  self.filename,
	  (("Could not parse line %d.  "  % line_nr) +
	    "This is possibly a bug.  Try deleting the line."),
	  e)
    #
    # Write it.  This ensures we can can create the recovery file when put into
    # the background.
    #
    try:
      self.write()
    except EnvironmentError, e:
      FatalError(self.filename, str(e), e)
  #
  # Add a new set of measures to the recovery file.
  #
  def add_sample(self, utc_now, measures):
    self.samples.append((utc_now, measures))
  #
  # Return the samples we hold.
  #
  def get_samples(self):
    return self.samples[:]
  #
  # Purge unwanted records.
  #
  def purge(self, oldest):
    while self.samples and self.samples[0][0] <= oldest:
      del self.samples[0]
  #
  # Close us.
  #
  def close(self):
    pass
  #
  # Write the file.
  #
  def write(self):
    handle = open(self.filename + ".new", "w")
    for line in self.samples:
      hex = lambda v: ''.join(["%x" % digit for digit in v])
      fields = ' '.join(["%s=%s" % (k.id,hex(v)) for k,v in line[1].items()])
      handle.write("%d %s\n" % (line[0], fields))
    handle.close()
    os.rename(self.filename + ".new", self.filename)

#
# Write the data recorded.
#
def record_weather(
    source, ws2300, recorders, once_only,
    serial_server=None, recovery_file=None):
  try:
    #
    # Connect to the databases.
    #
    trace("record: connect\n")
    for recorder in recorders:
      recorder.db.connect()
    #
    # Pump the data.
    #
    while True:
      #
      # Who is ready to do something?
      #
      pt = lambda t: time.strftime("%M:%S", time.localtime(t))
      trace(
          "record: %s\n" %
	  repr([
	    "%s s=%s w=%s" % (recorder.id, pt(recorder.next_sample), pt(recorder.next_write))
	    for recorder in recorders]))
      writes = [(recorder.next_write, recorder) for recorder in recorders]
      writes.sort()
      samples = [(recorder.next_sample, recorder) for recorder in recorders]
      samples.sort()
      wakeup = min(samples[0][0], writes[0][0])
      samples_ready = [r[1] for r in samples if r[0] <= wakeup]
      writes_ready = [r[1] for r in writes if r[0] <= wakeup]
      #
      # If the next event is in the future sleep until it is scheduled.
      #
      ws2300.serial_port.release()
      time.tzset()
      utc_now = time.time()
      time_to_sleep = wakeup - utc_now
      while time_to_sleep > 0.0:
	trace("record: sleep=%f wakeup=%s\n" % (time_to_sleep, pt(wakeup)))
        if not serial_server:
	  time.sleep(time_to_sleep)
	else:
	  serial_server.run(time_to_sleep)
	utc_now = max(time.time(), wakeup)
	time_to_sleep = wakeup - utc_now
      #
      # Write all data scheduled for now.
      #
      if writes_ready:
	trace("record: writes=%s\n" % repr([r.id for r in writes_ready]))
	for recorder in writes_ready:
	  recorder.write(source, utc_now)
	  if recovery_file:
	    oldest_write = min([recorder.last_write for recorder in recorders])
	    recovery_file.purge(oldest_write)
	if once_only:
	  break

      #
      # Read any samples scheduled for now.
      #
      if samples_ready:
	trace("record: samples=%s\n" % repr([r.id for r in samples_ready]))
	measure_list = {}
	for recorder in samples_ready:
	  measure_list.update(recorder.measures)
	for retries in range(5):
	  samples = read_measurements(ws2300, measure_list.keys())
	  measures = dict(zip(measure_list.keys(), samples))
	  got_garbage = [m.id for m,v in measures.items() if m.conv.garbage(v)]
	  if not got_garbage:
	    break
	  trace(
	    "record: GARBAGE=%s %s\n" % (
	    repr(got_garbage),
	    " ".join(["%s=%s" % (m.id, str(m.conv.binary2value(v))) for m,v in measures.items()])))
	trace(
	    "record: %s\n" %
	    " ".join(["%s=%s" % (m.id, str(m.conv.binary2value(v))) for m,v in measures.items()]))
	for recorder in samples_ready:
	  recorder.sample(measures, utc_now)
	if recovery_file:
	  recovery_file.add_sample(utc_now, measures)
	  recovery_file.write()
  finally:
    exc_info = None
    for recorder in recorders:
      try:
	recorder.close()
      except:
	exc_info = sys.exc_info()
    if exc_info:
      raise exc_info[0], exc_info[1], exc_info[2]

#
# Initialise recorders, recovering anything recorded in the recovery file.
#
# This is done in the foreground so if the once-off initialisation stuffs
# up the error is visible.
#
def initialise_recorders(source, ws2300, recorders, recovery_file=None):
  #
  # Read in the file.
  #
  time.tzset()
  utc_now = time.time()
  recorders_updated = {}
  #
  # Push the samples in the recovery file through the recorders.
  #
  if recovery_file:
    saved_samples = recovery_file.get_samples()
    if saved_samples:
      for recorder in recorders:
	recorder.recovery_init(saved_samples[0][0])
    current_samples = {}
    for sample_time, sample_measures in saved_samples:
      samples_ready = [
	recorder for recorder in recorders
	if recorder.next_sample <= sample_time]
      measures_required = {}
      for recorder in samples_ready:
	measures_required.update(recorder.measures)
      measures = {}
      measures.update(current_samples)
      measures.update(sample_measures)
      missing_measures = [id for id in measures_required if not id in measures]
      if missing_measures:
	missing_samples = read_measurements(ws2300, missing_measures)
	missing_samples = dict(zip(missing_measures, missing_samples))
	measures.update(missing_samples)
	current_samples.update(missing_samples)
      for recorder in samples_ready:
	recorder.sample(measures, sample_time)
	recorders_updated[recorder] = True
  #
  # Write all recorders whose save_time has expired between when the
  # last sample was taken and now, and ensure every recorder is
  # initialised.
  #
  for recorder in recorders:
    if not recorder in recorders_updated:
      recorder.init(utc_now)
      continue
    if recorder.next_write >= utc_now:
      continue
    recorder.write(source, saved_samples[-1][0])
    recorder.init(utc_now)

#
# Print a usage message and exit.
#
def usage(me, message=None):
  if message:
    raise FatalError(me, message)
  me = os.path.basename(me)
  w = lambda x: sys.stderr.write(x + "\n")
  w("usage: %s help-measures" % me)
  w("       %s tty_device measurement[=value] ..." % me)
  w("       %s tty_device display fields [url [sample [save [insert]]]]" % me)
  w("       %s tty_device record filename [pidfile [email [recoveryfile [port]]]]" % me)
  sys.exit(1)

#
# Print help for the measurements.
#
def measurements_help():
  measurements = Measure.IDS.values()
  measurements.sort(lambda a,b: cmp(a.id, b.id))
  maxwidth = max([len(m.name) for m in measurements] + [0])
  for m in measurements:
    dots = '.' * (maxwidth - len(m.name) + 1)
    desc = [m.conv.description]
    if m.conv.units:
      desc = [m.conv.units] + desc
    desc = ", ".join(desc)
    if m.address < 0:
      address = "%05d.%-2d" % (m.address, m.conv.nybble_count)
    elif isinstance(m.conv, ConversionBit):
      address = "0x%03x.%-2d" % (m.address, m.conv.bit)
    else:
      address = "0x%03x:%-2d" % (m.address, m.conv.nybble_count)
    sys.stdout.write("%-4s  %s %s %s  %s\n" % (m.id,m.name,dots,address,desc))

#
# Parse a record file and return the list of specs it contains.  The file
# contains the same arguments that would be passed on the command line
# to "display".  There is one argument per line.  Unlike "display" you can
# record to multiple files.  Separate the arguments for each file with a
# blank line.  A line starting with a '#' is a comment.  It is handled in
# the same way as a blank line.
#
def parse_record_file(filename):
  try:
    handle = open(filename)
  except EnvironmentError, e:
    sys.stderr.write("Can't open " + filename + ": " + str(e))
    sys.exit(1)
  try:
    result = []
    recorder = []
    for line in handle.readlines():
      if not line.strip()[:1] in ("", "#"):
	l = line.rstrip("\r\n")
	if recorder and line.lstrip() != line:
	  recorder[-1] += l
	else:
	  recorder.append(l)
      elif recorder:
	result.append(recorder)
	recorder = []
    if recorder:
      result.append(recorder)
      recorder = []
  finally:
    handle.close()
  return result

#
# Parse a measure
#
def parse_measure(me, measure):
  #
  # A well known measure?
  #
  m = Measure.IDS.get(measure, None)
  if m != None:
    return [m]
  m = Measure.NAMES.get(measure, None)
  if m != None:
    return [m]
  #
  # How about a raw address?
  #
  toks = measure.split(":",1)
  address = None
  length = -1
  try:
    address = int(toks[0], 16)
    if len(toks) == 1:
      length = None
    else:
      length = int(toks[1])
  except Exception, e:
    pass
  if address != None:
    if length == -1:
      usage(me, "Unrecognised length '%s'." % toks[1])
    conv = HexConversion(length)
    return [HexMeasure(address, "hex", conv, toks[0])]
  #
  # How about history data?
  #
  recno_start = None
  recno_end = None
  if measure.startswith("history:"):
    try:
      toks = measure[8:].split("-",1)
      recno_start = int(toks[0])
      if len(toks) == 2:
        recno_end = int(toks[1])
    except ValueError, e:
      recno_start = HistoryMeasure.MAX_HISTORY_RECORDS
  elif measure.startswith("h") and len(measure) == 4:
    try:
      recno_start = int(measure[1:])
    except ValueError, e:
      recno_start = HistoryMeasure.MAX_HISTORY_RECORDS
  if recno_start != None:
    if recno_end == None:
      recno_end = recno_start
    if (recno_start < -1 or
        recno_start >= HistoryMeasure.MAX_HISTORY_RECORDS or
	recno_end < 0 or
	recno_end >= HistoryMeasure.MAX_HISTORY_RECORDS or
	recno_start > recno_end):
      usage(me, "Bad hisory record number '%s'." % measure)
    return [HistoryMeasure(recno) for recno in range(recno_start, recno_end+1)]
  #
  # If we got here we don't know what it is.
  #
  usage(me, "Bad measure '%s'." % measure)

#
# Parse the requests.
#
def parse_measurements(me, args):
  read_requests = []
  write_requests = []
  for arg in args:
    operation = arg.split("=",1)
    for measure in parse_measure(me, operation[0]):
      if len(operation) == 1:
	if measure.conv.nybble_count == None:
	  usage(me, "No length given for '%s'." % operation)
	read_requests.append(measure)
      else:
	if measure.address < 0:
	  usage(me, "Can't modify measure '%s'." % operation[0])
	elif operation[1] == "reset":
	  if measure.reset == None:
	    usage(me, "I don't know how to reset measure '%s'." % operation[0])
	  data = None
	else:
	  try:
	    data = measure.conv.value2binary(measure.conv.parse(operation[1]))
	  except StandardError:
	    raise
	    usage(me, "'%s' does parse as a %s." % (operation[1], measure.name))
	write_requests.append((measure, data))
  return read_requests, write_requests

#
# Read the requests.
#
def read_measurements(ws2300, read_requests):
  if not read_requests:
    return []
  #
  # Optimise what we have to read.
  #
  batches = [(m.address, m.conv.nybble_count) for m in read_requests]
  batches.sort()
  index = 1
  addr = {batches[0][0]: 0}
  while index < len(batches):
    same_sign = (batches[index-1][0] < 0) == (batches[index][0] < 0)
    same_area = batches[index-1][0] + batches[index-1][1] + 6 >= batches[index][0]
    if not same_sign or not same_area:
      addr[batches[index][0]] = index
      index += 1
      continue
    addr[batches[index][0]] = index-1
    batches[index-1] = batches[index-1][0], batches[index][0] + batches[index][1] - batches[index-1][0]
    del batches[index]
  #
  # Read the data.
  #
  nybbles = ws2300.read_batch(batches)
  #
  # Return the data read in the order it was requested.
  #
  results = []
  for measure in read_requests:
    index = addr[measure.address]
    offset = measure.address - batches[index][0]
    results.append(nybbles[index][offset:offset+measure.conv.nybble_count])
  return results

#
# Print the results of what was read.
#
def print_measurements(requests, data_read):
  maxname = max([len(r.name) for r in requests if r.name != None] + [0])
  for measure, nybbles in zip(requests, data_read):
    output = measure.conv.str(measure.conv.binary2value(nybbles))
    sys.stdout.write("%-*s = %s" % (maxname, measure.name, output))
    if DEBUG_VALUE:
      sys.stdout.write(" " + repr(nybbles).replace(" ",""))
    sys.stdout.write("\n")

#
# Write the data requested.
#
def write_measurements(ws2300, write_requests):
  #
  # For bit values, read the data we are about to write.
  #
  measurements = [m for m, _ in write_requests if isinstance(m.conv, ConversionBit)]
  data_read = read_measurements(ws2300, measurements)
  cache = {}
  for m, nybbles in zip(measurements, data_read):
    cache[m.address] = nybbles[0]
  #
  # If we are resetting things, read the reset values.
  #
  resets = [i for i in range(len(write_requests)) if write_requests[i][1] == None]
  for i in resets:
    measure, data = write_requests[i]
    if type(measure.reset) != type(""):
      write_requests[i] = (measure, measure.conv.value2binary(measure.reset))
  reset_reads = [i for i in resets if type(write_requests[i][0].reset) == type("")]
  measurements = [Measure.IDS[write_requests[i][0].reset] for i in reset_reads]
  data_read = read_measurements(ws2300, measurements)
  for m, data, i in zip(measurements, data_read, reset_reads):
    measure = write_requests[i][0]
    value = measure.conv.value2binary(m.conv.binary2value(data))
    write_requests[i] = (measure, value)
  #
  # Now we can write the data.
  #
  maxlen = max([len(m.name) for m, _ in write_requests] + [0])
  for m, data in write_requests:
    sys.stdout.write("%-*s <- %s" % (maxlen, m.name, m.conv.str(m.conv.binary2value(data))))
    sys.stdout.flush()
    nybble = cache.get(m.address, None)
    write_command = m.conv.write(data, nybble)
    if DEBUG_VALUE:
      sys.stdout.write(" " + repr(write_command[0]).replace(" ",""))
    if not DISABLE_WRITE:
      ws2300.write_safe(m.address, *write_command[1:])
    for offset, nybble in enumerate(write_command[0]):
      cache[m.address + offset] = nybble
    sys.stdout.write("\n")
    sys.stdout.flush()

#
# Display the measurements.
#
def process_measurements(me, ws2300, args):
  read_requests, write_requests = parse_measurements(me, args)
  HistoryMeasure.set_constants(ws2300)
  data_read = read_measurements(ws2300, read_requests)
  print_measurements(read_requests, data_read)
  write_measurements(ws2300, write_requests)

#
# Identical to SystemExit, but this is the program daemonising.  Thus the
# background portion is continuing to run.  This means most cleanup actions
# should not happen.
#
class BackgroundExit(SystemExit):
  def __init__(self):
    SystemExit.__init__(self)

#
# Make stdout and stderr write to syslog.
#
class SyslogFile:
  priority		= None	# syslog priority
  def __init__(self, priority):
    self.priority = priority
  def write(self, message):
    syslog.syslog(self.priority, message.rstrip())
  def close(self):
    pass

#
# Put the program into the background.
#
def demonise(me, pid_file):
  if pid_file in ('.', None):
    return None
  if pid_file == '-':
    pid_handle = None
  else:
    try:
      pid_handle = open(pid_file, "w")
    except EnvironmentError, e:
      raise FatalErro(me, str(e), e)
  pid = os.fork()
  if pid != 0:
    raise BackgroundExit()
  #
  # Detach us from the terminal.
  #
  try:
    os.setpgrp()
  except AttributeError:
    pass
  try:
    os.setsid()
  except AttributeError:
    pass
  except EnvironmentError, e:
    if e.errno != errno.EPERM:
      raise
  #
  # Arrange logging to be written to syslog, trying all the while to ensure
  # we can tell the user what when wrong if something stuffs up!
  #
  sys.stdin.close()
  sys.stdin = None
  null = os.open("/dev/null", os.O_RDONLY)
  if null != 0:
    os.dup2(null, 0)
    os.close(null)
  sys.stdin = os.fdopen(0)
  ostdout, ostderr = sys.stdout, sys.stderr
  try:
    import syslog
    syslog.openlog(os.path.basename(me), syslog.LOG_INFO, syslog.LOG_DAEMON)
    sys.stdout = SyslogFile(syslog.LOG_INFO)
    sys.stderr = SyslogFile(syslog.LOG_ERR)
  except ImportError:
    pass
  null = os.open("/dev/null", os.O_WRONLY)
  if isinstance(sys.stdout, SyslogFile):
    ostdout.close()
    if null != 1:
      os.dup2(null, 1)
  if isinstance(sys.stderr, SyslogFile):
    ostderr.close()
    if null != 2:
      os.dup2(null, 2)
  if not null in (1,2):
    os.close(null)
  #
  # And write out pid to the pidfile.
  #
  if pid_handle == None:
    return None
  pid_handle.write(str(os.getpid()))
  pid_handle.close()
  return pid_file

#
# If some sort of error occurred, send an email.
#
def email_fatal(me, email, lines):
  stdin = run(['/usr/sbin/sendmail', '-t'])
  w = lambda s: stdin.write(s + "\n")
  if not isinstance(email, (type(()), type([]))):
    email = [email]
  w("To: " + ",".join(email))
  w("Subject: " + me + " FAILED!")
  w("")
  for line in lines:
    w(line.rstrip())
  w("")
  w("")
  w("--")
  w("Regards,")
  w(me)
  w("Running on " + socket.gethostname())
  stdin.close()

#
# Daemon mode recording.
#
def record_daemon(
    me, ws2300,
    filename, pid_file=None, email=None, recovery_file=None, port=None):
  #
  # The idea here is we check everything we can, so failing while hidden in
  # the background is unlikely.
  #
  specs = parse_record_file(filename)
  recorders =  [
      Recorder(filename, str(id), specs[id])
      for id in range(len(specs))]
  if recovery_file in (None, '.'):
    recovery_file = None
  else:
    recovery_file = RecoveryFile(recovery_file)
  if port in (None, '.'):
    serial_server = None
  else:
    serial_server = SerialServer(me, ws2300, port)
  initialise_recorders(filename, ws2300, recorders, recovery_file)
  #
  # Everything seems OK.  Go into the background.
  #
  pid_filename = demonise(me, pid_file)
  #
  # Ensure we exit nicely on a signal.
  #
  def sigtrap(sig, stack): sys.exit(0)
  for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
    if signal.getsignal(sig) != signal.SIG_IGN:
      signal.signal(sig, sigtrap)
  #
  # If he wants us to send em email then catch errors, otherwise just
  # let Python report them.
  #
  if email in ('', '-', None):
    class exception: pass
  else:
    exception = StandardError
  #
  # Run the daemon.
  #
  try:
    try:
      if isinstance(sys.stdout, SyslogFile):
        sys.stdout.write("Daemon Started.\n")
      record_weather(
        filename, ws2300, recorders,
	once_only=False, serial_server=serial_server, recovery_file=recovery_file)
    except exception:
      string_file = cStringIO.StringIO()
      exc = sys.exc_info()
      traceback.print_exception(exc[0], exc[1], exc[2], None, string_file)
      backtrace = ["  "+l for l in string_file.getvalue().splitlines()]
      the_story = [
          "I fell over in a screaming heap.  Sorry.",
	  "Here is the Python backtrace:",
	  ""
	]
      try:
	email_fatal(me, email, the_story + backtrace)
      except:
	traceback.print_exc()
      raise
  finally:
    if isinstance(sys.stdout, SyslogFile):
      sys.stdout.write("Daemon Stopped.\n")
    if pid_filename != None:
      try:
	os.unlink(pid_filename)
      except EnvironmentError, e:
        if e.errno != errno.ENOENT:
	  raise

#
# Our entry point.
#
def main(argv):
  #
  # Initial parsing of command line.
  #
  me = "ws2300.py"
  if len(argv) >= 1:
    me = argv[0]
  if len(argv) < 2:
    usage(me)
  tty_device = argv[1]
  if tty_device == "help-measures":
    measurements_help()
    sys.exit(0)
  if tty_device == "version":
    sys.stdout.write("Version: " + VERSION + "\n")
    sys.exit(0)
  #
  # Do the deed.
  #
  if len(argv) < 3:
    usage(me)
  if tty_device == ".":
    serialPort = None
  elif tty_device.find("://") != -1:
    match = re.match("ws2300://([^:/]+):([0-9]+)$", tty_device)
    if not match:
      usage(me, 'Invalid ws2300 server "%s"' % tty_port)
    serialPort = SerialClient(me, match.group(1), int(match.group(2)))
  else:
    serialPort = LinuxSerialPort(tty_device)
  try:
    try:
      backgroundExit = False
      ws2300 = Ws2300(serialPort)
      if argv[2] == "display":
	recorders = [Recorder(me, "0", argv[3:])]
	initialise_recorders(me, ws2300, recorders)
	record_weather(me, ws2300, recorders, True)
      elif argv[2] == "record":
	if len(argv) < 4 or len(argv) > 8:
	  usage(me, "Wrong number of arguments.")
	record_daemon(me, ws2300, *argv[3:])
      else:
	process_measurements(me, ws2300, argv[2:])
    except BackgroundExit:
      backgroundExit = True
      sys.exit(0)
    except FatalError, e:
      sys.stderr.write("%s: %s\n" % (os.path.basename(e.source), e.message))
      sys.exit(1)
  finally:
    if not backgroundExit:
      if serialPort != None:
	serialPort.close()
      #
      # Write the serialPort log.
      #
      if DEBUG_SERIAL:
	for line in ws2300.log_buffer:
	  sys.stdout.write(line + "\n")

if __name__ == "__main__":
  main(sys.argv)
