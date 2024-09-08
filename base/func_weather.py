# -*- coding: utf-8 -*-

import re
import json
import requests as req

# 北京天气
# def weather(special_error: str) -> str:
#     # 当日天气
#     url = "https://weather.cma.cn/api/jingdian/weather?pcode=ABJ"
#     headers = {"User-Agent" : Fk().user_agent()}
#     params = {}
#     report = ""
#     try:
#         r = req.get(url=url, headers=headers) 
#         dict = json.loads(r.text)
#         r.close()

#         data = dict["data"][0]
#         weather = data["weather"]

#         date_group = re.match(pattern=r"(\d{4})/(\d{2})/(\d{2})", string=weather["date"])

#         year = date_group.group(1)
#         month = date_group.group(2).lstrip("0")
#         day = date_group.group(3).lstrip("0")

#         date = year + "年" + month + "月" + day + "日"
        
#         # 实时天气
#         url_now = "https://weather.cma.cn/api/now/54511"
#         r_now = req.get(url=url_now, headers=headers) 
#         dict_now = json.loads(r_now.text)
#         r_now.close()

#         data_now = dict_now["data"]["now"]

#         date_group_now = re.match(pattern=r"(\d{4})/(\d{2})/(\d{2}) (\d{2}:\d{2})", string=dict_now["data"]["lastUpdate"])
#         year_now = date_group_now.group(1)
#         month_now = date_group_now.group(2).lstrip("0")
#         day_now = date_group_now.group(3).lstrip("0")
#         time_now = date_group_now.group(4)
#         date_now = year_now + "年" + month_now + "月" + day_now + "日 " + time_now
        
#         # 汇总报告
#         report = date + " 北京天气\n" \
#         + "---白天---\n最高气温：" \
#         + str(weather["high"]) + "℃\n天气：" + weather["dayText"] + "\n风向：" + weather["dayWindDirection"] \
#         + "\n风力：" + weather["dayWindScale"].replace("~", "-") \
#         + "\n---夜晚---\n最低气温：" + str(weather["low"]) \
#         + "℃\n天气：" + weather["nightText"] + "\n风向：" + weather["nightWindDirection"] \
#         + "\n风力：" + weather["nightWindScale"].replace("~", "-") \
#         + "\n---实时天气---\n更新时间：" + date_now \
#         + "\n降水：" + str(data_now["precipitation"]) + "mm\n温度：" + str(data_now["temperature"]) \
#         + "℃\n气压：" + str(data_now["pressure"]) + "hPa\n湿度：" + str(data_now["humidity"]) \
#         + "%\n风向：" + data_now["windDirection"] + "\n风速：" + str(data_now["windSpeed"]) \
#         + "m/s\n风力：" + data_now["windScale"].replace("~", "-")
#     except:
#         report = special_error
#     return report


def lookup_location_id(location: str, special_error: str) -> dict:
    # URL: https://geoapi.qweather.com/v2/city/lookup?
    # method: GET
    # params: location： 城市名，支持文字、以英文逗号分隔的经度,纬度坐标（十进制，最多支持小数点后两位），支持模糊搜索
    try:
        url = "https://geoapi.qweather.com/v2/city/lookup?"
        params = {
            "location": location,
            "key": "c52560aa29ee43819e0c10b2f65c7093"
        }
        response = req.get(url=url, params=params)
        data = response.json()

        if data["code"] == "200":
            return {"name": data["location"][0]["name"], "id": data["location"][0]["id"]}
        else:
            raise Exception("error")
    except:
        return "error"
        return special_error


def get_current_weather(location: str, special_error: str) -> str:
    # URL: https://devapi.qweather.com/v7/weather/now?
    # method: GET
    # params: location, key
    try:
        
        data = lookup_location_id(location=location, special_error=special_error)
        name = data["name"]
        loc = data["id"]
        url = "https://devapi.qweather.com/v7/weather/now"
        params = {
            "location": loc,
            "key": "c52560aa29ee43819e0c10b2f65c7093"
        }

        response = req.get(url=url, params=params)
        data = response.json()

        if data["code"] == "200":
            time_pattern = r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})[+-](?:\d{4}|\d{2}:\d{2})"
            date_group = re.match(pattern=time_pattern, string=data["updateTime"])
            update_time = date_group.group(1) + "年" + date_group.group(2) + "月" + date_group.group(3) + "日 " \
                        + date_group.group(4) + ":" + date_group.group(5) # 更新时间
            temperature = data["now"]["temp"] # 温度
            feelsLike = data["now"]["feelsLike"] # 体感温度
            text = data["now"]["text"] # 天气描述
            humidity = data["now"]["humidity"] # 相对湿度，百分比数值
            windScale = data["now"]["windScale"] # 风力等级
            weather_info = f"{update_time} {name}天气\n温度：{temperature}℃\n体感温度：{feelsLike}℃\n" \
                        + f"天气：{text}\n相对湿度：{humidity}%\n风力等级：{windScale}\n" \
                        + f"*查询地点匹配可能出现误差，注意核对"
            return weather_info
        else:
            raise Exception("error")
    except:
        return special_error
    
if __name__ == "__main__":
    weather_pattern = r"\$q (.+)天气"
    text = "$q 海淀天气"
    q = re.match(pattern=weather_pattern, string=text).group(1)
    print(get_current_weather(q, "error occurred in get_current_weather"))