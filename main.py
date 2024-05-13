#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import yaml
import signal
from argparse import ArgumentParser

from base.func_report_reminder import ReportReminder
from configuration import Config
from constants import ChatType
from robot import Robot, __version__
from wcferry import Wcf

from base.func_weather import weather

role_info_path = r"info\roles.yaml"
file = open(role_info_path, "r", encoding="utf-8")
roles = yaml.safe_load(file.read())
file.close()

key_info_path = r"info\ddlkey.yaml"
file_d = open(key_info_path, "r", encoding="utf-8")
ddlkey = yaml.safe_load(file_d.read())
file_d.close()

keyword = "dog"
role = roles[keyword]


def weather_report(robot: Robot) -> None:
    # 获取接收人
    receivers = ["wxid_bslrmqx7wofq22"]

    report = weather(robot.role["special_error"])

    for r in receivers:
        robot.sendTextMsg(report, r)
        # robot.sendTextMsg(report, r, "notify@all")   # 发送消息并@所有人


def main(chat_type: int):
    config = Config()
    wcf = Wcf(debug=True)

    def handler(sig, frame):
        wcf.cleanup()  # 退出前清理环境
        exit(0)

    signal.signal(signal.SIGINT, handler)

    robot = Robot(config, wcf, chat_type, role, ddlkey)
    robot.LOG.info(f"WeChatRobot【{__version__}】成功启动···")

    # 机器人启动发送测试消息
    robot.sendTextMsg("机器人启动成功！", "filehelper")
    robot.sendTextMsg(role["greet"], "wxid_bslrmqx7wofq22")
    # 接收消息
    # robot.enableRecvMsg()     # 可能会丢消息？
    robot.enableReceivingMsg()  # 加队列

    # 每天 7 点发送天气预报
    robot.onEveryTime("07:00", weather_report, robot=robot)

    # 每天 7:30 发送新闻
    # robot.onEveryTime("07:30", robot.newsReport)

    # 每天 16:30 提醒发日报周报月报
    # robot.onEveryTime("16:30", ReportReminder.remind, robot=robot)

    # 让机器人一直跑
    robot.keepRunningAndBlockProcess()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-c', type=int, default=0, help=f'选择模型参数序号: {ChatType.help_hint()}')
    args = parser.parse_args().c
    main(args)
