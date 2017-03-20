#!/bin/sh


sudo mount -o remount,rw / ; sudo mount -o remount,rw /boot ; 
rm -rf build;
mkdir build;
cd build;
cmake ../
make && make install
echo "\n\nPlease reboot system.\n"
