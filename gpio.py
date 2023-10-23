import RPi.GPIO as GPIO
import sys
import time

if ( len(sys.argv) != 2):
    print("gpio pin_number")
    exit()

pin_in = int(sys.argv[1])

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(pin_in, GPIO.IN,pull_up_down=GPIO.PUD_UP)   

while (1):
    o = GPIO.input(pin_in)
    print(o)
    time.sleep(1)
