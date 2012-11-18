###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

import os
import threading, Queue
import select
import subprocess
import time
import config
from TTLib import *



class WvDialProcess:

    INFO_NETIF = 0
    INFO_LIPADDR = 1
    INFO_RIPADDR = 2
    INFO_PDNSADDR = 3
    INFO_SDNSADDR = 4
    INFO_CONNTIME = 5
    ST_INTERFACE_MSG = 0
    ST_INTERFACE_CONN = 1
    ST_INTERFACE_HANG = 2
    ST_INTERFACE_PASSREQ = 3

    def __init__(self, wvd_cfg, wvd_cmd="wvdial", wvd_eargs="", send_to_interface_callback=None):
        self.cmd = wvd_cmd + ' -C ' + wvd_cfg
        if ( wvd_eargs != None ):
            self.cmd = self.cmd + ' ' + wvd_eargs
        self.sti_callback = send_to_interface_callback
        self.pid = None
        #self.wvdial_pr = None
        self.info = { WvDialProcess.INFO_NETIF:None, WvDialProcess.INFO_LIPADDR:None, WvDialProcess.INFO_RIPADDR:None,
                                    WvDialProcess.INFO_PDNSADDR:None, WvDialProcess.INFO_SDNSADDR:None, WvDialProcess.INFO_CONNTIME:None }
        self.queue = Queue.Queue()
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.execute)

    def start(self):
        self.thread.start()
        # wait for pid information from pipe thread
        self.pid = self.queue.get(True, None)

    def stop(self):
        #self.wvdial_pr.kill()
        #return
#        print "PID",self.pid
        os.kill(self.pid, 2)
        self.thread.join(5.0)
        if ( self.thread.isAlive() ):
            # if it's still alive after five seconds, sigterm it
            os.kill(self.pid, 15)
            self.thread.join(5.0)
            if ( self.thread.isAlive() ):
                # oh well... last resort
                os.kill(self.pid, 9)

    def send_to_interface(self, code, data):
        pass
        #self.sti_callback(data, code)

    def send_password(self, passwd):
        self.queue.put(passwd)

    def set_info(self, name, value):
        self.lock.acquire()
        self.info[name] = value
        self.lock.release()

    def get_info(self, name):
        self.lock.acquire()
        value = self.info[name]
        self.lock.release()
        return value

    def execute(self):
        wvdial_pr = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
        #self.wvdial_pr = wvdial_pr
        self.queue.put(wvdial_pr.pid+1) # put pid information in queue, so that main thread can pick it and proceed
        rfiles = [wvdial_pr.stdout]
        while rfiles:
            sources = select.select(rfiles, [], [], 1000)[0]
            for source in sources:
                data = source.readline()
                if data:
                    self.execute_parse_data(data, wvdial_pr)
                    self.send_to_interface(WvDialProcess.ST_INTERFACE_MSG, data)
                else: # eof
                    rfiles.remove(wvdial_pr.stdout)
        self.send_to_interface(WvDialProcess.ST_INTERFACE_HANG, '')


    def execute_parse_data(self, data, process):
        if ( data.find('Using interface ', 4, 20) != -1 ):
            self.set_info(WvDialProcess.INFO_NETIF, data[20:].strip('\n\r '))
        elif ( data.find('local    IP address', 4, 21) != -1 ):
            self.set_info(WvDialProcess.INFO_LIPADDR, data[21:].strip('\n\r '))
            self.set_info(WvDialProcess.INFO_CONNTIME, time.time())
            # use this message to "detect" successful connection
            self.send_to_interface(WvDialProcess.ST_INTERFACE_CONN, '')
        elif ( data.find('remote IP address', 4, 21) != -1 ):
            self.set_info(WvDialProcess.INFO_RIPADDR, data[21:].strip('\n\r '))
        elif ( data.find('primary     DNS address', 4, 25) != -1 ):
            self.set_info(WvDialProcess.INFO_PDNSADDR, data[25:].strip('\n\r '))
        elif ( data.find('secondary DNS address', 4, 25) != -1 ):
            self.set_info(WvDialProcess.INFO_SDNSADDR, data[25:].strip('\n\r '))
        elif ( data.find('Please enter password', 4, 25) != -1 ):
            # send a password request to be displayed by the interface
            self.send_to_interface(WvDialProcess.ST_INTERFACE_PASSREQ, '')
            # and wait for the reply in the queue from main thread
            passwd = self.queue.get(True, None)
            # once password has been submitted, send it to wvdial
            process.stdin.write(passwd + '\n')
            process.stdin.flush()
            passwd = ''


    def waitForIP(self):
        # wait maximum 2 minute for a valid IP
        log("Waiting for a valid IP ...")
        n = 60
        for i in range(1,n):
            theIP = self.info[2]
            if ( theIP != None):
                return theIP
            log("No IP yet. Retrying ..%d" % (n-i) )
            time.sleep(2)
        return None


if __name__ == '__main__':
 
    configfile = 'swpi.cfg'
    
    if not os.path.isfile(configfile):
        "Configuration file not found"
        exit(1)    
    cfg = config.config(configfile)
  
    print "connecting"
    wvd_prc = WvDialProcess("wind.conf")
    wvd_prc.start()
   
    IP = wvd_prc.waitForIP()
    print "IP",IP
    
    time.sleep(20)
    


    print "Disconnecting"
    
    wvd_prc.stop()
    
    print "info=" , wvd_prc.info

    
    
 

    print "Done"
