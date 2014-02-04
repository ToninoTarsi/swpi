#!/bin/bash


test=`awk '$4~/(^|,)ro($|,)/' /proc/mounts | grep /dev/root`
if [ -z "$test" ]
then 
	ro=0
else
	ro=1
	echo "Mounting in rw"
    sudo mount / -o remount,rw
fi


cd /home/pi/swpi

sudo mount / -o remount,rw
rm /restore/swpi.tar.z

tar cvfz /restore/swpi.tar.z *

cp /home/pi/swpi/restore.sh /restore

sudo mount / -o remount,ro
echo "System backupd"





