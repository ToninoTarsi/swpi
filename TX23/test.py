from ctypes import *

libTX23 = cdll.LoadLibrary('./libTX23.so')


iDir = c_int()
iSpeed = c_int()

print libTX23.getData(byref(iDir), byref(iSpeed),1)

print "DIR" , iDir
print "Speed",iSpeed

