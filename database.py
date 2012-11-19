###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

import serial
import time
import sys
import struct
import ConfigParser
import sqlite3

# Open database commection and cursor
def resetDB(filename='db/swpi.s3db',delete_all=False):
    conn = sqlite3.connect(filename,200)
    dbCursor = conn.cursor()
    
    if delete_all :
        dbCursor.execute("delete from SMS")
        dbCursor.execute("delete from CALL")
    dbCursor.execute("delete from METEO")
    conn.commit()
    print "DB Resetted "
    
if __name__ == '__main__':
    resetDB()
    
    
    