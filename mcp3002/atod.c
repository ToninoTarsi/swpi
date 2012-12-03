/*###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#
#     Please refer to the LICENSE file for conditions
#     Visit http://www.vololiberomontecucco.it
#
##########################################################################*/

#include "gb_common.h"
#include "gb_spi.h"

// Set GPIO pins to the right mode
// DEMO GPIO mapping:
//         Function            Mode
// GPIO0=  unused
// GPIO1=  unused
// GPIO4=  unused
// GPIO7=  unused
// GPIO8=  SPI chip select A   Alt. 0
// GPIO9=  SPI MISO            Alt. 0
// GPIO10= SPI MOSI            Alt. 0
// GPIO11= SPI CLK             Alt. 0
// GPIO14= unused
// GPIO15= unused
// GPIO17= unused
// GPIO18= unused
// GPIO21= unused
// GPIO22= unused
// GPIO23= unused
// GPIO24= unused
// GPIO25= unused
//

// For A to D we only need the SPI bus and SPI chip select A
void setup_gpio()
{
   INP_GPIO(8);  SET_GPIO_ALT(8,0);
   INP_GPIO(9);  SET_GPIO_ALT(9,0);
   INP_GPIO(10); SET_GPIO_ALT(10,0);
   INP_GPIO(11); SET_GPIO_ALT(11,0);
} // setup_gpio


//
//  Read ADC input 0 and show as horizontal bar
//
void main(void)
{

  int r, v, s, i, chan;

  do {
	printf ("SK Pang Electronics\n");
    printf ("Which channel do you want to test? Type 0 or 1.\n");
    chan  = (int) getchar();
    (void) getchar(); // eat carriage return
  } while (chan != '0' && chan != '1');
  chan = chan - '0';

  printf ("These are the connections for the analogue to digital test:\n");
  printf ("jumper connecting GP11 to SCLK\n");
  printf ("jumper connecting GP10 to MOSI\n");
  printf ("jumper connecting GP9 to MISO\n");
  printf ("jumper connecting GP8 to CSnA\n");
  printf ("Potentiometer connections:\n");
  printf ("  (call 1 and 3 the ends of the resistor and 2 the wiper)\n");
  printf ("  connect 3 to 3V3\n");
  printf ("  connect 2 to AD%d\n", chan);
  printf ("  connect 1 to GND\n");
  printf ("When ready hit enter.\n");
  (void) getchar();

  // Map the I/O sections
  setup_io();

  // activate SPI bus pins
  setup_gpio();

  // Setup SPI bus
  setup_spi();

  // The value returned by the A to D can jump around quite a bit, so 
  // simply printing out the value isn't very useful. The bar graph
  // is better because this hides the noise in the signal.

  while (1)
  {
    v= read_adc(chan);
    // V should be in range 0-1023
    // map to 0-63
    s = v >> 4;
    printf("%04d ",v);
    // show horizontal bar
    for (i = 0; i < s; i++)
      putchar('#');
    for (i = 0; i < 64 - s; i++)
      putchar(' ');
    putchar(0x0D); // go to start of the line
    short_wait();
  } // repeated read

  printf("\n");
  restore_io();
} // main
