###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""upload ."""

import config
import string


so = Session()
if not hasattr(so,'loggedin'):
    raise HTTP_REDIRECTION,"index.html"


filecontent = request['file'][0]

#print filecontent

f = open("swpi.cfg", "w")
f.write(filecontent)
f.close()

raise HTTP_REDIRECTION,"swpi_webconfig.py"

# A nested FieldStorage instance holds the file
#fileitem = form['file']

