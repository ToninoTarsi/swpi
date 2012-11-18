#define PAGESIZE 4096
#define BLOCK_SIZE 4096

#define IOBASE   0x20000000

#define GPIO_BASE		(IOBASE + 0x200000)
#define BSC0_BASE		(IOBASE + 0x205000)
#define TIMER_ARM_BASE	(IOBASE + 0x00B000)


/*
 * Defines for ARM Timer peripheral
 */
#define TIMER_ARM_LOAD		*(timer_arm.addr + 0x100)
#define TIMER_ARM_VALUE		*(timer_arm.addr + 0x101)
#define TIMER_ARM_CONTROL	*(timer_arm.addr + 0x102)
#define TIMER_ARM_IRQ_CLEAR	*(timer_arm.addr + 0x103)
#define TIMER_ARM_IRQ_RAW	*(timer_arm.addr + 0x104)
#define TIMER_ARM_IRQ_MASK	*(timer_arm.addr + 0x105)
#define TIMER_ARM_RELOAD	*(timer_arm.addr + 0x106)
#define TIMER_ARM_PREDIVIDE	*(timer_arm.addr + 0x107)
#define TIMER_ARM_COUNT		*(timer_arm.addr + 0x108)

// Zero-shifts are here for code readability, where a zero-bit holds significant
// meaning other than just a negated state, or where the negated state is notable.

#define TIMER_ARM_C_16BIT		(0 << 1)
#define TIMER_ARM_C_23BIT		(1 << 1)
#define TIMER_ARM_C_PS1			(0 << 2)
#define TIMER_ARM_C_PS16		(1 << 2)
#define TIMER_ARM_C_PS256		(2 << 2)
#define TIMER_ARM_C_PS1_1		(3 << 2)
#define TIMER_ARM_C_INTEN		(1 << 5)
#define TIMER_ARM_C_DISABLE		(0 << 7)
#define TIMER_ARM_C_ENABLE		(1 << 7)
#define TIMER_ARM_C_DBGHALT		(1 << 8)
#define TIMER_ARM_C_FREE_EN		(1 << 9)
#define TIMER_ARM_C_FPS(n)		((n & 0xff) << 16)
#define TIMER_ARM_C_FPS_MASK	(0xff << 16)


/*
 * Defines for I2C peripheral (aka BSC, or Broadcom Serial Controller)
 */
#define BSC0_C		*(bsc0.addr + 0x00)
#define BSC0_S		*(bsc0.addr + 0x01)
#define BSC0_DLEN	*(bsc0.addr + 0x02)
#define BSC0_A		*(bsc0.addr + 0x03)
#define BSC0_FIFO	*(bsc0.addr + 0x04)

#define BSC_C_I2CEN	(1 << 15)
#define BSC_C_INTR	(1 << 10)
#define BSC_C_INTT	(1 << 9)
#define BSC_C_INTD	(1 << 8)
#define BSC_C_ST	(1 << 7)
#define BSC_C_CLEAR	(1 << 4)
#define BSC_C_READ	1

#define START_READ	BSC_C_I2CEN|BSC_C_ST|BSC_C_CLEAR|BSC_C_READ
#define START_WRITE	BSC_C_I2CEN|BSC_C_ST

#define BSC_S_CLKT	(1 << 9)
#define BSC_S_ERR	(1 << 8)
#define BSC_S_RXF	(1 << 7)
#define BSC_S_TXE	(1 << 6)
#define BSC_S_RXD	(1 << 5)
#define BSC_S_TXD	(1 << 4)
#define BSC_S_RXR	(1 << 3)
#define BSC_S_TXW	(1 << 2)
#define BSC_S_DONE	(1 << 1)
#define BSC_S_TA	1

#define CLEAR_STATUS	BSC_S_CLKT|BSC_S_ERR|BSC_S_DONE



struct bcm2835_peripheral {
	unsigned long addr_p;	// Physical address
	unsigned long init_count;
	int mem_fd;		// File Descriptor for /dev/mem
	void *map;		// The mmap() 
	volatile unsigned int *addr;
};

extern struct bcm2835_peripheral gpio;
extern struct bcm2835_peripheral bsc0;
extern struct bcm2835_peripheral timer_arm;

extern void wait_i2c_done();
extern void i2c_read(char dev_addr, char reg_addr, char *buf, unsigned short len);
extern void i2c_write(char dev_addr, char reg_addr, char *buf, unsigned short len);
extern void dump_bsc_status();

extern int map_peripheral(struct bcm2835_peripheral *p);
extern void unmap_peripheral(struct bcm2835_peripheral *p);

