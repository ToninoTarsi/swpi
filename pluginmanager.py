###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     USB comunication based pywws by 'Jim Easterbrook' <jim@jim-easterbrook.me.uk>
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

""" plugin manager."""

import os
import sys
import importlib
import config
from TTLib import  *

class PluginLoader():
    def __init__(self, path,cfg):
        self.path = path
        self.cfg = cfg

    def loadAll(self):
        log("loading plugins")
        for (dirpath, dirs, files) in os.walk(self.path):
            if not dirpath in sys.path:
                sys.path.insert(0, dirpath)
        for file in files:
                (name, ext) = os.path.splitext(file)
                if ext == os.extsep + "py":
                    if ( name != "example" and name !="sync_plugin" and name != "__init__"):
                        mod =  importlib.import_module(name)
                        swpi_plugin_Thread = mod.swpi_plugin(self.cfg)
                        swpi_plugin_Thread.start()
        
            
            
if __name__ == '__main__':

    print "starting"
    
    configfile = 'swpi.cfg'
    cfg = config.config(configfile)
        
    pl = PluginLoader("./plugins",cfg)
    pl.loadAll()
    
    