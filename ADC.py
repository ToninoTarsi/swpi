#!/usr/bin/env python

# just some bitbang code for testing all 8 channels

import RPi.GPIO as GPIO, time, os

SPICLK = 11
SPIMOSI = 10
SPIMISO = 9
SPICS = 8

class MCPADC():
	
	def __init__(self, type="MCP3002" ):
		self.type = type
		
		GPIO.setmode(GPIO.BCM)
		
		# change these as desired
		# set up the SPI interface pins 
		GPIO.setup(SPIMOSI, GPIO.OUT)
		GPIO.setup(SPIMISO, GPIO.IN)
		GPIO.setup(SPICLK, GPIO.OUT)
		GPIO.setup(SPICS, GPIO.OUT)

	def readadc(self,adcnum):
		if (self.type == "MCP3002"):
			return self.readadc3002(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)
		elif (self.type == "MCP3008"):
			return self.readadc3008(adcnum, SPICLK, SPIMOSI, SPIMISO, SPICS)	
		else:
			return None

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
	def readadc3008(self,adcnum, clockpin, mosipin, misopin, cspin):
		if ((adcnum > 7) or (adcnum < 0)):
			return -1
			
		GPIO.output(cspin, True)
	
		GPIO.output(clockpin, False)  # start clock low
		GPIO.output(cspin, False)     # bring CS low
	
		commandout = adcnum
		commandout |= 0x18  # start bit + single-ended bit
		commandout <<= 3    # we only need to send 5 bits here
		for i in range(5):
			if (commandout & 0x80):
				GPIO.output(mosipin, True)
			else:
				GPIO.output(mosipin, False)
				commandout <<= 1
				GPIO.output(clockpin, True)
				GPIO.output(clockpin, False)
	
		adcout = 0
		# read in one empty bit, one null bit and 10 ADC bits
		for i in range(12):
			GPIO.output(clockpin, True)
			GPIO.output(clockpin, False)
			adcout <<= 1
			if (GPIO.input(misopin)):
				adcout |= 0x1
	
		GPIO.output(cspin, True)
	
		adcout /= 2       # first bit is 'null' so drop it
		return adcout
	
	# read SPI data from MCP3002 chip, 2 possible adc's (0 thru 1)
	def readadc3002(self,adcnum, clockpin, mosipin, misopin, cspin):
		if ((adcnum > 1) or (adcnum < 0)):
			return -1
		if (adcnum == 0):
			commandout = 0x6
		else:
			commandout = 0x7
				
		GPIO.output(cspin, True)
	
		GPIO.output(clockpin, False)  # start clock low
		GPIO.output(cspin, False)     # bring CS low
	
		#commandout = 0x6  #start bit and 1, 0 to select single ended ch0
		commandout <<= 5    # we only need to send 3 bits here
		for i in range(3):
			if (commandout & 0x80):
				GPIO.output(mosipin, True)
			else:
				GPIO.output(mosipin, False)
				commandout <<= 1
				GPIO.output(clockpin, True)
				GPIO.output(clockpin, False)
	
		adcout = 0
		# read in one empty bit, one null bit and 10 ADC bits
		for i in range(12):
			GPIO.output(clockpin, True)
			GPIO.output(clockpin, False)
			adcout <<= 1
			if (GPIO.input(misopin)):
				adcout |= 0x1
	
		GPIO.output(cspin, True)
	
		adcout /= 2       # first bit is 'null' so drop it
		return adcout


if __name__ == '__main__':	


	# Note that bitbanging SPI is incredibly slow on the Pi as its not
	# a RTOS - reading the ADC takes about 30 ms (~30 samples per second)
	# which is awful for a microcontroller but better-than-nothing for Linux

	print "| #0 \t #1 \t #2 \t #3 \t #4 \t #5 \t #6 \t #7\t|"
	print "-----------------------------------------------------------------"
	while True:
		print "|",
		adc = MCPADC("MCP3002")
		for adcnum in range(2):
			ret = adc.readadc(adcnum) 
			print ret,"\t",
		print "|"
		time.sleep(1)
