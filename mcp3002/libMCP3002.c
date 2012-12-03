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

int init()
{
	if ( setup_io() == 0 )
	{
		return -1;
	}

	// activate SPI bus pins
	INP_GPIO(8);  SET_GPIO_ALT(8,0);
	INP_GPIO(9);  SET_GPIO_ALT(9,0);
	INP_GPIO(10); SET_GPIO_ALT(10,0);
	INP_GPIO(11); SET_GPIO_ALT(11,0);

	// Setup SPI bus
	setup_spi();

	return 0;

}

int read_channel(int chan)
{
	int v;

	// The value returned by the A to D can jump around quite a bit, so
	// simply printing out the value isn't very useful. The bar graph
	// is better because this hides the noise in the signal.

	v = read_adc(chan);


}
