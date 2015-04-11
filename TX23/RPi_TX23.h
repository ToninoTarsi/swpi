/*
Raspberry Pi La Crosse TX23 communication library.
By:      John Burns (www.john.geek.nz)
Date:    14 August 2012
License: CC BY-SA v3.0 - http://creativecommons.org/licenses/by-sa/3.0/
*/

#ifndef RPI_TX23_H_
#define	RPI_TX23_H_

extern int Rpi_TX23_Option_Verbose;

// Includes
#include "bcm2835.h"
#include <time.h>
#include <sys/time.h>
#include <stdio.h>
#include <stdlib.h>

// Defines
#define	TRUE	1
#define	FALSE	0

#define TX23_DELAY_MicroSeconds 10
#define TX23_TIMEOUT_COMMS_LOOP 10000 //Timeout is this times Delay_MicroSeconds

// Define the Raspberry Pi GPIO Pins for the TX23
#define RPI_GPIO_TX23_DATA RPI_GPIO_P1_15

/* Macros to toggle port state of DATA line. */
#define TX23_DATA_SET_OUTPUT_LOW	bcm2835_gpio_write(RPI_GPIO_TX23_DATA, LOW);\
					bcm2835_gpio_fsel(RPI_GPIO_TX23_DATA, BCM2835_GPIO_FSEL_OUTP)
#define	TX23_DATA_SET_INPUT 		bcm2835_gpio_fsel(RPI_GPIO_TX23_DATA, BCM2835_GPIO_FSEL_INPT);\
					bcm2835_gpio_set_pud(RPI_GPIO_TX23_DATA, BCM2835_GPIO_PUD_OFF)
#define TX23_DATA_GET_BIT		bcm2835_gpio_lev(RPI_GPIO_TX23_DATA)

// Delay Macro
#define TX23_DoDelay	gettimeofday(&delayEnd,NULL);while(((unsigned int)((delayEnd.tv_sec-delayStart.tv_sec)*1000000ULL+(delayEnd.tv_usec-delayStart.tv_usec)))<delayTargetuSec){gettimeofday(&delayEnd,NULL);}

extern const char TX23_Directions[16][4];

/* Public Functions ----------------------------------------------------------- */
void RPi_TX23_InitPins( void );
unsigned char RPi_TX23_GetReading(int *iDir, int *iSpeed );
void RPi_TX23_debug ( void );
void RPi_TX23_GetDateTimeUTC( char * sTime );
void RPi_TX23_GetDateTimeLocal( char *sTime );
#endif

