###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""get cfg file ."""

import config
import string

so = Session()


if not hasattr(so,'loggedin'):
    raise HTTP_REDIRECTION,"index.html"
#else:
#    if ( not so['loggedin'] ):
#        raise HTTP_REDIRECTION,"index.html"    
#    

raise HTTP_REDIRECTION,"swpi.cfg"

