#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2018-03-05 08:33:33
# Project: ziru_data

from pyspider.libs.base_handler import *
import re
import pymongo
import datetime
import time
from datetime import timedelta

MONGODB_IP = '127.0.0.1'
MONGODB_PORT = 27017

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}


class Handler(BaseHandler):
    crawl_config = {
    }

    @every(minutes=3 * 60)
    def on_start(self):
        self.crawl('http://www.ziroom.com/z/nl/z1-u2-s1%E5%8F%B7%E7%BA%BF.html',headers=headers, callback=self.index_page)

    @config(age=60 * 60)
    def index_page(self, response):
        # 地铁航线列表
        line_list = response.doc('dl[class="clearfix zIndex5"] > dd > ul > li').items()
        index = 1
        for item in line_list:
            if index == 1:
                index = index + 1
            else:
                # 地铁路线
                line_name = item('li > span > a').text()
                print line_name
                # 地铁站点 
                station_list = item('li > div > span').items()
                for point in station_list:
                    stop_name = point('span > a').text()
                    stop_url = point('span > a').attr.href
                    if stop_name.find(u'全部') == -1:
                        print stop_name,stop_url
                        self.crawl(stop_url,headers=headers,callback = self.detail_page,save={'line_name':line_name,'stop_name':stop_name})

    @config(priority=2)
    def detail_page(self, response):
        room_list = response.doc('ul[id="houseList"] > li').items()
        
        for item in room_list:
            detail_url = item('li > div[class="priceDetail"] > p[class="more"] > a').attr.href
            self.crawl(detail_url,headers=headers,callback=self.parse_content,save={'line_name': response.save['line_name'],'stop_name': response.save['stop_name']})
    @config(age=60 * 60)      
    def parse_content(self,response):
        
        if response.text.find(u'咦~这个房源不见了~') != -1:
            pass
        else:
            # 地铁线路
            line_name = response.save['line_name'].encode("utf-8")
            # 地铁站点
            stop_name = response.save['stop_name'].encode("utf-8")
            # 房间名称
            room_name = response.doc('div[class="room_name"] > h2').text().encode("utf-8")

            # 房间地区
            location_temp = response.doc("div.room_name > p > span.ellipsis").text()
            loc_1 = location_temp.find("]")
            location = location_temp[1:loc_1].split(" ")[0]
            loc_attr1 = location_temp[1:loc_1].split(" ")[len(location_temp[1:loc_1].split(" "))-1]
            # 价钱
            price = response.doc('span[class="room_price"]').text().replace(u"￥",'')
            # 付钱周期
            period = response.doc('span.price > span[class="gray-6"]').text().replace(u"● /",'')
            # 房间信息
            room_info_list = response.doc('ul[class="detail_room"] > li').items()
            index = 1
            square = ''
            direction = ''
            room_type = ''
            floor = ''
            room_tran = ''

            for item in room_info_list:
                # 房间面积
                if index == 1:
                    square = item.text().split()[1]
                    if square.find(u"约") != -1:
                        square = room_square.replace(u"约",'')
                # 房间朝向
                if index == 2:
                    direction = item.text().split()[1].encode("utf-8")
                # 房间户型
                if index == 3:
                    room_type = item.text().split()[1].encode("utf-8")
                # 房间楼层
                if index == 4:
                    floor = item.text().split()[1].encode("utf-8")
                # 房间交通
                if index == 5:
                    room_tran = item('span').text().split(" ")
                index = index + 1
            # 房间特点
            room_tags_list = []
            room_tags = response.doc('p[class="room_tags clearfix"] > span').items()
            for item in room_tags:
                room_tags_list.append(item.text().encode("utf-8"))
            # 房间编号
            room_num = response.doc('h3.fb').text().split(" ")[1].encode("utf-8")

            p_list = response.doc('div[class="aboutRoom gray-6"] > p').items()
            # 房间周边
            room_around = ''
            # 周围交通
            around_tran = ''
            for item in p_list:
                if item.text().find(u"周边：") != -1:
                    room_around = item.text().encode("utf-8").split("：")[1].strip()
                else:
                    around_tran = item.text().encode("utf-8").split("：")[1].strip()
            # 房间配置
            deploy = []
            deploy_list = response.doc("ul[class='configuration clearfix'] > li").items()
            for item in deploy_list:
                deploy.append(item.text().encode("utf-8"))


            ziru_data = {}
            ziru_data['line_name'] = line_name
            ziru_data['stop_name'] = stop_name
            ziru_data['room_name'] = room_name
            ziru_data['square'] = float(square)
            ziru_data['direction'] = direction
            ziru_data['room_type'] = room_type
            ziru_data['floor'] = floor
            ziru_data['room_tran'] = room_tran
            ziru_data['room_tags_list'] = room_tags_list
            ziru_data['room_num'] = room_num
            ziru_data['room_around'] = room_around
            ziru_data['around_tran'] = around_tran
            ziru_data['deploy'] = deploy
            ziru_data['price'] = int(price)
            ziru_data['period'] = period
            ziru_data['room_url'] = response.url
            ziru_data['location'] = location
            ziru_data['loc_attr1'] = loc_attr1
            yield ziru_data
        
        
    def on_result(self,result):
        super(Handler, self).on_result(result)
        if not result:
            return
    
        client = pymongo.MongoClient(MONGODB_IP,MONGODB_PORT)
        db = client.research
        ziru_data = db.ziru_data
        room = {}
        if ziru_data.find_one({"room_num":result['room_num'],"price":result['price']}):
            pass
        else:
            # 当前时间
            now = datetime.datetime.now() # 这是数组时间格式
            now_time = now.strftime('%Y-%m-%d %H:%M:%S')
            now_time = time.strptime(now_time, "%Y-%m-%d %H:%M:%S")
            y,m,d,h,mm,s = now_time[0:6]
            #print y,m,d,h,mm,type(s)
            update_time = datetime.datetime(y,m,d,h,mm,s)

            result["insertime"] = update_time

            ziru_data.insert(result)


























        
       
