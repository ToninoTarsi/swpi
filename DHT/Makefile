all : DHT libDHT.so

clean :
	rm *.o DHT 

DHT : DHT.o
	gcc -o DHT  DHT.o -lrt -L/usr/local/lib -lwiringPi

libDHT.so : libDHT.o 
	gcc --shared -o libDHT.so libDHT.o  -lrt -L/usr/local/lib -lwiringPi

# The next lines generate the various object files

libDHT.o : libDHT.c  
	gcc -c libDHT.c  -std=gnu99  



DHT.o : DHT.c
	gcc -c -Wall DHT.c -std=gnu99


