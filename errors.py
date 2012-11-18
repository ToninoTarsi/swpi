###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#     Modem comunications based on Slawek Ligus pyhumod-0.03 module
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################

"""Exceptions and error-handling methods."""
from TTLib import *

ERROR_CODES = ['COMMAND NOT SUPPORT', 'ERR', 'NO CARRIER', 'BUSY']

class Error(Exception):
    """Generic Exception."""
    pass

class AtCommandError(Error):
    """AT Command exception."""
    pass

class PppdError(Error):
    """PPPD fork-exec exception."""
    pass

class HumodUsageError(Error):
    """Humod usage error exception."""
    pass

def check_for_errors(input_line):
    """Check if input line contains error code."""
    if ('ERROR' in input_line) or (input_line in ERROR_CODES):
        raise AtCommandError, input_line
        


