#!/usr/bin/env python3

import sys
import os
import time
import datetime

sys.path.append('../')

import rf95

# import RPi.GPIO as GPIO
# 
# 
# def handle_interrupt( channel):
#         # Read the interrupt register
#         print 'handle_interrupt'
# 
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(25, GPIO.IN)
# GPIO.add_event_detect(25, GPIO.RISING, callback=handle_interrupt)



def log(message) :
    print datetime.datetime.now().strftime("[%d/%m/%Y-%H:%M:%S]") , message
    with open("rx.log", "a") as myfile:
        myfile.write(datetime.datetime.now().strftime("[%d/%m/%Y-%H:%M:%S]")  + ' '  + message + '\n')




os.system( "sudo /opt/vc/bin/tvservice -o > /dev/null" )
os.system( "echo 1 | sudo tee /sys/class/leds/led0/brightness > /dev/null" )

# Create rf95 object with CS0 and external interrupt on pin 25
lora = rf95.RF95(1,0, None,None)

if not lora.init(): # returns True if found
    log("RF95 not found")
    quit(1)
else:
    log("RF95 LoRa mode ok")

# set frequency, power and mode
lora.set_frequency(869.2)
lora.set_tx_power(20)
#lora.set_modem_config_simple(rf95.BW_31K25HZ,rf95.CODING_RATE_4_8,rf95.SPREADING_FACTOR_512CPS)


#lora.set_modem_config(rfm95.Bw125Cr45Sf128 )  #      Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on. Default medium range.
#lora.set_modem_config(rf95.Bw500Cr45Sf128 )    #     Bw = 500 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on. Fast+short range.
#lora.set_modem_config(rf95.Bw31_25Cr48Sf512)    #    Bw = 31.25 kHz, Cr = 4/8, Sf = 512chips/symbol, CRC on. Slow+long range.
#lora.set_modem_config(rf95.Bw125Cr48Sf4096)    #     Bw = 125 kHz, Cr = 4/8, Sf = 4096chips/symbol, CRC on. Slow+long range.

 


# Send  packets
while (True):
    while not lora.available():
        time.sleep(0.1)
#    os.system( "echo 0 | sudo tee /sys/class/leds/led0/brightness > /dev/null" )
    data = lora.recv()
    rec_str = ""
    good = True
    for ch in data:
        if ord(chr(ch)) < 128 :
            rec_str = rec_str + chr(ch)
        else:
            good = False
    if (True):
        log ('RSSI: ' + str(lora.last_rssi) + ' Message: ' + rec_str)
    
#    time.sleep(0.100)
#    lora.send(lora.str_to_data("OK"))
#    lora.wait_packet_sent()
#    lora.wait_packet_sent()
    
    
    lora.set_mode_idle()
    #time.sleep(0.100)
#    os.system( "echo 1 | sudo tee /sys/class/leds/led0/brightness > /dev/null" )
    
    
                




