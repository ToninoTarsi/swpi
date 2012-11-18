#! /bin/bash

gcc -o readTX23 bcm2835.c RPi_TX23.c readTX23.c -lrt

gcc -c  bcm2835.c RPi_TX23.c  libTX23.c
gcc --shared -o libTX23.so bcm2835.o RPi_TX23.o libTX23.o -lrt