/*
  * pcf8563_i2c_rtc.c - example of accessing a PCF8563 via the BSC0 (I2C) peripheral on a BCM2835 (Raspberry Pi)
  * 
  * Copyright 2012 Kevin Sangeelee.
  * Released as GPLv2, see <http://www.gnu.org/licenses/>
  *
  * This is intended as an example of using Raspberry Pi hardware registers to drive an RTC chip. Use at your own risk or
  * not at all. As far as possible, I've omitted anything that doesn't relate to the RTC or the Raspi registers. There are more
  * conventional ways of doing this using kernel drivers, though these are harder to follow.
  */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdint.h>
#include <time.h>
#include <math.h>
#include <fcntl.h>
#include <sys/mman.h>
#include "bcm2835.h"


////////////////
//  main()
////////////////

char eeprom[22] = { 0, 0, };
short ac1, ac2, ac3, b1, b2, mb, mc, md;
unsigned short ac4, ac5, ac6;

float temperature_deg_c;
float pressure_hpa;

int read_bmp085(float altitude) {

	if(map_peripheral(&gpio) == -1) {
		printf("Failed to map the physical GPIO registers into the virtual memory space.\n");
		return -1;
	}
	if(map_peripheral(&bsc0) == -1) {
		printf("Failed to map the physical BSC0 (I2C) registers into the virtual memory space.\n");
		return -1;
	}
	
	/* BSC0 is on GPIO 0 & 1 */
	*gpio.addr &= ~0x3f; // Mask out bits 0-5 of FSEL0 (i.e. force to zero)
	*gpio.addr |= 0x24;  // Set bits 0-5 of FSEL0 to binary '100100'
	
	// Read eeprom data if the array is empty
	// I2C Device Address 0x77 (hardwired into the chip, 0xEE & 0xEF)
	if((unsigned short)*eeprom == 0) {
	
		// Device 0x77, register 0xaa, read into buf, 22 bytes
		i2c_read(0x77, 0xaa, eeprom, 22);

		ac1 = (short)eeprom[0] << 8 | eeprom[1];
		ac2 = (short)eeprom[2] << 8 | eeprom[3];
		ac3 = (short)eeprom[4] << 8 | eeprom[5];
		ac4 = (unsigned short)eeprom[6] << 8 | eeprom[7];
		ac5 = (unsigned short)eeprom[8] << 8 | eeprom[9];
		ac6 = (unsigned short)eeprom[10] << 8 | eeprom[11];
		b1 = (short)eeprom[12] << 8 | eeprom[13];
		b2 = (short)eeprom[14] << 8 | eeprom[15];
		mb = (short)eeprom[16] << 8 | eeprom[17];
		mc = (short)eeprom[18] << 8 | eeprom[19];
		md = (short)eeprom[20] << 8 | eeprom[21];
		
		// Test values
		//ac1 = 408, ac2 = -72, ac3 = -14383, ac4 = 32741, ac5 = 32757, ac6 = 23153;
		//b1 = 6190, b2 = 4, mb = -32768, mc = -8711, md = 2868;
		// Also include 'ut = 27898' , 'up = 23843', and 'oss = 0'
		//printf("%d %d %d %d %d %d\n", ac1, ac2, ac3, ac4, ac5, ac6);
		//printf("%d %d %d %d %d\n", b1, b2, mb, mc, md);
	}
	
	
	char ut_buf[2];
	char up_buf[2];
		
	char cmd_ut = 0x2e;
	char cmd_up[] = {0x34, 0x74, 0xb4, 0xf4};
	int oss_delay[] = {4500, 7500, 13500, 25500};
	int oss = 1; // This is an index into the above array
	
	/*
	 * Get Uncompensated Temperature from BMP085
	 */
	i2c_write(0x77, 0xf4, &cmd_ut, 1);
	usleep(4500); // just wait the maximum possible time for conversion
	i2c_read(0x77, 0xf6, ut_buf, 2);
	
	long ut = (long)ut_buf[0] << 8 | ut_buf[1]; 
	
	// Temperature compensation algorithm (derived from datasheet)
	long x1 = ((ut - ac6) * ac5) >> 15;
	long x2 = (mc * (1 << 11)) / (x1 + md);
	long b5 = x1 + x2;
	long t = (b5 + 8)  >> 4;
	
	temperature_deg_c = (float)t / 10;
	printf("Temperature: %0.1fC\n", temperature_deg_c);
	
	int idx;
	float p0 = 0;
	
	for(idx=0; idx < 2; idx++) {
		/*
		 * Get Uncompensated Pressure from BMP085, based on the OverSampling Setting
		 * of (0, 1, 2, or 3). This determines accuracy, conversion delay, and power consumption.
		 */
		i2c_write(0x77, 0xf4, &cmd_up[oss], 1);
		usleep(oss_delay[oss]); // wait according to the chosen oss mode
		i2c_read(0x77, 0xf6, up_buf, 3);

		long up = (((long)up_buf[0] << 16) | ((long)up_buf[1] << 8) | up_buf[2]) >> (8 - oss);
		
		// Pressure compensation algorithm (derived from datasheet)
		long b6 = b5 - 4000;
		x1 = (b2 * (b6 * b6 >> 12)) >> 11;
		x2 = ac2 * b6 >> 11;
		long x3 = x1 + x2;
		long b3 = (((ac1 * 4 + x3) << oss) + 2) >> 2;
		x1 = ac3 * b6 >> 13;
		x2 = (b1 * (b6 * b6 >> 12)) >> 16;
		x3 = ((x1 + x2) + 2) >> 2;
		unsigned long b4 = ac4 * (unsigned long)(x3 + 32768) >>15;
		unsigned long b7 = ((unsigned long)up - b3) * (50000 >> oss);
		long p = b7 < 0x80000000 ? (b7 * 2) / b4 : (b7 / b4) * 2;
		x1 = (p >> 8) * (p >> 8);
		x1 = (x1 * 3038) >> 16;
		x2 = (-7357 * p) >> 16;
		p = p + (x1 + x2 + 3791) / 16;
		
		p0 += (float)p / powf(1.0f - (altitude / 44330), 5.255f);
		
		usleep(100000);
	}
	p0 /= 2;
	pressure_hpa = p0 / 100;
	printf("Pressure p0 (sea level): %0.1f hPa\n", pressure_hpa);
	
	unmap_peripheral(&gpio);
	unmap_peripheral(&bsc0);
	
	return 0;
}
