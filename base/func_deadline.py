# -*- coding: utf-8 -*-
import os
import re
import json
import time

from faker import Faker as Fk
from bs4 import BeautifulSoup

import urllib3
from urllib3.util.ssl_ import create_urllib3_context

from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium import webdriver as driver

# 部分源码修改自Github开源项目learn2018-autodown，进行了修改重构
URL = "https://learn.tsinghua.edu.cn"
URL_LOGIN = "https://id.tsinghua.edu.cn/do/off/ui/auth/login/post/bb5df85216504820be7bba2b0ae1535b/0?/login.do"
URL_CURRENT_SEMESTER = "https://learn.tsinghua.edu.cn/f/wlxt/index/course/student/"

user_agent = Fk().user_agent()
headers = {"User-Agent": user_agent}

ctx = create_urllib3_context()
ctx.load_default_certs()
ctx.options |= 0x4  # ssl.OP_LEGACY_SERVER_CONNECT
http = urllib3.PoolManager(ssl_context=ctx)


def login(user_id, user_password):
    if user_id != None and user_password != None:
        params = {
            "i_user": user_id,
            "i_pass": user_password,
            "atOnce": "true",
        }

        try:
            response = http.request(
                method="POST", url=URL_LOGIN, fields=params, headers=headers
            )
            return [True, response.data.decode("utf-8")]
        except:
            return [False]
    else:
        return [False]


# 尝试从网络学堂获取ddl？
def deadline(account: str, pwd: str, special_ddl: str, special_error: str) -> str:
    # 尝试登录
    info = "学号：" + account + "\n"

    success = login(user_id=account, user_password=pwd)
    if success[0]:
        soup = BeautifulSoup(success[1], "html.parser")
        url_learn = soup.find("div", attrs={"class": "wrapper"}).find("a").attrs["href"]
        # print(url_learn)

        # 非通用方案
        service = Service(executable_path=r"C:\Program Files\Mozilla Firefox\geckodriver.exe")
        options = driver.FirefoxOptions()

        dri = driver.Firefox(service=service, options=options)
        time.sleep(5)
        dri.get(url_learn)
        dri.implicitly_wait(20)
        time.sleep(1)

        soup = BeautifulSoup(dri.page_source, "html.parser")

        # 尝试获取ddl
        ddl = []

        current_semester = soup.find("div", attrs={"id": "course1"})
        courses = current_semester.find("div", attrs={"id": "selfcourse"})
        for item in courses.find_all("div", attrs={"class": "item"}):
            home = item.find("ul", attrs={"class": "state stu clearfix"}).find_all(
                "li"
            )[2]
            home_cnt = int(home.find("span", attrs={"class": "zyundo"}).text)
            # print(home_cnt)

            if home_cnt > 0:
                course_name = item.find("a", attrs={"class": "title"}).text
                ddl_list = []

                uri = home.find("a").attrs["href"]
                dri.get(URL + uri)
                dri.implicitly_wait(20)
                time.sleep(1)

                course_soup = BeautifulSoup(dri.page_source, "html.parser")
                table = course_soup.find(
                    "table",
                    attrs={"id": "wtj", "class": "dataTable no-footer", "role": "grid"},
                )

                for undo_home in table.find("tbody").find_all("tr"):
                    rest_time_str = undo_home.find(
                        "td", attrs={"class": "sorting_2"}
                    ).text
                    if rest_time_str != r"已过期":
                        rest_time = re.match(
                            r"剩余(\d+)天|剩余(\dd):(\dd):(\dd)", rest_time_str
                        )
                        home_name = undo_home.find("a", attrs={"class": "col2"}).text
                        if rest_time_str[-1] == r"天":
                            if int(rest_time.group(1)) < 5:
                                ddl_list.append(
                                    r"- " + home_name + r"：剩余" + rest_time.group(1) + r"天"
                                )
                        else:
                            ddl_list.append(
                                r"- " +
                                home_name
                                + r"：剩余"
                                + rest_time.group(1)
                                + r"时"
                                + rest_time.group(2)
                                + r"分"
                            )

                if len(ddl_list) > 0:
                    ddl.append((course_name, ddl_list))

        dri.close()

        if len(ddl) > 0:
            home_info = ""
            for course in ddl:
                home_info += str(course[0]) + "：\n"
                for homework in course[1]:
                    home_info += homework + "\n"

            home_info = home_info.rstrip("\n")
            return info + home_info
        else:
            return info + special_ddl
    else:
        return special_error
