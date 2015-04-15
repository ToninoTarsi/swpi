#include <wiringPi.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#define MAX_TIME 85
#define DHT11PIN 1
#define MAXTRY  100


int dht11_val[5]={0,0,0,0,0};



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
	*temp = dht11_val[2]+dht11_val[3]/10.;
	*hum = dht11_val[0]+dht11_val[1]/10.;
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


