#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <sys/mman.h>

#include "bcm2835.h"

struct bcm2835_peripheral gpio = {GPIO_BASE, 0};
struct bcm2835_peripheral bsc0 = {BSC0_BASE, 0};
struct bcm2835_peripheral timer_arm = {TIMER_ARM_BASE, 0};

// Exposes the physical address defined in the passed structure using mmap on /dev/mem
int map_peripheral(struct bcm2835_peripheral *p)
{
	if(p->init_count > 0) {
		p->init_count++;
		return 0;
	}

	// Open /dev/mem 
	if ((p->mem_fd = open("/dev/mem", O_RDWR|O_SYNC) ) < 0) {
		printf("Failed to open /dev/mem, try checking permissions.\n");
		return -1;
	}

	p->map = mmap(
	NULL,
	BLOCK_SIZE,
	PROT_READ|PROT_WRITE,
	MAP_SHARED,
	p->mem_fd,  // File descriptor to physical memory virtual file '/dev/mem'
	p->addr_p	  // Address in physical map that we want this memory block to expose
	);

	if (p->map == MAP_FAILED) {
		perror("mmap");
		return -1;
	}

	p->addr = (volatile unsigned int *)p->map;
	p->init_count++;

	return 0;
}


void unmap_peripheral(struct bcm2835_peripheral *p) {

	p->init_count--;
	if(p->init_count == 0) {
		munmap(p->map, BLOCK_SIZE);
		close(p->mem_fd);
	}
}

// Function to wait for the I2C transaction to complete
void wait_i2c_done() {

		while((!((BSC0_S) & BSC_S_DONE))) {
			usleep(100);
		}
}

// Function to write data to an I2C device via the FIFO.  This doesn't refill the FIFO, so writes are limited to 16 bytes
// including the register address. len specifies the number of bytes in the buffer.
void i2c_write(char dev_addr, char reg_addr, char *buf, unsigned short len) {

		int idx;
		
		BSC0_A = dev_addr;
		BSC0_DLEN = len + 1;	// one byte for the register address, plus the buffer length
		
		BSC0_FIFO = reg_addr;	// start register address
		for(idx=0; idx < len; idx++)
			BSC0_FIFO = buf[idx];
			
		BSC0_S = CLEAR_STATUS; // Reset status bits (see #define)
		BSC0_C = START_WRITE;	// Start Write (see #define)

		wait_i2c_done();
		
}

// Function to read a number of bytes into a  buffer from the FIFO of the I2C controller
void i2c_read(char dev_addr, char reg_addr, char *buf, unsigned short len) {

		i2c_write(dev_addr, reg_addr, NULL, 0);
		
		unsigned short bufidx = 0;

		memset(buf, 0, len); // clear the buffer

		BSC0_DLEN = len;
		BSC0_S = CLEAR_STATUS; // Reset status bits (see #define)
		BSC0_C = START_READ;	// Start Read after clearing FIFO (see #define)

		do {
			// Wait for some data to appear in the FIFO
			while((BSC0_S & BSC_S_TA) && !(BSC0_S & BSC_S_RXD));

			// Consume the FIFO
			while((BSC0_S & BSC_S_RXD) && (bufidx < len)) {
				buf[bufidx++] = BSC0_FIFO;
			}
		} while((!(BSC0_S & BSC_S_DONE)));
}

void dump_bsc_status() {
	
	unsigned int s = BSC0_S;
	
	printf("BSC0_S: ERR=%d  RXF=%d  TXE=%d  RXD=%d  TXD=%d  RXR=%d  TXW=%d  DONE=%d  TA=%d\n",
		(s & BSC_S_ERR) != 0, 
		(s & BSC_S_RXF) != 0, 
		(s & BSC_S_TXE) != 0, 
		(s & BSC_S_RXD) != 0, 
		(s & BSC_S_TXD) != 0, 
		(s & BSC_S_RXR) != 0, 
		(s & BSC_S_TXW) != 0, 
		(s & BSC_S_DONE) != 0, 
		(s & BSC_S_TA) != 0 );
}
