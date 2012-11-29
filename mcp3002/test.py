from ctypes import *
import time

libMCP = cdll.LoadLibrary('./libMCP3002.so')



while 1:
    print "ch 0",libMCP.read_channel(0)
    print "ch 1",libMCP.read_channel(1)
    time.sleep(1)