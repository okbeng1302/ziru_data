# coding:utf-8

# import sys
import re
import pymongo

import codecs
fd = codecs.open('ditie.txt')
content = fd.read()

client = pymongo.MongoClient("127.0.0.1",27017)
db = client.research
bjditie_data = db.bjditie_data

stop_list = content.split("|")
print len(stop_list)
for item in stop_list:
	line = {}
	line_info = item.split(",")
	line['loc_x'] = line_info[1]
	line['loc_y'] = line_info[2]
	line["stop_name"] = line_info[0]
	if bjditie_data.find_one({"stop_name":line_info[0]}):
		print "地铁站：",line_info[0],"已存在"
	else:
		bjditie_data.insert(line)
fd.close()