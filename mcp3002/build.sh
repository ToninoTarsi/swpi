#! /bin/bash

gcc -c libMCP3002.c gb_common.c gb_spi.c 
gcc --shared -o libMCP3002.so libMCP3002.o gb_common.o gb_spi.o -lrt