#!/bin/bash


cd /home/pi/swpi

sudo mount / -o remount,rw
rm /restore/swpi.tar.z

tar cvfz /restore/swpi.tar.z *

cp /home/pi/swpi/restore.sh /restore

echo "System backupd"





