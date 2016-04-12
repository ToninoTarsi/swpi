#! /bin/bash

cd /home/pi/swpi
logfile=./log/log`date '+%d%m%Y'`.log
sudo python -u swpi.py | tee -a $logfile

