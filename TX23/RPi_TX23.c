/*
Raspberry Pi La Crosse TX23 communication library.
By:      John Burns (www.john.geek.nz)
Date:    14 August 2012
License: CC BY-SA v3.0 - http://creativecommons.org/licenses/by-sa/3.0/
*/

#include "RPi_TX23.h"

const char TX23_Directions[16][4] = {{"N"}, {"NNE"}, {"NE"}, {"ENE"}, {"E"}, {"ESE"}, {"SE"}, {"SSE"}, {"S"}, {"SSW"}, {"SW"}, {"WSW"}, {"W"}, {"WNW"}, {"NW"}, {"NNW"}};

int Rpi_TX23_Option_Verbose = 0;

void RPi_TX23_InitPins( void ) 
{
	// Set the DATA pin to input
	TX23_DATA_SET_INPUT;
}

// Returns Date and time in Local Time Zone
void RPi_TX23_GetDateTimeLocal(char *sTime)
{
	// Returns the current date and time in ISO 8601 format
	time_t now = time(NULL);
	strftime(sTime, 32, "%Y-%m-%dT%H:%M:%S%z", localtime(&now));
	//sprintf (sTime,"%04d-%02d-%02dT%02d:%02d:%02dZ", now_utc->tm_year + 1900, now_utc->tm_mon+1, now_utc->tm_mday, now_utc->tm_hour, now_utc->tm_min, now_utc->tm_sec);
 
}

void RPi_TX23_GetDateTimeUTC(char *sTime)
{
	// Returns the current date and time in UTC
	time_t now;
	struct tm * now_utc;
	time ( &now );
	now_utc = gmtime ( &now );
	
	sprintf (sTime,"%04d-%02d-%02dT%02d:%02d:%02dZ", now_utc->tm_year + 1900, now_utc->tm_mon+1, now_utc->tm_mday, now_utc->tm_hour, now_utc->tm_min, now_utc->tm_sec);
 
  }

void RPi_TX23_debug ( void )
{
	unsigned int timeout = 2000000;
	/*This function will pull the data line low, then measure the number
	of microseconds to every state change of the data pin.
	It is an infinite loop.
	*/
	
	struct timeval start, stop;
	unsigned int pinstate = 0;

	//Pull the DATA Pin low for 100ms to signal TX23 to send data
	TX23_DATA_SET_OUTPUT_LOW;
	delay(500);
	gettimeofday(&start,NULL);
	TX23_DATA_SET_INPUT;
	while (1)
		{
		timeout--;
		if ( TX23_DATA_GET_BIT != pinstate )
			{
			gettimeofday(&stop,NULL);
			pinstate ^= 1;
			printf("%duS,%d\n",(int)((stop.tv_sec-start.tv_sec)*1000000ULL+(stop.tv_usec-start.tv_usec)),pinstate);
			}
		if (!timeout)
			break;
		}
}

//unsigned char TX23_GetReading( void )
unsigned char RPi_TX23_GetReading(int *iDir, int *iSpeed )
{
	
	unsigned int timeout;			// Timeout for reading the port
	struct timeval start, stop;		// Used to calculate the baud rate
	unsigned int bitLength;	// The length of each bit in uSec

	// Local Variables
	int startframe = 6;	//Start with binary 110
	int winddir = 0;
	int winddir2 = 0;
	int windspeed = 0;
	int windspeed2 = 0;
	int checksum = 0;
	int iCounter = 0;

	// Variables to store delay info
	struct timeval delayStart, delayEnd;
	unsigned int delayTargetuSec = 0;

	//Pull the DATA Pin low for 500ms to signal TX23 to send data
	TX23_DATA_SET_OUTPUT_LOW;
	gettimeofday(&delayStart,NULL);
	delayTargetuSec = 500000;
	TX23_DoDelay;

	//Release the DATA Pin
	TX23_DATA_SET_INPUT;
	
	// Wait 5ms for data pin to stabilise
	gettimeofday(&delayStart,NULL);
	delayTargetuSec = 10000;
	TX23_DoDelay;
	
	// Data pin will still be low
	// We are now expecting 11011 as the first five bits from TX23
	// We calculate the baud rate from the length of the first three bits (110)

	// Input should be low right now
	if ( TX23_DATA_GET_BIT != 0 ) 
	{
		if(Rpi_TX23_Option_Verbose)
			printf("Error 1 : Invalid pin state\n");
		return FALSE;
	}

	// Wait for input to go high
	timeout = 6 * TX23_TIMEOUT_COMMS_LOOP;	//Should take less than this many loops
	while ( TX23_DATA_GET_BIT == 0 ) {
		timeout --;
		if (timeout==0)
		{
			if(Rpi_TX23_Option_Verbose)
				printf("Error 2 : Timed out waiting for rising edge \n");
			return FALSE;
		}
	}



	// Start the timers
	gettimeofday(&start,NULL);

	// Wait for input to go low
	timeout = TX23_TIMEOUT_COMMS_LOOP;	//Should take less than this many loops
	while ( TX23_DATA_GET_BIT == 1 ) {
		timeout --;
		if (timeout==0)
		{
			if(Rpi_TX23_Option_Verbose)
				printf("Error 3 : Timed out waiting for falling edge \n");
			return FALSE;
		}
	}

	// Wait for input to go high again
	timeout = TX23_TIMEOUT_COMMS_LOOP;	//Should take less than this many loops
	while ( TX23_DATA_GET_BIT == 0 ) {
		timeout --;
		if (timeout==0)
		{
			if(Rpi_TX23_Option_Verbose)
				printf("Error 4 : Timed out waiting for rising edge \n");
			return FALSE;
		}
	}

	// Stop the timer 
	gettimeofday(&stop,NULL);
	
	//Restart the serial delay timer
	gettimeofday(&delayStart,NULL);
	delayTargetuSec = 0;

	bitLength = (int)((stop.tv_usec-start.tv_usec)/3);
	bitLength += 5;
	// Wait for a little bit to make sure we're getting the stable values
	delayTargetuSec += (bitLength/2);TX23_DoDelay;
	
	//Get the rest of the start frame
	for (iCounter=0;iCounter<2;iCounter++)
	{
		startframe = ((startframe<<1) | TX23_DATA_GET_BIT);
		delayTargetuSec += bitLength;
		TX23_DoDelay;
	}

	// Wind Direction	
	for (iCounter=0;iCounter<4;iCounter++)
	{
		winddir |= (TX23_DATA_GET_BIT << iCounter);
		delayTargetuSec += bitLength;
		TX23_DoDelay;
	}

	// Wind Speed
	for (iCounter=0;iCounter<12;iCounter++)
	{
		windspeed |= (TX23_DATA_GET_BIT << iCounter);
		delayTargetuSec += bitLength;
		TX23_DoDelay;
	}

	// Checksum
	for (iCounter=0;iCounter<4;iCounter++)
	{
		checksum |= (TX23_DATA_GET_BIT << iCounter);
		delayTargetuSec += bitLength;
		TX23_DoDelay;
	}
	
	// Wind Direction 2
	for (iCounter=0;iCounter<4;iCounter++)
	{
		winddir2 |= ((TX23_DATA_GET_BIT ^ 1) << iCounter);
		delayTargetuSec += bitLength;
		TX23_DoDelay;
	}


	// Wind Speed 2
	for (iCounter=0;iCounter<12;iCounter++)
	{
		windspeed2 |= ((TX23_DATA_GET_BIT ^ 1) << iCounter);
		delayTargetuSec += bitLength;
		TX23_DoDelay;
	}

	//Calculate Checksum
	unsigned int checksumCalc = 0;
	checksumCalc += (winddir & 15);
	checksumCalc += ((windspeed >> 8) & 15);
	checksumCalc += ((windspeed >> 4) & 15);
	checksumCalc += (windspeed & 15);

	//Decide on the result to return
	unsigned char isValidData = TRUE;
	if (startframe != 27) isValidData = FALSE;
	if (checksum != checksumCalc) isValidData = FALSE;
	if (winddir != winddir2) isValidData = FALSE;
	if (windspeed != windspeed2) isValidData = FALSE;

	if(Rpi_TX23_Option_Verbose)
	{
		printf("--------------------\n");
		printf("Bit Length: %d uSec\n", bitLength);
		printf("Start frame: %d\n", startframe);
		printf("Wind Direction: %s (%d)\n", TX23_Directions[winddir], winddir);
		printf("Wind Direction2: %s (%d)\n", TX23_Directions[winddir2], winddir2);
		printf("Wind Speed: %d\n", windspeed);
		printf("Wind Speed2: %d\n", windspeed2);
		printf("Checksum (received): %d\n", checksum);
		printf("Checksum (calculated): %d\n", checksumCalc);
		printf("Data is ");
		if (isValidData == FALSE) printf("NOT ");
		printf("Valid!\n");
		printf("--------------------\n");
	}

	if (isValidData==TRUE)
		{
		*iDir = winddir;
		*iSpeed = windspeed;
		}

	return isValidData;
}
