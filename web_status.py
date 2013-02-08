###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""reboot ."""

import string
import globalvars
import os

so = Session()
if not hasattr(so,'loggedin'):
    raise HTTP_REDIRECTION,"index.html"

if 'update' in request.keys():
    update = request['update'][0]
else:
    update = "1"
    

HTML_TEMPLATE = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" >
<head>
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
            var textarea = document.getElementById('TextArea1');
            textarea.scrollTop = textarea.scrollHeight;
            
            $reloadfunction
        }
        
        function CheckboxUpdate_onclick() {
            if (CheckboxUpdate.checked == 1)
                window.location = "/web_status.py?update=1";
            else
                window.location = "/web_status.py?update=0";
             
        }

    </script>
    

    <p>
            <img alt="swpi" src="swpi-banner.jpg" 
            width="800" /><br />
        Auto update <input id="CheckboxUpdate" type="checkbox" $checked onclick="return CheckboxUpdate_onclick()" name="CheckboxUpdate" />
        <br />
        <textarea id="TextArea1" name="S1">$log</textarea></p>

</body>
</html>"""

html_template=string.Template(HTML_TEMPLATE)



filetoadd = "log/log"+globalvars.logFileDate+".log"
#filetoadd = "log/log"+"28012013"+".log"


if ( os.path.isfile(filetoadd) ) :  
    f = open(filetoadd,"r")
    text = f.read()
    d = dict(log=text)
    f.close()

    if update == "1" :
        d.update(reloadfunction="setTimeout(function() {window.location.reload(1);}, 5000);") 
        d.update(checked='checked="checked"')
    else:
        d.update(reloadfunction="") 
        d.update(checked='')


    html = html_template.safe_substitute(d)

    print html
else:
    print "log file not found"



