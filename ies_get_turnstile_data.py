# -*- coding: utf-8 -*-

# 1. readme -ში ჩავწეროთ რომ turnstile_records ცხრილში სადაც გადაგვაქვს ტურნიკეტის
#    მონაცემები. უნდა არსებობდეს UNIQUE ინდექსი:
#	 ALTER TABLE  `ies_inventari`.`turnstile_records` 
#	 ADD UNIQUE  `unique_row` (  `date_time` ,  `card_number` ,  `in_out_state` )

import os
import MySQLdb
import io
from ctypes import *
from datetime import datetime

turnstile_ip = "10.0.0.245"
mysql_ip = "10.0.0.237"
mysql_user = "turnstile"
mysql_pass = "turnstile"
mysql_db = "ies_inventari"
turnstile_conn_params = "protocol=TCP,ipaddress=" + turnstile_ip + ",port=4370,timeout=4000,passwd="
# log ფაილის სახელი
log_filename = "log"
# სკრიპტი ბეჭდავდეს თუ არა ტერმინალში
printing = False
# სკრიპტი წერდეს თუ არა log ფაილში
write_in_log = True

# სკრიპტის მისამართი
script_path = os.path.dirname(os.path.realpath(__file__))
log_file_path = script_path + "/" + log_filename
# შევცვალოთ სამუშაო დირექტორია იმ მისამართზე სადაც გვაქვს ies_get_turnstile_data.py
os.chdir(script_path)
commpro = windll.LoadLibrary(script_path + "/plcommpro.dll")

# ფუნქცია ბეჭდავს ტერმინალში და წერს ლოგ ფაილში მიწოდებულ message ტექსტს
def print_and_log(message):
	current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	if printing is True:
		print ("[" + current_time + "] " + message)
	if write_in_log is True:
		log_file = open(log_file_path, "a")
		log_file.write("[" + current_time + "] " + message + "\n")
		log_file.close()


try:
	# Mysql - თან დაკავშირება
	db = MySQLdb.connect(mysql_ip, mysql_user, mysql_pass, mysql_db)
	cursor = db.cursor()
except:
	print("Cannot connect to Mysql on %s" % mysql_ip)
	exit()

print("Connected successfully to Mysql on %s" % mysql_ip)


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



constr = create_string_buffer(turnstile_conn_params) 
conn_hendler = commpro.Connect(constr)

if conn_hendler != 0:
	print "Connected successfully to turnstile..."
else:
	print "Cannot connect to turnstile via IP(" + turnstile_ip +") address"
	commpro.Disconnect(conn_hendler)
	db.close()
	exit()


table = "transaction" # Download the user data from the user table
fieldname = "*"		# Download all field information in the table
query_filter = "Cardno=3944526"	# Have no filtering conditions and thus download all information
options = ""	
query_buf = create_string_buffer(4*1024*1024)
query_table = create_string_buffer(table)
query_fieldname = create_string_buffer(fieldname)
query_filter = create_string_buffer(query_filter)
query_options = create_string_buffer(options)
ret = commpro.GetDeviceData(conn_hendler, query_buf, 4*1024*1024, query_table, query_fieldname, query_filter, query_options)

if ret > 0:
	print str(ret) + ' ' + table + ' records found!'
else:
	print "Error (GetDeviceData)- " + str(ret)
	commpro.Disconnect(conn_hendler)
	db.close()
	exit()
commpro.Disconnect(conn_hendler)
conn_hendler = 0

lines = query_buf.value.split('\r\n')
insert_columns = "INSERT IGNORE INTO  turnstile_records (date_time ,card_number, in_out_state) VALUES"
insert_queries = ""
insert_values = ""
insert_values_caunt = 0
del lines[0]
del lines[-1]
for line in lines:
	values = line.split(',')
	card_number = values[0]
	verified = values[2]
	event_type = values[4]
	in_out_state = values[5]
	time = turnstile_time_to_mysql_time(values[6])

	if (verified == '4' and event_type == '0'):
		insert_values += "('%s', '%s', '%s')," % (time, card_number, in_out_state)
		insert_values_caunt += 1
	else:
		print_and_log("wrong value(s): %s %s %s %s %s" % (card_number, verified, event_type, in_out_state, time))

	if insert_values_caunt >= 500:
		try:
			cursor.execute(insert_columns + insert_values[:-1])
			db.commit()
		except:
			print_and_log("Error during inserting turnstile data in mysql(%s)" % mysql_ip)
		insert_values = ""
		insert_values_caunt = 0


if insert_values_caunt > 0:
	try:
		cursor.execute(insert_columns + insert_values[:-1])
		db.commit()
	except:
		print_and_log("Error during inserting turnstile data in mysql(%s)" % mysql_ip)
print "done"
