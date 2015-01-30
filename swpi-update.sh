#! /bin/bash

echo $1
if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
	theurl="http://www.vololiberomontecucco.it/swpi/swpi-src.tar.gz"
	thefile="swpi-src.tar.gz"
else
    echo "arguments supplied"
	theurl="http://www.vololiberomontecucco.it/swpi/swpi_"
	theurl+=$1
	theurl+=.tar.gz
	thefile="swpi_"
	thefile+=$1
	thefile+=.tar.gz
fi


echo $theurl




test=`awk '$4~/(^|,)ro($|,)/' /proc/mounts | grep /dev/root`
if [ -z "$test" ]
then 
	ro=0
else
	ro=1
	echo "Mounting in rw"
    sudo mount / -o remount,rw
fi





sudo mount / -o remount,rw
cd /home/pi/swpi

sudo chown -R  pi  /home/pi/swpi 
sudo chown  pi ./DHT
sudo chown  pi ./mcp3002
sudo chown  pi ./TX23
sudo chown  pi ./wh1080_rf

cd /home/pi/
wget $theurl
tar -xvf $thefile
rm $thefile
cd swpi

echo "Changing permissions"

sudo chmod +x ./usbreset
sudo chmod +x ./wifi_reset.sh
sudo chmod +x ./swpi.sh
sudo chmod +x ./swpi-update.sh
sudo chmod +x ./killswpi.sh
sudo chmod +x ./restore.sh
sudo chmod +x ./backup.sh
sudo chmod +x ./DHT/DHT
sudo chmod +x ./DHT/DHT_rf
sudo chmod +x ./wh1080_rf/wh1080_rf
sudo chmod +x ./wh1080_rf/spi_init
sudo chmod +x ./mcp3002/atod
sudo chmod +x ./mcp3002/libMCP3002.so
sudo chmod 755 ./swpi.py



if [ $ro = 1 ] ; then 
	echo "Mounting in ro"
	sudo mount / -o remount,ro
fi
