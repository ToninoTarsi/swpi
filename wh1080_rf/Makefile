CC=gcc
CFLAGS=-c -Wall -std=gnu99

all: wh1080_rf spi_init

wh1080_rf: wh1080_rf.o rf_bcm2835.o bmp085.o
	$(CC) -lm  wh1080_rf.o rf_bcm2835.o bmp085.o -lbcm2835 -o wh1080_rf

spi_init: spi_init.o
	$(CC) -lm  spi_init.o -lbcm2835 -o spi_init


wh1080_rf.o: wh1080_rf.c
	$(CC) $(CFLAGS) wh1080_rf.c

rf_bcm2835.o: rf_bcm2835.c
	$(CC) $(CFLAGS) rf_bcm2835.c

bmp085.o: bmp085.c
	$(CC) $(CFLAGS) bmp085.c

spi_init.o: spi_init.c
	$(CC) $(CFLAGS) spi_init.c

clean:
	rm -f wh1080_rf.o bcm2835.o bmp085.o wh1080_rf spi_init.o spi_init

	
