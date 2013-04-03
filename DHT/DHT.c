#include <wiringPi.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#define MAX_TIME 85
#define DHT11PIN 1
#define MAXTRY  100
//#include <unistd.h>

int dht11_val[5]={0,0,0,0,0};

int type=11;

int dht11_read_val(float *temp, float *hum)
{
  uint8_t lststate=HIGH;
  uint8_t counter=0;
  uint8_t j=0,i;
  float farenheit;
  for(i=0;i<5;i++)
     dht11_val[i]=0;
  pinMode(DHT11PIN,OUTPUT);
  digitalWrite(DHT11PIN,LOW);
  delay(18);
  digitalWrite(DHT11PIN,HIGH);
  delayMicroseconds(40);
  pinMode(DHT11PIN,INPUT);
  for(i=0;i<MAX_TIME;i++)
  {
    counter=0;
    while(digitalRead(DHT11PIN)==lststate){
      counter++;
      delayMicroseconds(1);
      if(counter==255)
        break;
    }
    lststate=digitalRead(DHT11PIN);
    if(counter==255)
       break;
    // top 3 transistions are ignored
    if((i>=4)&&(i%2==0)){
      dht11_val[j/8]<<=1;
      if(counter>16)
        dht11_val[j/8]|=1;
      j++;
    }
  }
  // verify cheksum and print the verified data
  if((j>=40)&&(dht11_val[4]==((dht11_val[0]+dht11_val[1]+dht11_val[2]+dht11_val[3])& 0xFF)))
  {
	  if ( type == 11)
	  {
		  *temp = dht11_val[2]+dht11_val[3]/10.;
		  *hum = dht11_val[0]+dht11_val[1]/10.;
	  }
	  else
	  {
		  float f, h;
		  h = dht11_val[0] * 256 + dht11_val[1];
		  h /= 10;

		  f = (dht11_val[2] & 0x7F)* 256 + dht11_val[3];
		  f /= 10.0;
		  if (dht11_val[2] & 0x80)
			  f *= -1;
		  *temp = f;
		  *hum = h;
		  //printf("Temp =  %.1f *C, Hum = %.1f \%\n", f, h);
	  }
    //printf("Humidity = %d.%d %% Temperature = %d.%d *C (%.1f *F)\n",dht11_val[0],dht11_val[1],dht11_val[2],dht11_val[3],farenheit);
    return 0;
  }
  else
    //printf("Invalid Data!!\n");
    //printf("Data (%d): 0x%x 0x%x 0x%x 0x%x 0x%x\n", j, dht11_val[0], dht11_val[1], dht11_val[2], dht11_val[3], dht11_val[4]);
    return 1;

}

int read(float *temp, float *hum)
{
	int i;
	for ( i=0;i<MAXTRY;i++ )
	{
		if (dht11_read_val(temp, hum) == 0)
		{
			//printf("%d\n",i);
			return 0;
		}
		delay(50);
	}
	return 1;
}

int main(int argc, char *argv[])
{

	if ( argc > 1 )
		type = 22;

	float temp,hum;
	if ( type == 11)
		printf("Interfacing Temperature and Humidity Sensor (DHT11) With Raspberry Pi\n");
	else
		printf("Interfacing Temperature and Humidity Sensor (DHT22) With Raspberry Pi\n");

	if(wiringPiSetup()==-1)
		exit(1);

	 if ( read(&temp,&hum) == 0 )
	 {
		 printf("Temp =  %.1f *C, Hum = %.1f \%\n", temp, hum);
		 return 0;
	 }
	 else
	 {
		 printf("Invalid Data!!\n");
	 }

	return 1;
}
