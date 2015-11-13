###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#     Modem comunications based on Slawek Ligus pyhumod-0.03 module
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

#

"""This module defines the base Modem() class."""

import serial
import threading
import Queue
import time
import os
import errors
import actions
import at_commands as atc
import signal
import config
import subprocess
from TTLib import *
import globalvars
import re


class Interpreter(threading.Thread):
    """Interpreter thread."""
    def __init__(self, modem, queue, patterns):
        self.active = True
        self.queue = queue
        self.patterns = patterns
        self.modem = modem
        threading.Thread.__init__(self)

    def run(self):
        """Keep interpreting messages while active attribute is set."""
        while self.active:
            self.interpret(self.queue.get())
            
    def stop(self):
        self.active = False

    def interpret(self, message):
        """Match message pattern with an action to take.

        Arguments:
            message -- string received from the modem.
        """
        #print "D- Interpreter :" +  message
        for pattern_action in self.patterns:
            pattern, action = pattern_action
            if pattern.search(message):
                action(self.modem, message)
                break
        else:
            actions.null_action(self.modem, message)


class QueueFeeder(threading.Thread):
    """Queue feeder thread."""
    def __init__(self, queue, ctrl_port, ctrl_lock):
        self.active = True
        self.queue = queue
        self.ctrl_port = ctrl_port
        self.ctrl_lock = ctrl_lock
        threading.Thread.__init__(self)

    def run(self):
        """Start the feeder thread."""
        while self.active:
            self.ctrl_lock.acquire()
            try:
                # set timeout
                input_line = self.ctrl_port.readline() 
                #print "Debug- QueueFeeder : " +  input_line
                self.queue.put(input_line)  
            except:
                log("Error in ctrl_port.readline")    
                systemRestart()
            finally:
                self.ctrl_lock.release()
                # Putting the thread on idle between releasing
                # and acquiring the lock for 100ms
                time.sleep(2)
                while (  globalvars.bAnswering):
                    #print "QueueFeeder sleep"
                    time.sleep(1)

    def stop(self):
        """Stop the queue feeder thread."""
        self.active = False
        self.ctrl_port.write('\r\n')

    def reset(self):
        try:
            self.ctrl_port.close()
            self.ctrl_port.open()
            self.ctrl_port.send_at("Z","",False) # Echo Disabled
            self.ctrl_port.send_at("E0","",False) # Echo Disabled
            self.ctrl_port.send_at("^CURC=0","",False) # disable periodic message
            self.ctrl_port.send_at("+CVHU=0","",False) # enable hang-up voice call 
            self.ctrl_port.send_at("H","",False)
            self.ctrl_port.send_at("+CMGF=1","",False)
            
        except:
            pass

class Prober(object):
    """Class responsible for reading in and queueing of control data."""

    def __init__(self, modem):
        self.queue = Queue.Queue()
        self._interpreter = None
        self._feeder = None
        self.modem = modem
        self.patterns = None

    def _stop_interpreter(self):
        """Stop the interpreter."""
        self._interpreter.active = False
        self._interpreter.queue.put('')

    def _start_interpreter(self):
        """Instanciate and start a new interpreter."""
        self._interpreter = Interpreter(self.modem, self.queue, self.patterns)
        self._interpreter.start()

    def start(self, patterns=None):
        """Start the prober.

        Starts two threads, an instance of QueueFeeder and Interpreter.
        """
        self.patterns = patterns
        if not patterns:
            self.patterns = actions.STANDARD_ACTIONS
        if self._feeder:
            raise errors.HumodUsageError('Prober already started.')
        else:
            self._feeder = QueueFeeder(self.queue, self.modem.ctrl_port, 
                                       self.modem.ctrl_lock)
            self._feeder.start()
            self._start_interpreter()

    def stop(self):
        """Stop the prober."""
        if self._feeder:
            self._stop_interpreter()
            self._feeder.stop()
            self._feeder = None
        else:
            raise errors.HumodUsageError('Prober not started.')


# pylint: disable-msg=R0904
# pylint: disable-msg=R0903
# pylint: disable-msg=R0902
# pylint: disable-msg=R0901
class ModemPort(serial.Serial):
    """Class extending serial.Serial by humod specific methods."""

    def doRead(self,term,tout):
        matcher = re.compile(term)    #gives you the ability to search for anything
        buff    = ""
        tic     = time.clock()
        buff   += self.read(128)
        # you can use if not ('\n' in buff) too if you don't like re
        while ((time.clock - tic) < tout) and (not matcher.search(buff)):
            buff += self.read(128)
    
        return buff

    def send_at(self, cmd, suffix, prefixed=True):
        """Send serial text to the modem.

        Arguments:
            self -- serial port to send to,
            text -- text value to send,
            prefixed -- boolean determining weather to strip the AT
                        command prefix from each output line.

        Returns:
            List of strings.
        """
        self.write('AT%s%s\r' % (cmd, suffix))
        #print "D: - Sending " + ('AT%s%s\r' % (cmd, suffix))
        # Read in the echoed text.
        # Check for errors and raise exception with specific error code.
        input_line = self.readline()
        errors.check_for_errors(input_line)
        # Return the result.
        if prefixed:
            # If the text being sent is an AT command, only relevant context
            # answer (starting with '+command:' value) will be returned by 
            #return_data(). Otherwise any string will be returned.
            return self.return_data(cmd)
        else:
            return self.return_data()

    def read_waiting(self):
        """Clear the serial port by reading all data waiting in it."""
        return self.read(self.inWaiting())

    def return_data(self, command=None):
        """Read until exit status is returned.

        Returns:
            data: List of right-stripped strings containing output
            of the command.

        Raises:
            AtCommandError: If an error is returned by the modem.
        """
        data = list()
        while 1:
            # Read in one line of input.
            input_line = self.readline().rstrip()
            # Check for errors and raise exception with specific error code.
            errors.check_for_errors(input_line)
            if input_line == 'OK':
                return data
            # Append only related data (starting with "command" contents).
            if command:
                if input_line.startswith(command):
                    prefix_length = len(command)+2
                    data.append(input_line[prefix_length:])
            else:
                # Append only non-empty data.
                if input_line:
                    data.append(input_line)


class ConnectionStatus(object):
    """Data structure representing current state of the modem."""

    def __init__(self):
        """Constructor for ConnectionStatus class."""
        self.rssi = 0
        self.uplink = 0
        self.downlink = 0
        self.bytes_tx = 0
        self.bytes_rx = 0
        self.link_uptime = 0
        self.mode = None
 
    def report(self):
        """Print connection status report."""
        format = '%20s : %5s'
        mapping = (('Signal Strength', self.rssi),
                   ('Bytes rx', self.bytes_rx),
                   ('Bytes tx', self.bytes_tx),
                   ('Uplink (B/s)', self.uplink),
                   ('Downlink (B/s)', self.downlink),
                   ('Seconds uptime', self.link_uptime),
                   ('Mode', self.mode))
        print
        for item in mapping:
            print format % item


class Modem(atc.SetCommands, atc.GetCommands, atc.ShowCommands,
            atc.InteractiveCommands, atc.EnterCommands):
    """Class representing a modem."""

    # pylint: disable-msg=R0901
    # pylint: disable-msg=R0904
    
    status = ConnectionStatus()
    #baudrate = 9600
    PPPD_PARAMS = ['modem', 'crtscts', 'defaultroute', 'usehostname', '-detach', 'noauth' ,
               'noipdefault', 'call', 'humod', 'user', 'ppp', 'usepeerdns',
               'idle', '0', 'logfd', '8']
    pppd_params = PPPD_PARAMS
    _pppd_pid = None
    _dial_num = '*99#'

    def __init__(self, data,audio, ctrl,cfg):
        """Open a serial connection to the modem."""
        self.cfg = cfg

        self.IP = "None"
        self.bAnswering = False
        
        _dial_num = self.cfg.dialnum
        
        if ( not cfg.usedongle ):
            return
        
        self.data_port = ModemPort()
        self.data_port.setPort(data)
        self.data_port.setBaudrate(self.cfg.modem_baudrate)

        self.audio_port = ModemPort()
        self.audio_port.setPort(audio)
        self.audio_port.setBaudrate(self.cfg.audio_baudrate)

        self.ctrl_port = ModemPort(ctrl, self.cfg.ctrl__baudrate,
                                   timeout=self.cfg.prober_timeout)
        
        
            
        self.ctrl_lock = threading.Lock()
        self.prober = Prober(self)
        atc.SetCommands.__init__(self)
        atc.GetCommands.__init__(self)
        atc.EnterCommands.__init__(self)
        atc.InteractiveCommands.__init__(self)
        atc.ShowCommands.__init__(self)
        # Tony
        self.ctrl_port.send_at("Z","",False) # Echo Disabled
        self.ctrl_port.send_at("E0","",False) # Echo Disabled
        self.ctrl_port.send_at("^CURC=0","",False) # disable periodic message
        #self.ctrl_port.send_at("+CVHU=0","",False) # enable hang-up voice call 
        self.ctrl_port.send_at("H","",False)	
        

#     def answerCall(self,listOfMessages): # Tony 2012
#         """answer a call with a list of message provided."""
#         audio_port = self.audio_port
#         audio_port.open()
#         self.answer()
#         self.set_destination_port(2)
# 
#         time.sleep(0.5)
#         for message in listOfMessages:
#             time.sleep(0.2)
#             if ( not os.path.exists(message)):
#                 log( "ERROR : File not found : " + message)
#                 continue
#             f = open(message, "rb")
#             while True:
#                 chunk = f.read(320)
#                 if chunk:
#                     #print "sending chunk"
#                     audio_port.write(chunk)
#                     time.sleep( 0.020 )
#                 else:
#                     break
#         log( "DEBUG : Message sended : " )
#         time.sleep(1)
#         self.hangup()
#         log( "DEBUG : hangup  " )
#         time.sleep(1)
#         audio_port.close()        
#         log( "DEBUG : audio_port.close  " )
        
    def answerCallNew(self,listOfMessages): # Tony 2012
        try:
            globalvars.bAnswering = True
            """answer a call with a list of message provided."""
            audio_port = self.audio_port
            audio_port.open()
            self.answer()
            self.set_destination_port(2)
            
            memfile = ""
            for message in listOfMessages:
                if ( not os.path.exists(message)):
                    log( "WARNING : File not found : " + message)
                    continue
                f = open(message, "rb")
                chunk = f.read()
                memfile += chunk
    
            i = 0
            while ( (i) < len(memfile) ):
                fine = min(len(memfile),i+320) 
                chunk = memfile[i:fine]		
                audio_port.write(chunk)
                time.sleep( 0.020 )
                #time.sleep( 0.020 )
                i += 320
            
            #log( "DEBUG : Message sended : " )
            time.sleep(1)
            self.hangup()
            #log( "DEBUG : hangup  " )
            time.sleep(1)
            globalvars.bAnswering = False
            audio_port.close()        
            #log( "DEBUG : audio_port.close  " )
            
            return True
        except:
            log("Error in answering call. May be user has hangup")
            globalvars.bAnswering = False  
            audio_port.close()
              
            return False		


    def connectwvdial(self):
        if ( self._pppd_pid != None ) :
            self.disconnectwvdial()
        if os.name != 'nt':
            pid = os.fork()
        else:
            pid = 0 
        if pid:
            self._pppd_pid = pid
        else:
            try:
                logFile = datetime.datetime.now().strftime("log/wvdial_%d%m%Y.log")
                os.system("wvdial -C " + self.cfg.operator + ".conf 2>> " + logFile)
            except:
                raise errors.PppdError('An error while starting wvdial.')
            

    def disconnectwvdial(self):
        """Disconnect the modem."""
        if self._pppd_pid:
            #print self._pppd_pid
            os.kill(self._pppd_pid, 15)
            os.kill(self._pppd_pid+1, 15)
            os.kill(self._pppd_pid+2, 15)
            #os.kill(self._pppd_pid,signal.SIGINT) # tony
#            os.waitpid(self._pppd_pid, 2)
            self._pppd_pid = None 
#            print self._pppd_pid
#            self.IP = "None"
#            log("Disconnected")
            return True
        else:
            log( "Not connected")
            return False

    def tryconnect(self, dialtone_check):
        """Use pppd to connect to the network."""
        try:
            # Modem is not connected if _pppd_pid is set to None.
            if not self._pppd_pid:
                data_port = self.data_port
                #log( "Openind data")
                data_port.open()
                #log( "Opened")
                data_port.write('ATZ\r\n')
                print data_port.return_data()
                data_port.write('ATQ0 V1 E1 S0=0 &C1 &D2 +FCLASS=0\r\n')
                print data_port.return_data()
                data_port.write('AT+CGDCONT=1,"IP","internet.wind",,\r\n')
                print data_port.return_data()
                if not dialtone_check:
                    data_port.write('ATX3\r\n')
                    print data_port.return_data()
                data_port.write('ATDT%s\r\n' % self._dial_num)
                print data_port.readline()
                status = data_port.readline()
                print status
                if status.startswith('CONNECT' )  :
#                   pppd_args = [defaults.PPPD_PATH, self.baudrate, self.data_port.port] + self.pppd_params
                    pppd_args = [self.pppd_path, self.data_port.port ,self.baudrate ] + self.pppd_params							 
                    pid = os.fork() 
                    if pid:
                        self._pppd_pid = pid
                    else:
                        try:
                            
                            os.execv(self.pppd_path, pppd_args)
                        except:
                            raise errors.PppdError('An error while starting pppd.')
            else:
                last_pppd_result = os.waitpid(self._pppd_pid, os.WNOHANG)
                if last_pppd_result != (0, 0):
                    # Reconnect.
                    self._pppd_pid = None
                    self.connect(dialtone_check)
                else:
                    # Modem already connected.   
                    raise errors.HumodUsageError('Modem already connected.')
            return True
        except:
            return False

    def connect(self, dialtone_check=True):
        for i in range(1,5):
            if self.tryconnect(dialtone_check):
                return True
            time.sleep(1)
        return False


    def disconnect(self):
        """Disconnect the modem."""
        if self._pppd_pid:
            #os.kill(self._pppd_pid, 15)
            os.kill(self._pppd_pid,signal.SIGINT) # tony
            os.waitpid(self._pppd_pid, 0)
            self._pppd_pid = None 
            
            os.system('echo "AT0" > /dev/ttyUSB0')
            self.data_port.close()
            return True
        else:
            return False
            #raise errors.HumodUsageError('Not connected.')
            
if __name__ == '__main__':

    configfile = 'swpi.cfg'
    if not os.path.isfile(configfile):
        "Configuration file not found"
        exit(1)    
    cfg = config.config(configfile)
    
    modem = Modem(cfg.dongleDataPort,cfg.dongleAudioPort,cfg.dongleCtrlPort,cfg)
    print modem
    
    print ""
    log( "Modem Model : "  + modem.show_model())
    log(  "Revision : "  + modem.show_revision())
    log(  "Modem Serial Number : " + modem.show_sn())
    log(  "Pin Status : " + modem.get_pin_status())
    log(  "Device Center : " + modem.get_service_center()[0] + " " + str(modem.get_service_center()[1]))
    log(  "Signal quality : " + str(modem.get_rssi()))
    
    
    log( "Checking new sms messages...")
    smslist = modem.sms_list()
    for message in smslist:
        print message
    
    #modem.enable_textmode(True)
    modem.enable_clip(True)    
    modem.enable_nmi(True)


    
#    log("trying to send sms to %s" % cfg.number_to_send)
#    modem.sms_send(cfg.number_to_send, "prova")
    
#     log( "Trying to connect to internet with 3G dongle ....")
#     time.sleep(1)
#     modem.connectwvdial()
#     time.sleep(2)
#     waitForIP()
#     IP = getIP()
#     if IP != None:
#         log("Connected with IP :" + IP)
#     time.sleep(10)
#     
#     log( "Trying to disconnect 3G dongle ....")
#     modem.disconnectwvdial()
    