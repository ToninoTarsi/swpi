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
    conn = sqlite3.connect('db/swpi.s3db',200)    
    dbCursor = conn.cursor()
    dbCursor.execute("SELECT * FROM METEO where datetime(TIMESTAMP_LOCAL) > datetime('now','-1 day') order by rowid asc limit 1")
    data = dbCursor.fetchall()
    print "rain_rate_24h" , data
    if ( len(data) == 1):
        therain = (data[0][9])    
        rain_rate_24h = therain
        print  rain_rate_24h
    else : print " nodara"
    dbCursor.execute("SELECT * FROM METEO where datetime(TIMESTAMP_LOCAL) > datetime('now','-1 hour') order by rowid asc limit 1")
    data = dbCursor.fetchall()
    print "rain_rate_1h" ,  data
    if ( len(data) == 1):
        therain = (data[0][9])    
        rain_rate_1h = therain  
        print  rain_rate_1h
    else : print " nodara" 
    if conn:        
        conn.close()
    
    
    