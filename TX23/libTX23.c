// Compile with: gcc -o readTX23 ./bcm2835-1.8/src/bcm2835.c ./RPi_TX23.c readTX23.c

/*
Sensor:
La Crosse TX23 Anemometer interfaced to Raspberry Pi GPIO port

TX23 Wires:
	Brown	TXDATA - Connected to GPIO Port P1-15 (GPIO 22)
	Brown	TXDATA - Connected via a 10k pullup resistor to GPIO Port P1-01 (3V3 Power)
	Red	Vcc - Connected to GPIO Port P1-01 (3V3 Power)
	Green - Not Connected
	Yellow	GND  - Connected to GPIO Port P1-06 (Ground)

	
	GPIO Pins can be changed in the Defines of RPi_SHT1x.h
*/

#include "bcm2835.h"
#include <stdio.h>
#include <time.h>
#include "RPi_TX23.h"

int init()
{
	Rpi_TX23_Option_Verbose = 0;
	if(bcm2835_init())
		return 1;
	else
		return 0;
}


int getData(int *iDir, int *iSpeed,int verbose)
{
	Rpi_TX23_Option_Verbose = verbose;

	if (RPi_TX23_GetReading(iDir,iSpeed)==TRUE)
	{
		return 1;
	}
	return 0;

}


