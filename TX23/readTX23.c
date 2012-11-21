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




void printWindSpeedAndDirection(void)
{
	
	// Local variables
	char thetime[32];
	int WindDirection = 0;
	int WindSpeed = 0;
	
		
	// Set up the TX23 Pins
	RPi_TX23_InitPins();

	//Read from the TX23
	if (RPi_TX23_GetReading(&WindDirection,&WindSpeed)==TRUE)
	{
		RPi_TX23_GetDateTimeLocal(thetime);
		printf("(%d , %d )", WindDirection, WindSpeed);
//		printf("%s,Wind Direction,%0.1f\n",thetime,((double)WindDirection)*22.5);
//		printf("%s,Wind Speed,%d\n",thetime,WindSpeed);

	}
	else
	{
		exit(1);
	}
}



int main (int argc, char *argv[])
{
	//Check for debugging flags
	int i;
	int debugMode = 0;
	for (i = 1; i < argc ; i++)
	{
		if ((strcmp(argv[i],"--debug") == 0) || (strcmp(argv[i],"-d") == 0))
			debugMode = 1;
		else if ((strcmp(argv[i],"--verbose") == 0) || (strcmp(argv[i],"-v") == 0))
			Rpi_TX23_Option_Verbose = 1;
		else if ((strcmp(argv[i],"--help") == 0) || (strcmp(argv[i],"-?") == 0))
		{
			printf("Usage: readTX23 [OPTION]\nRead data from a La Crosse TX23U Anemometer.\n");
			printf("\t-v, --verbose\t\tGive detailed error messages\n");
			printf("\t-d, --debug\t\tShow times and pin state changes only\n");
			printf("\t-?, --help\t\tShow usage information\n\n");
			exit(0);
		}
	}
	
	//Initialise the Raspberry Pi GPIO
	if(!bcm2835_init())
		exit(1);

	//Print a result
	if (debugMode)
		RPi_TX23_debug();
	else	
		printWindSpeedAndDirection();

	return 0;
}
