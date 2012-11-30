###########################################################################
#     Sint Wind PI
#       Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

all : atod libMCP3002.so

clean :
	rm *.o atod libMCP3002.so

atod : gb_common.o gb_spi.o atod.o
	gcc -o atod gb_common.o gb_spi.o atod.o

libMCP3002.so : gb_common.o gb_spi.o atod.o libMCP3002.o
	gcc --shared -o libMCP3002.so libMCP3002.o gb_common.o gb_spi.o -lrt

# The next lines generate the various object files

libMCP3002.o : libMCP3002.c gb_common.c gb_common.h gb_spi.h
	gcc -c libMCP3002.c
     
gb_common.o : gb_common.c gb_common.h
	gcc -c gb_common.c

gb_spi.o : gb_spi.c gb_common.h gb_spi.h
	gcc -c gb_spi.c

atod.o : atod.c gb_common.h gb_spi.h
	gcc -c atod.c
