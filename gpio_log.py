import RPi.GPIO as GPIO
import time,datetime

# Set up GPIO using BCM numbering
GPIO.setmode(GPIO.BCM)

# Set pin 23 as input
GPIO.setup(23, GPIO.IN)

# File to write data
file_name = "gpio_log.txt"
today = datetime.date.today()

try:
    with open(file_name, "w") as file:
        while True:
            # Get current time
            current_time = time.time()
            ms_since_midnight = (time.time() - time.mktime(today.timetuple())) * 1000
            #current_time_ms = int((time.time() * 100000)) / 100
            
            # Read state of pin 23
            pin_state = GPIO.input(23)
            
            # Write to file
            file.write("{}, {}\n".format(ms_since_midnight, pin_state))
            
            # Flush to ensure data is written immediately
            file.flush()
            
            # Sleep for 0.001 seconds
            #time.sleep(0.001)

except KeyboardInterrupt:
    # Clean up GPIO on keyboard interruptgpio   
    GPIO.cleanup()

