###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""reboot ."""

import config
import string
import os


so = Session()
if not hasattr(so,'loggedin'):
    raise HTTP_REDIRECTION,"index.html"



if os.name != 'nt':
    os.system("sudo reboot")
else:
    print " Sorry can not rebbot windows"

