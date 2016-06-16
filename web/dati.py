import sqlite3
import json
import collections
import datetime
import os

try:
    datastart = request['datestart'][0]
    datastop = request['datestop'][0]
    interval = int(request['interval'][0])
except:
    datastart = str(datetime.datetime.now().strftime("%Y-%m-%d 00:00:00"))
    datastop = str(datetime.datetime.now().strftime("%Y-%m-%d 23:59:59"))
    interval= 10

conn = sqlite3.connect('/swpi/db/swpi.s3db',200)
dbCursor = conn.cursor()
sql=('SELECT TIMESTAMP_LOCAL,HUM,TEMP,TEMP_APPARENT,TEMPINT,HUMINT,DEW_POINT,WIND_AVE,WIND_GUST,WIND_CHILL,WINDIR_CODE,WIND_DIR,PRESSURE from Meteo \
WHERE TIMESTAMP_LOCAL >"%s" and TIMESTAMP_LOCAL<"%s" order by TIMESTAMP_LOCAL desc')%(datastart,datastop)
dbCursor.execute(sql)
rows = dbCursor.fetchall()

objects_list = []
i=1


for row in rows:
    i=i+1
    if (i%interval)==0:
        d = collections.OrderedDict()
        d['TIME']= row[0][:19]
        d['HUM'] = row[1]
        d['TEMP'] = row[2] 
        d['TEMP_APPARENT'] = row[3]
        d['TEMPINT'] = row[4]
        d['HUMINT'] = row[5]
        d['DEW_POINT'] = row[6]
        d['WIND_AVE'] = row[7]
        d['WIND_GUST'] = row[8]
        d['WIND_CHILL'] = row[9]
        d['WINDIR_CODE'] = row[10]
        d['WIND_DIR'] = row[11]
        d['PRESSURE'] = row[12]
        objects_list.append(d)
 
j = json.dumps(objects_list)
objects_file = '/swpi/web/dati.json'
f = open(objects_file,'w')
print >> f, j

conn.close()
redirectURL ="graph.html"
print 'Content-Type: text/html'
print 'Location: %s' % redirectURL
print # HTTP says you have to have a blank line between headers and content
print '<html>'
print '  <head>'
print '    <meta http-equiv="refresh" content="0;url=%s" />' % redirectURL
print '    <title>You are going to be redirected</title>'
print '  </head>' 
print '  <body>'
print '    Redirecting... <a href="%s">Click here if you are not redirected</a>' % redirectURL
print '  </body>'
print '</html>'
