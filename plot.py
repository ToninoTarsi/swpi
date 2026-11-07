
#!/usr/bin/env python
# -*- coding: ascii -*-

import RPi.GPIO as GPIO
import time
import sys

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------

PIN = 23
T = 30.0
OUTPUT_FILE = "pin23.txt"

# Read duration from command line
if len(sys.argv) > 1:
    try:
        T = float(sys.argv[1].replace(",", "."))
    except ValueError:
        print("Invalid parameter T")
        sys.exit(1)

if T <= 0:
    print("Duration T must be greater than zero")
    sys.exit(1)

# -------------------------------------------------
# GPIO INITIALIZATION
# -------------------------------------------------

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN)

print("Monitoring GPIO%d for %.2f seconds..." % (PIN, T))

samples = []

# -------------------------------------------------
# ACQUISITION
# -------------------------------------------------

start = time.time()

try:
    while True:
        elapsed = time.time() - start

        if elapsed >= T:
            break

        state = GPIO.input(PIN)
        samples.append((elapsed, state))

finally:
    GPIO.cleanup()

# -------------------------------------------------
# SAVE DATA
# -------------------------------------------------

with open(OUTPUT_FILE, "w") as f:

    f.write("Tempo (s)\tStato GPIO23\n")

    for elapsed, state in samples:
        tempo = ("%.6f" % elapsed).replace(".", ",")
        f.write("%s\t%d\n" % (tempo, state))

# -------------------------------------------------
# RESULTS
# -------------------------------------------------

print("Acquisition completed.")
print("Requested duration: %.2f seconds" % T)
print("Samples acquired: %d" % len(samples))
print("Average sampling frequency: %.1f Hz" % (len(samples) / T))
print("Output file: %s" % OUTPUT_FILE)
