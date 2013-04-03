#! /bin/bash

cd /home/pi/swpi

sudo chown  pi ./DHT
sudo chown  pi ./mcp3002
sudo chown  pi ./TX23
sudo chown  pi ./wh1080_rf

cd /home/pi/
wget http://www.vololiberomontecucco.it/swpi/swpi-src.tar.gz
tar xvfz swpi-src.tar.gz
rm swpi-src.tar.gz
cd swpi

echo "Changing permissions"

sudo chmod +x ./usbreset
sudo chmod +x ./wifi_reset.sh
sudo chmod +x ./swpi.sh
sudo chmod +x ./swpi-update.sh
sudo chmod +x ./killswpi.sh
sudo chmod +x ./DHT/DHT
sudo chmod +x ./wh1080_rf/wh1080_rf
sudo chmod +x ./wh1080_rf/spi_init
sudo chmod +x ./mcp3002/atod
sudo chmod +x ./mcp3002/libMCP3002.so





