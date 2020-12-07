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
#include <string.h>
#include <getopt.h>
#include <libgen.h>
#include <unistd.h>
#include <stdbool.h>

char *myname;
bool json_format = false;

bool
printWindSpeedAndDirection(void)
{
	
	// Local variables
	char thetime[32];
	int WindDirection = 0;
	int WindSpeed = 0;
	char *p;
	double mph;
		
	// Set up the TX23 Pins
	RPi_TX23_InitPins();

	if (json_format) {
	  RPi_TX23_GetDateTimeUTC(thetime);
	  p = strchr(thetime, 'T');
	  if (p)
	    *p = ' ';
	  p = strrchr(thetime, 'Z');
	  if (p)
	    *p = '\0';
	  mph = (double)WindSpeed / 10 * 3600 / 1609.344; 
	  printf("{\"time\" : \"%s\", \"model\" : \"TX23U\", \"wind_avg_mi_h\" : %f, \"wind_dir_deg\" : %.1f, \"mic\" : \"CRC\"}\n",
		 thetime,
		 mph,
		 (double)WindDirection*22.5);
	} else {
	  //Read from the TX23
	  if (RPi_TX23_GetReading(&WindDirection, &WindSpeed) == TRUE) {
	      RPi_TX23_GetDateTimeLocal(thetime);
	      printf("(%d , %d )", WindDirection, WindSpeed);
//		printf("%s,Wind Direction,%0.1f\n",thetime,((double)WindDirection)*22.5);
//		printf("%s,Wind Speed,%d\n",thetime,WindSpeed);
	}
	else
	  return false;

	fflush(stdout);
	return true;
}

void
repeat_read(int count, int interval)
{
  int i;

  if (count <= 0) {
    for (;;) {
      printWindSpeedAndDirection();
      sleep(interval);
    }
  } else {
    for (i = 0; i++ < count; ) {
      printWindSpeedAndDirection();
      sleep(interval);
    }
  }
}

void
usage()
{
  printf("Usage: %s [OPTION]\nRead data from a La Crosse TX23U Anemometer.\n", myname);
  printf("  -c --count count: How many times to read.\n");
  printf("  -i --interval sec: read every sec seconds.\n");
  printf("  -j --json: report in json format.\n");
  printf("  -v --verbose: Give detailed error messages\n");
  printf("  -d --debug: Show times and pin state changes only\n");
  printf("  -?|h --help: Show usage information\n");
  exit(0);
}

int main (int argc, char *argv[])
{
  int c;
  int iteration_count = 1;
  int interval = 1; /* 1 sec */
	int i;
	int debugMode = 0;

  myname = basename(argv[0]);

  for (;;) {
    int option_index = 0;
    static struct option long_options[] = {
      {"count",   required_argument, 0,  'c'},
      {"interval", required_argument, 0,  'i'},
      {"json",    no_argument, 0,  'j'},
      {"debug",   no_argument, 0,  'd'},
      {"verbose", no_argument, 0,  'v'},
      {"help",    no_argument, 0,  'h'},
      {0,         0,                 0,  0 }
    };

    c = getopt_long(argc, argv, "c:i:jdvh",
		    long_options, &option_index);
    if (c == -1)
      break;

    switch (c) {
    case 'c':
      iteration_count = atoi(optarg);
      break;
    case 'i':
      interval = atoi(optarg);
      break;
    case 'j':
      json_format = true;
      break;
    case 'v':
      Rpi_TX23_Option_Verbose = 1;
      break;
    case 'd':
      debugMode = 1;
      break;
    case 'h':
    case '?':
    default:
      usage();
      break;
    }
  }

	//Initialise the Raspberry Pi GPIO
	if(!bcm2835_init())
		exit(1);

	//Print a result
	if (debugMode)
		RPi_TX23_debug();
	else	
	  repeat_read(iteration_count, interval);

	return 0;
}
