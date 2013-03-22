/*
* Maplin N96GY (Fine Offset WH1080/WH1081) RF receiver using a
* Raspberry Pi and an RFM01 or RFM12b transceiver module. I switched
* to an RFM01 module after frying the RFM12b; turns out it works *far*
* better anyway, so it was something of a blessing in disguise.
* 
* The code here is really just experimental, and is not intended to be used
* beyond a learning excercise. It conveys the basics of what's required
* to get the Raspberry Pi receiving sensor data, but that's about it!
*
* I can't be sure it still works with an RFM12b, but it shouldn't be far off
* the mark if not - a bit of debugging may be required, but I no longer
* have a working module to test.
*
* This program configures an RFM01 to receive RF transmissions from the
* weather station's sensors, and reads them directly from the receiver's
* demodulator via the DATA pin, in to a GPIO pin on the Raspberry Pi. The
* pulse widths are used to derive the data-packet that was transmitted.
*
* The process switches to SCHED_RR for realtime latency while it waits
* for a packet. It returns to SCHED_OTHER when a packet is received.
* This ensures that bit transitions aren't missed, and also allows very
* heavy loads to run on the Pi while maintaining reliable reads. Optionally,
* the command 'sysctl kernel.sched_wakeup_granularity_ns=100000' may
* further improve latency, though it seems to work with Raspbian defaults
* regardless.
*
* Includes Luc Small's version of CRC8 from the OneWire Arduino library
* adapted for Fine Offset's calculations that also happen to work for this
* weather station. The SPI code was derived from the driver example at 
* kernel.org.
*
* This program is free software; you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation as version 2 of the License.
*
*/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <unistd.h>
#include <stdint.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>
#include <time.h>
#include <sched.h>

#include "wh1080_rf.h"
#include "bcm2835.h"
#include "rfm01.h"

uint16_t bw_scale[6] = {BW_67, BW_134, BW_200, BW_270, BW_340, BW_400};

struct RSSI rssi_scale[24] = {
	L0R73,L0R79,L0R85,L0R91,L0R97,L0R103,
	L6R73,L6R79,L6R85,L6R91,L6R97,L6R103,
	L14R73,L14R79,L14R85,L14R91,L14R97,L14R103,
	L20R73,L20R79,L20R85,L20R91,L20R97,L20R103,
};

uint8_t _crc8( uint8_t *addr, uint8_t len);

static void pabort(const char *s)
{
	perror(s);
	abort();
}

static const char *device = "/dev/spidev0.0";
static uint8_t mode=0;
static uint8_t bits = 8;
static uint32_t speed = 1000000;
static uint16_t delay=0;


static uint16_t send_command16(int fd, uint16_t cmd)
{
	uint8_t tx[2];
	uint8_t *buf = (uint8_t *)&cmd;
	tx[0] = buf[1];
	tx[1] = buf[0];

	//printf("SPI %02x%02x\n", buf[1], buf[0]);

	uint8_t rx[2] = {0, 0};
	struct spi_ioc_transfer tr = {
		.tx_buf = (unsigned long)tx,
		.rx_buf = (unsigned long)rx,
		.len = 2,
		.delay_usecs = delay,
		.speed_hz = speed,
		.bits_per_word = bits,
	};

	if(ioctl(fd, SPI_IOC_MESSAGE(1), &tr) < 1)
		pabort("can't send spi message");
	
	return (((uint16_t)rx[0]) << 8) + rx[1];
}

int g_low_threshold = 1000;

uint16_t cmd_reset	= CMD_RESET;
uint16_t cmd_status = CMD_STATUS;

// Expected bit rate: 95 = 1959, 99 = 1700, 9c = 1500, a1 = 1268, aa = 1000, b8 - 756, d5 = 500
uint16_t cmd_drate = CMD_DRATE|0xaa;	// drate is c8xx rather than c6xx
// uint16_t cmd_freq	= CMD_FREQ|0x620; // 433.92 MHz
uint16_t cmd_freq = CMD_FREQ|0x67c; // 868.3 MHz Tony

#ifdef RFM01
	uint16_t cmd_afc	= CMD_AFC|AFC_ON|AFC_OUT_ON|AFC_MANUAL|AFC_FINE|AFC_RL_7;
	uint16_t cmd_dcycle = CMD_LOWDUTY|0x00;
	uint16_t cmd_fifo	= CMD_FIFO|0x00;

	//uint16_t cmd_config	= CMD_CONFIG|BAND_433|LOAD_CAP_12C0|BW_67;

	// Enviroment
	uint16_t cmd_config = CMD_CONFIG|BAND_868|LOAD_CAP_12C0|BW_67; // Tony
	uint16_t cmd_rcon = (CMD_RCON|RX_EN|VDI_DRSSI|LNA_0|RSSI_97);
	

	uint16_t cmd_dfilter = (CMD_DFILTER|CR_LOCK_FAST|FILTER_OOK);
#endif

#ifdef RFM12B
	uint16_t cmd_config	= 0x8017;
	uint16_t cmd_power	= 0x8281; // RFM01 doesn't support this
	uint16_t cmd_sync	= 0xce55;
	uint16_t cmd_afc	= 0xc407; // or C400 for no AFC. C6xx on RFM01
	uint16_t cmd_dcycle = 0xc800;
	uint16_t cmd_pll	= 0xcc1f;
	uint16_t cmd_fifo	= 0xca8a; // CExx rather than CAxx on RFM01

	uint16_t cmd_dfilter = 0xc260;
	uint16_t cmd_rcon = (CMD_RCON|P16|VDI_MEDIUM|LNA_MEDIUM|RSSI_97|BW_340);
#endif

void strobe_afc(int fd) {

	send_command16(fd, cmd_afc|AFC_STROBE); // Strobe high
	send_command16(fd, cmd_afc & (~AFC_ON)); // Strobe low, disable AFC processing
	uint16_t status = send_command16(fd, cmd_status);
	// get offs bits and extend two's complement to a byte
	int8_t offset = (status & STATUS_OFFS) | (status & STATUS_OFFSIGN ? 0xe0 : 0);
	
	float freq_offs = (float)offset;
	#ifdef RFM12B
		freq_offs *= 2.5;
	#endif
	send_command16(fd, cmd_afc); // Strobe low, re-enable AFC

	printf("Frequency deviation %0.1fKHz (%d)\n", freq_offs, (int)offset);

	send_command16(fd, cmd_rcon);
}

/*
 * Sample the DRSSI flag at 'interval' microsecond intervals over a period of 'duration' ms,
  *and return the average.
*/

float sample_rssi(int fd, int duration, int interval) {

	unsigned int start_time, now;
	unsigned int loop_count = 0, rssi_total = 0;

	start_time = TIMER_ARM_COUNT;

	do {
		uint16_t status = send_command16(fd, cmd_status);
		int rssi = (status & STATUS_RSSI) ? 1 : 0;
		loop_count++;
		rssi_total+=rssi;
		now = TIMER_ARM_COUNT;
		usleep(interval);	// microseconds
	} while(now - start_time < (duration * 1000));	// duration as microseconds

	float duty = ((float)rssi_total/loop_count) * 100;

	return duty;
}

extern int read_bmp085(float altitude);

int main(int argc, char *argv[])
{
	//unsigned char bytes2[] = {0xa1,0x82,0x0a,0x59,0x03,0x06,0x00,0x4e,0x06,0xc8};
	//calculate_values(bytes2);
	//return -1;
	
	uint8_t packet_sig = 0xfa;

	if(map_peripheral(&gpio) == -1 || map_peripheral(&timer_arm) == -1) {
		printf("Failed to map the GPIO or TIMER registers into the virtual memory space.\n");
		return -1;
	}

	// 0xF90200; // run at 1MHz
	TIMER_ARM_CONTROL = TIMER_ARM_C_DISABLE|TIMER_ARM_C_FREE_EN
							|TIMER_ARM_C_16BIT|TIMER_ARM_C_PS1
							|TIMER_ARM_C_FPS(0xf9);
	
	// Init GPIO21 (on pin 13) as input (DATA), GPIO22 (pin 15) as output (nRES)
	//*(gpio.addr + 2) = (*(gpio.addr + 2) & 0xfffffe07)|(0x001 << 6); Tony

	// RPi (Rev1) Init GPIO21 (on pin 13) as input (DATA), GPIO22 (pin 15) as output (nRES)
	//*(gpio.addr + 2) = (*(gpio.addr + 2) & 0xfffffe07)|(0x001 << 6);

	// RPi (Rev2) Init GPIO27 (on pin 13) as input (DATA)
	*(gpio.addr + 2) = (*(gpio.addr + 2) & 0xff1fffff)|(0x001 << 6)

	#ifdef RFM01
		printf("Initialising RFM01\n");
	#endif
	#ifdef RFM12B
		printf("Initialising RFM12b\n");
	#endif
	
	int fd;

	fd = open(device, O_RDWR);
	if (fd < 0)
		pabort("can't open device");

	// SPI mode
	if(ioctl(fd, SPI_IOC_WR_MODE, &mode) == -1)
		pabort("Can't set SPI mode");

	// Bits per word (driver only supports 8 -bits I think, but RFM12B handles this ok)
	if(ioctl(fd, SPI_IOC_WR_BITS_PER_WORD, &bits) == -1)
		pabort("Can't set bits per word");

	// SPI clock speed (Hz)
	if(ioctl(fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed) == -1)
		pabort("Can't set SPI clock speed");

	printf("SPI: mode %d, %d-bit, %d KHz\n", mode, bits, speed/1000);

	// LED on
	*(gpio.addr + (0x1c >> 2)) = 1 << 22;

	// Reset the module? Maybe use software reset if needed.
	//send_command(fd, cmd_fifo); // in case reset sensitivity is low
	//send_command(fd, cmd_reset);
	usleep(100000);

	// LED off
	*(gpio.addr + (0x28 >> 2)) = 1 << 22;

	send_command16(fd, cmd_status);
	send_command16(fd, cmd_config);
	send_command16(fd, cmd_freq);
	send_command16(fd, cmd_drate);
	send_command16(fd, cmd_rcon);
	send_command16(fd, cmd_dfilter);
	send_command16(fd, cmd_fifo);
	send_command16(fd, cmd_afc);
	send_command16(fd, cmd_dcycle);
	#ifdef RFM12B
		send_command16(fd, cmd_power);
		send_command16(fd, cmd_sync);
		send_command16(fd, cmd_pll);
	#endif

	printf("Ctrl+C to exit\n");
	usleep(5000);	// Allow crystal oscillator to start

	
	int idx1, idx2;
	for(idx1=0; idx1 < 24; idx1++) {

		uint16_t cmd_rcon_mod = (cmd_rcon & ~(RSSI_X2|LNA_XX)) | (rssi_scale[idx1].rssi_setth |rssi_scale[idx1].g_lna);

		printf("%15s idx %-2d  ", rssi_scale[idx1].name, idx1);
		
		for(idx2=0; idx2 < 6; idx2++) {
		
			uint16_t cmd_config_mod = (cmd_config & ~BW_X2) | bw_scale[idx2];

			send_command16(fd, cmd_config_mod);
			send_command16(fd, cmd_rcon_mod);
			usleep(1000);
		
			rssi_scale[idx1].duty[idx2] = sample_rssi(fd, 25, 100);
			
			if(cmd_rcon_mod == cmd_rcon && cmd_config_mod == cmd_config)
				printf("%6.2f< ", rssi_scale[idx1].duty[idx2]);
			else
				printf("%6.2f  ", rssi_scale[idx1].duty[idx2]);
			fflush(stdout);
		}
		printf("\n");
	}
	send_command16(fd, cmd_config);
	send_command16(fd, cmd_rcon);
	usleep(1000);


	// Show the average RSSI to indicate noise at startup. If args dictate
	// then repeat forever. Note that an unshielded Ethernet cable will
	// radiate noise, so include a delay to allow console output to be flushed.
	do {
		float duty = sample_rssi(fd, 250, 100);
		printf("RSSI Duty %0.2f\r", duty);
		fflush(stdout);
		usleep(250000);
	} while(argc > 1);

	printf("\n");

	uint16_t status;

	uint8_t rssi = 0, oldrssi = 0;
	unsigned int shorts = 0;
	unsigned int rssitime, oldrssitime, now;
	int count = 0, timeout = 1;
	time_t last_valid = time(0);
	int crc_passed;

	unsigned int rssitime_buf[500];
	unsigned char bytes[10];

	oldrssitime = TIMER_ARM_COUNT;

	// Switch to realtime scheduler
	scheduler_realtime();
	do {

		// Read the GPIO pin for clocked DATA value
		//status = ((*(gpio.addr + 13)) >> 21) & 1;
		status = ((*(gpio.addr + 13)) >> 27) & 1; // Tony
		rssi = status;
		rssitime = TIMER_ARM_COUNT;
		// Check if the pin transitioned
		if(rssi != oldrssi) {
			// If falling edge (1 -> 0), then store bit pulse duration
			if(rssi == 0) {
				rssitime_buf[count] = rssitime - oldrssitime;
				if(++count == 500)
				count = 499;
			}
			oldrssi = rssi;
			oldrssitime = rssitime;
			timeout = 0;
		}
		// Check time since last transition. If timeout, then dump packet.
		int packet_offset = 0;
		now = TIMER_ARM_COUNT;
		if(!timeout && (now - oldrssitime) > 5000) { // && count > 0

			uint8_t sig_matched = 0;
		
			if(count > 60) { // then maybe something at least interesting
				// Look for device_id
				int idx;
				uint8_t bit, sig_in = 0;
				for(idx=0; idx < count; idx++) {
					bit = rssitime_buf[idx] < g_low_threshold ? 1 : 0;
					sig_in = (sig_in << 1) | bit;

					if((sig_matched = (sig_in == packet_sig))) {
						packet_offset = idx - 3;
						break;
					}
				}
				printf("\rData bits = %d   (offset %d) (%d short) %s\n",
					count, packet_offset, shorts, sig_matched ? "Packet signature found" : "No packet signature found");
				if(count == 88 && sig_matched) { // then probably a data packet

					// LED on
					*(gpio.addr + (0x1c >> 2)) = 1 << 22;

					strobe_afc(fd); // lock frequency to good signal

					int b;
					uint8_t byte;
					for(idx=0; idx < 10; idx++) {
						byte = 0;
						for(b=0; b < 8; b++) {
							// Short pulses 1, long pulses 0
							uint8_t bit = rssitime_buf[packet_offset + (idx * 8 + b)] < g_low_threshold ? 1 : 0;
							byte = (byte << 1) + bit;
						}
						bytes[idx] = byte;
						printf("%02x ", byte);
					}
					crc_passed = bytes[9] == _crc8(bytes, 9);
					printf("crc %s (gap %ds)\n", crc_passed ? "ok" : "fail", (int)(time(0) - last_valid));
					last_valid = time(0);
					fflush(stdout);
				}
			} else {
				if(shorts++ % 10 == 0) {
					printf(".");
					fflush(stdout);
				}
			}
			timeout = 1;

			// If we get enough bits, then dump stats to indicate pulse lengths coming from the device.
			if(count > 40) {
				// These are slightly confusing - lo used to mean low side of threshold, but printf below reports them as binary
				// 0 and 1. So the meanings are opposite - to be fixed.
				unsigned int idx, min_lo=999999, min_hi=999999, max_lo = 0, max_hi = 0;
				unsigned int val;
				for(idx = 0; idx < count; idx++) {
					// printf("RSSI 1 -> 0  %3d: %4dus ( %s )\n", idx, rssitime_buf[idx],
					//	rssitime_buf[idx] >= LOW_THRESHOLD ? "Hi" : "Lo");
					val = rssitime_buf[idx];
					
					// Short pulses are binary '1', long pulses are binary '0'
					if(val < g_low_threshold) {
						if(val < min_lo)
						min_lo = val;
						if(val > max_lo)
						max_lo = val;
					} else {
						if(val < min_hi)
						min_hi = val;
						if(val > max_hi)
						max_hi = val;
					}
				}

				printf("Pulse stats: Hi: %u - %u   Lo: %u - %u  (%d point)\n", min_lo, max_lo, min_hi, max_hi, count);

				// Recalculate the pulse threshold if we got a perfect read.
				if(count == 88 && crc_passed) {
					//g_low_threshold = ( ((max_lo + min_lo) / 2) + ((max_hi + min_hi) / 2)) / 2;
					g_low_threshold =(max_lo + min_hi) / 2;
					printf("Threshold now %d\n", g_low_threshold);
					
					// Note the time of the last reading...
					unsigned int wait_start = TIMER_ARM_COUNT, elapsed;

					// at this point, we can do other stuff that requires the RT scheduler
					
					#ifdef USE_BMP085
					read_bmp085(ALTITUDE_M);	// read pressure, calculate for the given altitude
					#endif
					
					calculate_values(bytes);
					
					// Wait for remainder of 47 seconds in standard scheduler until we can expect the next read
					scheduler_standard();

					do {
						elapsed = (TIMER_ARM_COUNT - wait_start) / 1000000;
						printf("Wait %us \r", 47 - elapsed);
						fflush(stdout);
						usleep(250000);
					} while(elapsed < 47);
					printf("Listening for transmission\n");
					scheduler_realtime();
				}
			}
			count = 0;


			// LED off
			*(gpio.addr + (0x28 >> 2)) = 1 << 22;
		}
		usleep(5); // No point running with nanosecond loops when pulses are in the hundreds of microseconds...
		
	} while(1); // Ctrl+C to exit for now...


	// Currenty unreachable
	close(fd);
	
	unmap_peripheral(&gpio);
	unmap_peripheral(&timer_arm);
	
	return 0;
}

char *direction_name[] = {"N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"};

void calculate_values(unsigned char *buf) {
	
	unsigned short device_id = ((unsigned short)buf[0] << 4) | (buf[1] >> 4);
	unsigned short temperature_raw = (((unsigned short)buf[1] & 0x0f) << 8) | buf[2];
	float temperature = ((float)temperature_raw - 400) / 10;
	int humidity = buf[3];
	
	unsigned short wind_avg_raw = (unsigned short)buf[4];
	float wind_avg_ms = roundf((float)wind_avg_raw * 34.0f) / 100;
	float wind_avg_mph = wind_avg_ms * 2.23693629f;

	unsigned short wind_gust_raw = (unsigned short)buf[5];
	float wind_gust_ms = roundf((float)wind_gust_raw * 34.0f) / 100;
	float wind_gust_mph = wind_gust_ms * 2.23693629f;
	
	unsigned short rain_raw = (((unsigned short)buf[6] & 0x0f) << 8) | buf[7];
	
	float rain = (float)rain_raw * 0.3f;
	
	int direction = buf[8] & 0x0f;
	
	char *direction_str = direction_name[direction];
	
	printf("Station Id: %04X\n", device_id);
	printf("Temperature: %0.1fC, Humidity: %d%%\n", temperature, humidity);
	printf("Wind speed: %0.2f m/s, Gust Speed %0.2f m/s, %s\n", wind_avg_ms, wind_gust_ms, direction_str);
	printf("Wind speed: %0.1f mph, Gust Speed %0.1f mph, %s\n", wind_avg_mph, wind_gust_mph, direction_str);
	printf("Total rain: %0.1f mm\n", rain);
}

/*
* Function taken from Luc Small (http://lucsmall.com), itself
* derived from the OneWire Arduino library. Modifications to
* the polynomial according to Fine Offset's CRC8 calulations.
*/
uint8_t _crc8( uint8_t *addr, uint8_t len)
{
	uint8_t crc = 0;

	// Indicated changes are from reference CRC-8 function in OneWire library
	while (len--) {
		uint8_t inbyte = *addr++;
		uint8_t i;
		for (i = 8; i; i--) {
			uint8_t mix = (crc ^ inbyte) & 0x80; // changed from & 0x01
			crc <<= 1; // changed from right shift
			if (mix) crc ^= 0x31;// changed from 0x8C;
			inbyte <<= 1; // changed from right shift
		}
	}
	return crc;
}

void scheduler_realtime() {

	struct sched_param p;
	
	p.__sched_priority = sched_get_priority_max(SCHED_RR);
	
	if( sched_setscheduler( 0, SCHED_RR, &p ) == -1 ) {
		perror("Failed to switch to realtime scheduler.");
	}
}

void scheduler_standard() {

	struct sched_param p;
	
	p.__sched_priority = 0;
	
	if( sched_setscheduler( 0, SCHED_OTHER, &p ) == -1 ) {
		perror("Failed to switch to normal scheduler.");
	}
}
