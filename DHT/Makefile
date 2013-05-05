all : DHT libDHT.so DHT_rf

clean :
	rm *.o DHT 

DHT : DHT.o
	gcc -o DHT  DHT.o -lrt -L/usr/local/lib -lwiringPi

libDHT.so : libDHT.o 
	gcc --shared -o libDHT.so libDHT.o  -lrt -L/usr/local/lib -lwiringPi

DHT_rf: DHT_rf.o
	gcc -o DHT_rf DHT_rf.o -std=gnu99 -I. -lbcm2835

# The next lines generate the various object files

libDHT.o : libDHT.c  
	gcc -c libDHT.c  -std=gnu99  

DHT.o : DHT.c
	gcc -c -Wall DHT.c -std=gnu99


DHT_rf.o : DHT_rf.c
	gcc -c -Wall DHT_rf.c -std=gnu99 -I. -lbcm2835


