###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

import sys
import struct
import ConfigParser
import os
import ftplib
# import Image
# import ImageFont, ImageDraw, ImageOps
import urllib2
import time

class Version(object):
    """Class defining software configuration."""
    def __init__(self,versionfile):
        self.versionfile = versionfile
        if ( not os.path.isfile(versionfile)):
            self.ver = "00.00.00"
            self.magior = 0
            self.minor = 0
            self.build = 0
        else:
            f = open(versionfile, "r")
            self.ver = f.read()
            self.magior = int(self.ver.split('.')[0])
            self.minor = int(self.ver.split('.')[1])
            self.build = int(self.ver.split('.')[2])
    
    def getVersion(self):
        return self.ver
        
        
    def incBuild(self):
        self.build = self.build+1
        if ( self.build > 99 ) :
            self.minor = self.minor + 1
            self.build = 0
        self.ver = "%2.2d.%2.2d.%2.2d" % (self.magior ,self.minor ,self.build)
        f = open(self.versionfile, "w")
        f.write(self.ver)
        
        
 
if __name__ == '__main__':
    v = Version("VERSION")
    print v.getVersion() 
    v.incBuild()
    print v.getVersion() 