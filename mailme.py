###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################
#                      Mail a file
from TTLib import *
import sys

configfile = 'swpi.cfg'
if not os.path.isfile(configfile):
    "Configuration file not found"
    exit(1)    
cfg = config.config(configfile)

for arg in sys.argv[1:]: 
    print "Sending file: ",arg

    print SendMail(cfg,"your file","your file",arg) 
    