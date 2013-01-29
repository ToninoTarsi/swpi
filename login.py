###########################################################################
#	 Sint Wind PI
#	 Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#	 Please refer to the LICENSE file for conditions 
#	 Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""config web server login."""

import config

configfile = 'swpi.cfg'
cfg = config.config(configfile,False)


# set the attribute 'user' of the session object
so = Session()
so.user = request['user'][0]
so.password = request['password'][0]

if ( so.user.upper() == "ADMIN" and so.password == cfg.SMSPwd ):
	# redirect to the home page
	so.loggedin = True
	raise HTTP_REDIRECTION,"swpi_webconfig.py"
else:
	raise HTTP_REDIRECTION,"index.html"

