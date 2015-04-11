###########################################################################
#     Sint Wind PI
#       Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

all : readTX23 libTX23.so

clean :
	rm *.o readTX23 libTX23.so

readTX23 : bcm2835.o RPi_TX23.o readTX23.o
	gcc -o readTX23 bcm2835.o RPi_TX23.o readTX23.o -lrt

libTX23.so : libTX23.o bcm2835.o RPi_TX23.o 
	gcc --shared -o libTX23.so libTX23.o bcm2835.o RPi_TX23.o  -lrt

# The next lines generate the various object files

libTX23.o : libTX23.c  RPi_TX23.c RPi_TX23.h bcm2835.h bcm2835.c
	gcc -c libTX23.c
     
bcm2835.o : bcm2835.h bcm2835.c
	gcc -c bcm2835.c

RPi_TX23.o : RPi_TX23.c RPi_TX23.h bcm2835.h bcm2835.c
	gcc -c RPi_TX23.c

readTX23.o : readTX23.c RPi_TX23.h bcm2835.h bcm2835.c
	gcc -c readTX23.c
