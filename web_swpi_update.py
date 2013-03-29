###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""updare ."""

import string
import globalvars
import os
import version
import urllib
import tarfile

def swpi_update():
    url = ' http://www.vololiberomontecucco.it/swpi/swpi-src.tar.gz'
    urllib.urlretrieve(url,filename='swpi-src.tar.gz')
    t = tarfile.open('swpi-src.tar.gz', 'r:gz')
    t.extractall('../')  
    os.remove("swpi-src.tar.gz")
    os.system( "sudo chown pi mcp3002/" )
    os.system( "sudo chown pi TX23/" )
    os.system( "sudo chown pi wh1080_rf/" )
    os.system( "sudo chown pi DHT/" )    
    
html1 = """<head>
    <title>Sint Wind PI</title>
    <style type="text/css">
        #TextArea1
        {
            height: 600px;
            width: 800px;
        }
    </style>
</head>
<body onload="init()">

    <script>
        function init() {
 
        }
        function Reboot_onclick() {
            window.location = '/web_reboot.py'
        }

    </script>
    

    <p>
            <img alt="swpi" src="swpi-banner.jpg" 
            width="800" /><br />
    <p>
        &nbsp;</p>
    <p>"""
    
html2 = """</body>
</html>"""


so = Session()
if not hasattr(so,'loggedin'):
    raise HTTP_REDIRECTION,"index.html"

old_version = version.Version("./VERSION").getVersion()

swpi_update()

new_version = version.Version("./VERSION").getVersion()

print html1
if (old_version == new_version ):
    message = "system is already up to date. Current version is %s <br>" % new_version
else:
    message = 'System updated from version %s to version %s . A system reboot is needed to activate the new version<br> <input id="Reboot" type="button" value="Reboot" onclick="return Reboot_onclick()" />'  %(old_version,new_version)
    
print message

print html2