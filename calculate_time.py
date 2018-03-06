# coding:utf-8

"""
@author:xiaobai
@date:2018-03-05
@desc:利用高德api计算北京两地铁站之间的距离

注:更改mongo数据库中某字段的字段类型
db.ziru_data.find({}).forEach(function(x){x.room_square=parseFloat(x.room_square);db.ziru_data.save(x)})
result = ziru_data.find()

for item in result:
	if item["room_square"].find(u"约") != -1:
		 room_square = item["room_square"].replace(u"约",'')
		 ziru_data.update({"room_num":item['room_num'],"room_price":item['room_price']},{"$set":{"room_square":room_square}})
"""
import requests

import pymongo
import json
client = pymongo.MongoClient("127.0.0.1",27017)
db = client.research
ziru_data = db.ziru_data
"""
[39.9249428832,116.4346075058],
"""
origin_list = [[39.9761869497,116.3538730145]]

def load_ditie_loc():
	bjditie_data = db.bjditie_data
	result = bjditie_data.find({})
	for origin in origin_list:
		print origin
		for item in result:
			stop_name = item["stop_name"]
			loc_x = item["loc_x"] 
			loc_y = item["loc_y"]
			route = crawl_time(origin[1],origin[0],float(loc_y),float(loc_x))


			bjditie_data.update({"stop_name":stop_name},{"$set":{"xitu":route}})

# 计算两地点之间的距离
def crawl_time(a,b,c,d):
	# y,x
	url = "http://restapi.amap.com/v3/direction/transit/integrated?key=e1dfd64c9a62c7608d3a0eb7e225857f&origin=%s,%s&destination=%s,%s&city=北京&cityd=北京&strategy=0&nightflag=0&date=2018-3-19&time=18:00" % (a,b,c,d)
	response = requests.get(url)
	content = json.loads(response.content)
	return content["route"]
def main():
	load_ditie_loc()

if __name__ == '__main__':
	main()
