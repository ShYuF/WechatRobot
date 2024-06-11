# -*- coding: utf-8 -*-

import re
import json
import requests as req
from faker import Faker as Fk

class WeatherAlarm:
    '''
    天气紧急预警
    '''

    TEST = "测试"

    # interval: int = 10, 检查间隔时间，默认为10分钟
    def __init__(self, interval: int = 10):
        self.id_list = []
        self.interval = interval
        self.ticks = 0

    # 更新时间
    # tick: int, 更新时间刻
    # special_error: str, 查询失败时的特殊报告
    def update(self, tick: int, special_error: str, area: str = "海淀区") -> str:
        if tick == None:
            return "error"
        self.ticks += tick
        
        if self.ticks >= self.interval:
            self.ticks = 0
            return self.alarm(special_error=special_error, area=area)
        
        return ""

    # 海淀天气预警
    # special_error: 查询失败时的特殊报告
    # area: 预警地区，默认为北京市海淀区
    def alarm(self, special_error: str = "查询失败", area: str = "海淀区") -> str:
        url = "https://weather.cma.cn/api/map/alarm?adcode=11"
        headers = {"User-Agent" : Fk().user_agent()}
        params = {}
        report = ""
        try:
            r = req.get(url=url, headers=headers) 
            dic = json.loads(r.text)
            r.close()

            msg = dic["msg"]
            if msg != "success":
                return "error"
            
            data_list = dic["data"]
            
            for data in data_list:
                title = data["title"]

                if area != WeatherAlarm.TEST:
                    judge = re.match(r"北京市" + area, title)
                    if judge == None:
                        continue
                
                # 判断是否已经发布过
                id = data["id"]
                if id in self.id_list:
                    continue
                if area != WeatherAlarm.TEST:
                    self.id_list.append(id)

                # 预警发布时间
                time_group = re.match(pattern=r"(\d{4})/(\d{2})/(\d{2}) (\d{2}:\d{2})",string=data["effective"])
                year = time_group.group(1)
                month = time_group.group(2).lstrip("0")
                day = time_group.group(3).lstrip("0")
                time = time_group.group(4)
                effective = year + "年" + month + "月" + day + "日 " + time

                # 预警内容
                description = data["description"]
                
                report += "发布时间：" + effective + "\n" + description + "\n"
        except:
            report = "error"
        finally:
            return report
        
    # 检查预警
    def test(self, area: str = TEST) -> str:
        return self.alarm("查询失败", area)
    

# if __name__ == "__main__":
#     alarm = WeatherAlarm()
#     print(alarm.test(r"怀柔区"))
