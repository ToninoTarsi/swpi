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

cd /restore


tar -C /swpi -xvf /restore/swpi.tar.z


echo "System restored"

sudo mount / -o remount,ro
