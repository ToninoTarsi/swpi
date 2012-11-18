## Copyright 2009 Laurent Bovet <laurent.bovet@windmaster.ch>
##                Jordi Puigsegur <jordi.puigsegur@gmail.com>
##
##  This file is part of wfrog
##
##  wfrog is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
from math import pow, sqrt

reference = {
    "temp": "C",
    "press": "hPa",
    "wind": "m/s",
    "rain": "mm",
}

def identity(value):
    return value

def FToC(value): 
    return (((value * 1.0) - 32.0) * 5.0) / 9.0 if value != None else None

def CToF(value): 
    return  ((value * 9.0) / 5.0) + 32.0 if value != None else None

def InHgToHPa(value):
    return value / 0.02953 if value != None else None

def HPaToInHg(value):
    return value * 0.02953 if value != None else None

def HPaToMmHg(value):
    return value * 0.750062 if value != None else None

def MmHgToHPa(value):
    return value / 0.750062 if value != None else None

def InToMm(value): 
    return value * 25.4 if value != None else None

def MmToIn(value): 
    return value / 25.4 if value != None else None

def MpsToKt(value):
    return value / 0.514 if value != None else None

def KtToMps(value):
    return value * 0.514 if value != None else None

def MpsToKmh(value):
    return value * 3.6 if value != None else None

def KmhToMps(value):
    return value / 3.6 if value != None else None

def MphToMps(value): 
    return value / 2.2445 if value != None else None

def MpsToMph(value): 
    return value * 2.2445 if value != None else None
    
def MpsToBft(value):
    return pow((pow((value*3.6),2))/9, 1.0/3.0) if value != None else None

def BftToMps(value):
    return sqrt(pow(value, 3)*9)/3.6 if value != None else None
    
conversions = {
    "temp" : {
        "C" : [ identity, identity ],
        "F" : [ CToF, FToC ],
        },
    "press" : {
        "hPa" : [ identity, identity ],
        "mmHg" : [ HPaToMmHg, MmHgToHPa ],
        "inHg" : [ HPaToInHg, InHgToHPa ],
        },
    "wind" : {
        "m/s" : [ identity, identity ],
        "km/h": [ MpsToKmh, KmhToMps ],
        "mph": [ MpsToMph, MphToMps ],
        "kt": [ MpsToKt, KtToMps ],
        "bft": [MpsToBft, BftToMps ]
        },
    "rain" : {
        "mm" : [identity, identity ],
        "in" : [MmToIn, InToMm ],
    }
}

def convert(measure, value, to_units, from_units=None):
    try:
        val = value
        if from_units: # convert to reference units
            val = conversions[measure][from_units][1](val)
        if not to_units:
            return val 
        return conversions[measure][to_units][0](val)
    except:
        return val

class Converter(object):
    
    units = reference
    
    def __init__(self, units):
        self.units.update(units)
    
    def convert(self, measure, value):        
        raw_measure = re.split("[0-9]|int", measure)[0] # strip trailing numbers
        if not self.units.has_key(raw_measure): 
            return value
        return convert(raw_measure, value, self.units[raw_measure])            

    def convert_back(self, measure, value):        
        raw_measure = re.split("[0-9]|int", measure)[0] # strip trailing numbers
        if not self.units.has_key(raw_measure): 
            return value
        return convert(raw_measure, value, None, self.units[raw_measure])      
    
    def temp(self, value):
        return self.convert("temp", value)

    def press(self, value):
        return self.convert("press", value)

    def wind(self, value):
        return self.convert("wind", value)

    def rain(self, value):
        return self.convert("rain", value)

def unit_roll(measure, unit):
    """Gives the next unit alternative, wrapping"""
    k=conversions[measure].keys()
    i = k.index(unit)
    if i==len(k)-1:
        return k[0]
    else:
        return k[i+1]
    

if __name__ == "__main__":
    target = {
    "temp": "F",
    "press": "mmHg",
    "wind": "kt",
    "rain": "in",
}
    
    c = Converter( target )
    
    print c.temp(20)
    print c.wind(1)
    print c.rain(254)
    print c.press(1000)
