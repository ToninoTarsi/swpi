import RPi.GPIO as GPIO
import sys
import time

if ( len(sys.argv) != 2):
    print("gpio pin_number")
    exit()

__PIN_A = sys.argv(1)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(__PIN_A, GPIO.IN,pull_up_down=GPIO.PUD_UP)   

while (1):
    o = GPIO.input(__PIN_A)
    print(o)
    time.sleep(1)
