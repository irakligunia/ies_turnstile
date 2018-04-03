 # -*- coding: utf-8 -*-
import io
from ctypes import *

ip = "10.0.0.245"

params = "protocol=TCP,ipaddress=" + ip + ",port=4370,timeout=4000,passwd="

commpro = windll.LoadLibrary("plcommpro.dll")

def turnstile_time_to_mysql_time(time):
	time = int(time)
	seconds = str(time % 60).zfill(2)
	time /= 60
	minute = str(time % 60).zfill(2)
	time /= 60
	hour = str(time % 24).zfill(2)
	time /= 24
	day = str(time % 31 + 1).zfill(2)
	time /= 31
	month = str(time % 12 + 1).zfill(2)
	time /= 12
	year = str(time + 2000)

	return (year + '-' + month + '-' + day + ' '+ hour + ':' + minute + ':' + seconds)



constr = create_string_buffer(params) 
hcommpro = commpro.Connect(constr)

if hcommpro != 0:
	print "Connected successfully to turnstile..."
else:
	print "Cannot connect to turnstile via IP(" + ip +") address"
	commpro.Disconnect(hcommpro)
	exit()


table = "transaction"		# Download the user data from the user table
fieldname = "*"		# Download all field information in the table
query_filter = ""	# Have no filtering conditions and thus download all information
options = ""	
query_buf = create_string_buffer(4*1024*1024)
query_table = create_string_buffer(table)


# print type(query_table), query_table
# exit()

query_fieldname = create_string_buffer(fieldname)
query_filter = create_string_buffer(query_filter)
query_options = create_string_buffer(options)
ret = commpro.GetDeviceData(hcommpro, query_buf, 4*1024*1024, query_table, query_fieldname, query_filter, query_options)
if ret>0:
	print query_buf.value
	print str(ret) + ' ' + table + ' records found!'
	# print query_buf.value
else:
	print "Error - 1"
	exit()
commpro.Disconnect(hcommpro)
hcommpro = 0

lines = query_buf.value.split('\r\n')
del lines[0]
del lines[-1]
for line in lines:
	words = line.split(',')

	# print words
	# print line

print "done"