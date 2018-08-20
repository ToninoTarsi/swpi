#!/usr/bin/env python3

import sys
import os
import time
import datetime

sys.path.append('../')


current_milli_time = lambda: int(round(time.time() * 1000))

def log(message) :
    print datetime.datetime.now().strftime("[%d/%m/%Y-%H:%M:%S]") , message
    with open("tx.log", "a") as myfile:
        myfile.write(datetime.datetime.now().strftime("[%d/%m/%Y-%H:%M:%S]")  + ' '  + message + '\n')

os.system( "sudo /opt/vc/bin/tvservice -o > /dev/null" )
os.system( "echo 1 | sudo tee /sys/class/leds/led0/brightness > /dev/null" )

current_milli_time = lambda: int(round(time.time() * 1000))

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
#lora.set_modem_config_simple(rf95.BW_125KHZ,rf95.CODING_RATE_4_8,rf95.SPREADING_FACTOR_512CPS)

#lora.set_modem_config(rfm95.Bw125Cr45Sf128 )  #      Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on. Default medium range.
#lora.set_modem_config(rf95.Bw500Cr45Sf128 )    #     Bw = 500 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on. Fast+short range.
#lora.set_modem_config(rf95.Bw31_25Cr48Sf512)    #    Bw = 31.25 kHz, Cr = 4/8, Sf = 512chips/symbol, CRC on. Slow+long range.
#lora.set_modem_config(rf95.Bw125Cr48Sf4096)    #     Bw = 125 kHz, Cr = 4/8, Sf = 4096chips/symbol, CRC on. Slow+long range.


# Send  packets
i = 0
while (True):
    os.system( "echo 0 | sudo tee /sys/class/leds/led0/brightness > /dev/null" )  # ON
    p = "$SW,1,315.0,0,0,11.7,89,948,0*01"
    i = i + 1
    m_start = current_milli_time()
    lora.send(lora.str_to_data(p))
    lora.wait_packet_sent()
    os.system( "echo 1 | sudo tee /sys/class/leds/led0/brightness > /dev/null" ) # OFF
    sent_time = current_milli_time()-m_start
    log("Sent packe(" +str(sent_time) + "ms) " + p)
#    lora.set_mode_idle()
    
    # wait ack
    count = 0
    while ( count < 300  and not lora.available()):
        time.sleep(0.01)
        count = count + 1
    if (lora.available() ):
        os.system( "echo 0 | sudo tee /sys/class/leds/led0/brightness > /dev/null" )  # ON 
        data = lora.recv()
        rec_str = ""
        for ch in data:
            rec_str = rec_str + chr(ch)
        log ('ACT RSSI: ' + str(lora.last_rssi) + ' Message: ' + rec_str)
    else:
        log ("ACT Timeout")

    lora.set_mode_idle() 
    time.sleep(0.5)                 
    os.system( "echo 1 | sudo tee /sys/class/leds/led0/brightness > /dev/null" ) # OFF   
    time.sleep(1.5)



