# -*- coding: utf-8 -*-

import re
import json
import requests as req
from faker import Faker as Fk

# 北京天气
def weather(special_error: str) -> str:
    # 当日天气
    url = "https://weather.cma.cn/api/jingdian/weather?pcode=ABJ"
    headers = {"User-Agent" : Fk().user_agent()}
    params = {}
    report = ""
    try:
        r = req.get(url=url, headers=headers) 
        dict = json.loads(r.text)
        r.close()

        data = dict["data"][0]
        weather = data["weather"]

        date_group = re.match(pattern=r"(\d{4})/(\d{2})/(\d{2})", string=weather["date"])

        year = date_group.group(1)
        month = date_group.group(2).lstrip("0")
        day = date_group.group(3).lstrip("0")

        date = year + "年" + month + "月" + day + "日"
        
        # 实时天气
        url_now = "https://weather.cma.cn/api/now/54511"
        r_now = req.get(url=url_now, headers=headers) 
        dict_now = json.loads(r_now.text)
        r_now.close()

        data_now = dict_now["data"]["now"]

        date_group_now = re.match(pattern=r"(\d{4})/(\d{2})/(\d{2}) (\d{2}:\d{2})", string=dict_now["data"]["lastUpdate"])
        year_now = date_group_now.group(1)
        month_now = date_group_now.group(2).lstrip("0")
        day_now = date_group_now.group(3).lstrip("0")
        time_now = date_group_now.group(4)
        date_now = year_now + "年" + month_now + "月" + day_now + "日 " + time_now
        
        # 汇总报告
        report = date + " 北京天气\n" \
        + "---白天---\n最高气温：" \
        + str(weather["high"]) + "℃\n天气：" + weather["dayText"] + "\n风向：" + weather["dayWindDirection"] \
        + "\n风力：" + weather["dayWindScale"].replace("~", "-") \
        + "\n---夜晚---\n最低气温：" + str(weather["low"]) \
        + "℃\n天气：" + weather["nightText"] + "\n风向：" + weather["nightWindDirection"] \
        + "\n风力：" + weather["nightWindScale"].replace("~", "-") \
        + "\n---实时天气---\n更新时间：" + date_now \
        + "\n降水：" + str(data_now["precipitation"]) + "mm\n温度：" + str(data_now["temperature"]) \
        + "℃\n气压：" + str(data_now["pressure"]) + "hPa\n湿度：" + str(data_now["humidity"]) \
        + "%\n风向：" + data_now["windDirection"] + "\n风速：" + str(data_now["windSpeed"]) \
        + "m/s\n风力：" + data_now["windScale"].replace("~", "-")
    except:
        report = special_error
    return report
