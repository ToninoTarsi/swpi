/*###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#
#     Please refer to the LICENSE file for conditions
#     Visit http://www.vololiberomontecucco.it
#
##########################################################################*/

#include "gb_common.h"

#define BCM2708_PERI_BASE        0x20000000
#define CLOCK_BASE               (BCM2708_PERI_BASE + 0x101000) /* Clocks */
#define GPIO_BASE                (BCM2708_PERI_BASE + 0x200000) /* GPIO   */
#define PWM_BASE                 (BCM2708_PERI_BASE + 0x20C000) /* PWM    */
#define SPI0_BASE                (BCM2708_PERI_BASE + 0x204000) /* SPI0 controller */
#define UART0_BASE               (BCM2708_PERI_BASE + 0x201000) /* Uart 0 */
#define UART1_BASE               (BCM2708_PERI_BASE + 0x215000) /* Uart 1 (not used) */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <dirent.h>
#include <fcntl.h>
#include <assert.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>

#include <unistd.h>

#define PAGE_SIZE (4*1024)
#define BLOCK_SIZE (4*1024)

int  mem_fd;
char *clk_mem_orig, *clk_mem, *clk_map;
char *gpio_mem_orig, *gpio_mem, *gpio_map;
char *pwm_mem_orig, *pwm_mem, *pwm_map;
char *spi0_mem_orig, *spi0_mem, *spi0_map;
char *uart_mem_orig, *uart_mem, *uart_map;

// I/O access
volatile unsigned *gpio;
volatile unsigned *pwm;
volatile unsigned *clk;
volatile unsigned *spi0;
volatile unsigned *uart;


//
//  GPIO
//

// GPIO setup macros. Always use INP_GPIO(x) before using OUT_GPIO(x) or SET_GPIO_ALT(x,y)
#define INP_GPIO(g) *(gpio+((g)/10)) &= ~(7<<(((g)%10)*3))
#define OUT_GPIO(g) *(gpio+((g)/10)) |=  (1<<(((g)%10)*3))
#define SET_GPIO_ALT(g,a) *(gpio+(((g)/10))) |= (((a)<=3?(a)+4:(a)==4?3:2)<<(((g)%10)*3))

#define GPIO_SET0   *(gpio+7)  // Set GPIO high bits 0-31
#define GPIO_SET1   *(gpio+8)  // Set GPIO high bits 32-53

#define GPIO_CLR0   *(gpio+10) // Set GPIO low bits 0-31
#define GPIO_CLR1   *(gpio+11) // Set GPIO low bits 32-53
#define GPIO_PULL   *(gpio+37) // Pull up/pull down
#define GPIO_PULLCLK0 *(gpio+38) // Pull up/pull down clock


//
//  UART 0
//

#define UART0_BAUD_HI *(uart+9)
#define UART0_BAUD_LO *(uart+10)


int setup_io();
void restore_io();

//
// This is a software loop to wait
// a short while.
//
void short_wait()
{ int w;
  for (w=0; w<100; w++)
  { w++;
    w--;
  }
} // short_wait


//
// Simple SW wait loop
//
void long_wait(int v)
{ int w;
  while (v--)
    for (w=-800000; w<800000; w++)
    { w++;
      w--;
    }
} // long_wait


//
// Set up memory regions to access the peripherals.
// This is a bit of 'magic' which you should not touch.
// It it also the part of the code which makes that
// you have to use 'sudo' to run this program.
//
int setup_io()
{  unsigned long extra;

   /* open /dev/mem */
   if ((mem_fd = open("/dev/mem", O_RDWR|O_SYNC) ) < 0) {
      printf("Can't open /dev/mem\n");
      printf("Did you forgot to use 'sudo .. ?'\n");
      return 0;
   }

   /*
    * mmap clock
    */
   if ((clk_mem_orig = malloc(BLOCK_SIZE + (PAGE_SIZE-1))) == NULL) {
      printf("allocation error \n");
      return 0;
   }
   extra = (unsigned long)clk_mem_orig % PAGE_SIZE;
   if (extra)
     clk_mem = clk_mem_orig + PAGE_SIZE - extra;
   else
     clk_mem = clk_mem_orig;

   clk_map = (unsigned char *)mmap(
      (caddr_t)clk_mem,
      BLOCK_SIZE,
      PROT_READ|PROT_WRITE,
      MAP_SHARED|MAP_FIXED,
      mem_fd,
      CLOCK_BASE
   );

   if ((long)clk_map < 0) {
      printf("clk mmap error %d\n", (int)clk_map);
      return 0;
   }
   clk = (volatile unsigned *)clk_map;


   /*
    * mmap GPIO
    */
   if ((gpio_mem_orig = malloc(BLOCK_SIZE + (PAGE_SIZE-1))) == NULL) {
      printf("allocation error \n");
      exit (-1);
   }
   extra = (unsigned long)gpio_mem_orig % PAGE_SIZE;
   if (extra)
     gpio_mem = gpio_mem_orig + PAGE_SIZE - extra;
   else
     gpio_mem = gpio_mem_orig;

   gpio_map = (unsigned char *)mmap(
      (caddr_t)gpio_mem,
      BLOCK_SIZE,
      PROT_READ|PROT_WRITE,
      MAP_SHARED|MAP_FIXED,
      mem_fd,
      GPIO_BASE
   );

   if ((long)gpio_map < 0) {
      printf("gpio mmap error %d\n", (int)gpio_map);
      return 0;
   }
   gpio = (volatile unsigned *)gpio_map;

   /*
    * mmap PWM
    */
   if ((pwm_mem_orig = malloc(BLOCK_SIZE + (PAGE_SIZE-1))) == NULL) {
      printf("allocation error \n");
      return 0;
   }
   extra = (unsigned long)pwm_mem_orig % PAGE_SIZE;
   if (extra)
     pwm_mem = pwm_mem_orig + PAGE_SIZE - extra;
   else
     pwm_mem = pwm_mem_orig;

   pwm_map = (unsigned char *)mmap(
      (caddr_t)pwm_mem,
      BLOCK_SIZE,
      PROT_READ|PROT_WRITE,
      MAP_SHARED|MAP_FIXED,
      mem_fd,
      PWM_BASE
   );

   if ((long)pwm_map < 0) {
      printf("pwm mmap error %d\n", (int)pwm_map);
      return 0;
   }
   pwm = (volatile unsigned *)pwm_map;

   /*
    * mmap SPI0
    */
   if ((spi0_mem_orig = malloc(BLOCK_SIZE + (PAGE_SIZE-1))) == NULL) {
      printf("allocation error \n");
      return 0;
   }
   extra = (unsigned long)spi0_mem_orig % PAGE_SIZE;
   if (extra)
     spi0_mem = spi0_mem_orig + PAGE_SIZE - extra;
   else
     spi0_mem = spi0_mem_orig;

   spi0_map = (unsigned char *)mmap(
      (caddr_t)spi0_mem,
      BLOCK_SIZE,
      PROT_READ|PROT_WRITE,
      MAP_SHARED|MAP_FIXED,
      mem_fd,
      SPI0_BASE
   );

   if ((long)spi0_map < 0) {
      printf("spi0 mmap error %d\n", (int)spi0_map);
      return 0;
   }
   spi0 = (volatile unsigned *)spi0_map;

   /*
    * mmap UART
    */
   if ((uart_mem_orig = malloc(BLOCK_SIZE + (PAGE_SIZE-1))) == NULL) {
      printf("allocation error \n");
      return 0;
   }
   extra = (unsigned long)uart_mem_orig % PAGE_SIZE;
   if (extra)
     uart_mem = uart_mem_orig + PAGE_SIZE - extra;
   else
     uart_mem = uart_mem_orig;

   uart_map = (unsigned char *)mmap(
      (caddr_t)uart_mem,
      BLOCK_SIZE,
      PROT_READ|PROT_WRITE,
      MAP_SHARED|MAP_FIXED,
      mem_fd,
      UART0_BASE
   );

   if ((long)uart_map < 0) {
      printf("uart mmap error %d\n", (int)uart_map);
      return 0;
   }
   uart = (volatile unsigned *)uart_map;
   return 1;

} // setup_io

//
// Undo what we did above
//
void restore_io()
{
  munmap(uart_map,BLOCK_SIZE);
  munmap(spi0_map,BLOCK_SIZE);
  munmap(pwm_map,BLOCK_SIZE);
  munmap(gpio_map,BLOCK_SIZE);
  munmap(clk_map,BLOCK_SIZE);
  // free memory
  free(uart_mem_orig);
  free(spi0_mem_orig);
  free(pwm_mem_orig);
  free(gpio_mem_orig);
  free(clk_mem_orig);
} // restore_io

// simple routine to convert the last several bits of an integer to a string 
// showing its binary value
// nbits is the number of bits in i to look at
// i is integer we want to show as a binary number
// we only look at the nbits least significant bits of i and we assume that 
// s is at least nbits+1 characters long
void make_binary_string(int nbits, int i, char *s)
{ char *p;
  int bit;

  p = s;
  for (bit = 1 << (nbits-1); bit > 0; bit = bit >> 1, p++)
    *p = (i & bit) ? '1' : '0';
  *p = '\0';
}
