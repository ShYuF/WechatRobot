# -*- coding: utf-8 -*-

import logging
import os
import re
import time
import yaml
import json
import xml.etree.ElementTree as ET
from queue import Empty
from threading import Thread
from base.func_zhipu import ZhiPu

from wcferry import Wcf, WxMsg

from base.func_bard import BardAssistant
from base.func_chatglm import ChatGLM
from base.func_chatgpt import ChatGPT
from base.func_chengyu import cy
from base.func_news import News
from base.func_tigerbot import TigerBot
from base.func_xinghuo_web import XinghuoWeb
from configuration import Config
from constants import ChatType
from job_mgmt import Job

import random
from base.func_weather import get_current_weather
from base.func_deadline import deadline
from base.func_alarm import WeatherAlarm

__version__ = "39.0.10.1"


class Robot(Job):
    """个性化自己的机器人
    """

    def __init__(self, config: Config, wcf: Wcf, roles: dict, keyword: str = "default") -> None:
        self.wcf = wcf
        self.config = config

        self.roles = roles.copy()
        self.keyword = keyword
        self.admin = ""
        self.ALARM = []

        self.lock = False
        
        self.LOG = logging.getLogger("Robot")
        self.wxid = self.wcf.get_self_wxid()
        self.allContacts = self.getAllContacts()

        with open(r"info\info.yaml", "r", encoding="utf-8") as file:
            info = yaml.safe_load(file.read())
            self.admin = info["admin"]
            self.ALARM = info["alarm"]
            file.close()

        self.alarm = WeatherAlarm()
        

        self.cmdMode = False
        self.emojiMode = False
        self.queryMode = False

        self.todoList: list = []

        with open(r"emoji\emoji.yaml", "r", encoding="utf-8") as file:
            emoji_info = yaml.safe_load(file.read())
            file.close()

        # print(emoji_info)

        self.local_path = os.getcwd()
        self.emoji_list: list = []
        for fileType in emoji_info["emojiType"]:
            if len(emoji_info[fileType]) > 0:
                tmp = [self.local_path + f"\emoji\{file}.{fileType}" for file in emoji_info[fileType]]
                self.emoji_list.extend(tmp)
        # print(self.emoji_list)

        def help(): self.sendTextMsg(
                    """命令列表:
                    \r$cmd: 进入命令模式（在命令模式下无效）
                    \r$exit: 退出命令模式
                    \r$lock: 锁定/解锁机器人
                    \r$reset: 重置机器人
                    \r$switch [role]: 切换角色
                    \r$emoji: 进入/退出表情模式
                    \r$emoji [-test]: 测试表情
                    \r$todo [-add] [content] / [-show] / [-del] [index]: 添加/查看/删除Todo List内容
                    \r$query: 开启/关闭查询功能""", self.admin)
        def lock(): 
            self.lock = not self.lock
            if self.lock:
                self.sendTextMsg("已锁定", self.admin)
            else:
                self.sendTextMsg("已解锁", self.admin)
        def reset(): 
            self.chat = ZhiPu(self.config.ZhiPu, self.roles.get(self.keyword, "default"))
            self.sendTextMsg(self.roles.get(self.keyword, "default")["greet"], self.admin)
        def switch(role: str = ""): 
            self.keyword = role if role in self.roles.keys() else "default"
            self.chat = ZhiPu(self.config.ZhiPu, self.roles.get(self.keyword, "default"))
            self.sendTextMsg(self.roles.get(self.keyword, "default")["greet"], self.admin)
        def emoji():
            self.emojiMode = not self.emojiMode
            if self.emojiMode:
                self.sendTextMsg("已开启表情模式", self.admin)
            else:
                self.sendTextMsg("已关闭表情模式", self.admin)
        def emojiTest():
            self.sendTextMsg("测试表情", self.admin)
            for emoji in self.emoji_list:
                self.wcf.send_emotion(emoji, self.admin)
        def todo(cmd: str = "show", args: str | int | None = None):
            self.todoList.clear()
            file = open(r"info\todo.json", "r", encoding="utf-8")
            self.todoList = json.load(file)["Todo"]
            file.close()
            if cmd == "add":
                if args == None:
                    self.sendTextMsg("请输入内容", self.admin)
                    return
                self.todoList.append(args)
                file = open(r"info\todo.json", "w", encoding="utf-8")
                json.dump({"Todo": self.todoList}, file, ensure_ascii=False)
                file.close()
                self.sendTextMsg(f"已添加", self.admin)
            elif cmd == "show":
                msg = "Todo List\n----------------\n"
                if len(self.todoList) == 0:
                    msg += "当前无事项\n"
                else:
                    for i, todo in enumerate(self.todoList):
                        msg += f"{i + 1}. {todo}\n"
                msg = msg.strip()
                self.sendTextMsg(msg, self.admin)
            elif cmd == "del":
                if args == None:
                    self.sendTextMsg("请输入序号", self.admin)
                    return
                if args > len(self.todoList) or args <= 0:
                    self.sendTextMsg("无效序号", self.admin)
                    return
                self.todoList.pop(args - 1)
                file = open(r"info\todo.json", "w", encoding="utf-8")
                json.dump({"Todo": self.todoList}, file, ensure_ascii=False)
                file.close()
                self.sendTextMsg(f"已删除", self.admin)
            else:
                self.sendTextMsg("无效命令", self.admin)
        def query():
            self.queryMode = not self.queryMode
            if self.queryMode:
                self.sendTextMsg("已开启查询功能", self.admin)
            else:
                self.sendTextMsg("已关闭查询功能", self.admin)

        self.cmd = {
            r"^\$help$": help,
            r"^\$lock$": lock,
            r"^\$reset$": reset,
            r"^\$switch (\w+)$": switch,
            r"^\$emoji$": emoji,
            r"^\$emoji -test$": emojiTest,
            r"^\$todo -(?:(add) (.+)|(show)|(del) (\d+))$": todo,
            r"^\$query$": query
        }

        self.chat = ZhiPu(
            self.config.ZhiPu,
            self.roles.get(self.keyword, "default")
        )

        self.LOG.info(f"已选择: {self.chat}")
        self.sendTextMsg(self.roles.get(self.keyword, "default")["greet"], self.admin)


    @staticmethod
    def value_check(args: dict) -> bool:
        if args:
            return all(value is not None for key, value in args.items() if key != 'proxy')
        return False


    def toAt(self, msg: WxMsg) -> bool:
        """处理被 @ 消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        return self.toChitchat(msg)


    # 考虑到ai的成语接龙效果已经基本满足使用，暂时禁用该函数
    def toChengyu(self, msg: WxMsg) -> bool:
        """
        处理成语查询/接龙消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        status = False
        texts = re.findall(r"^([#|?|？])(.*)$", msg.content)
        # [('#', '天天向上')]
        if texts:
            flag = texts[0][0]
            text = texts[0][1]
            if flag == "#":  # 接龙
                if cy.isChengyu(text):
                    rsp = cy.getNext(text)
                    if rsp:
                        self.sendTextMsg(rsp, msg.roomid)
                        status = True
            elif flag in ["?", "？"]:  # 查词
                if cy.isChengyu(text):
                    rsp = cy.getMeaning(text)
                    if rsp:
                        self.sendTextMsg(rsp, msg.roomid)
                        status = True

        return status

    def getRandomEmoji(self) -> str:
        emoji = random.choice(self.emoji_list)
        return emoji

    def toChitchat(self, msg: WxMsg) -> bool:
        """闲聊
        """
        #at: str = ""
        if not self.chat:  # 没接 ChatGPT，固定回复
            rsp = ""
        else:  # 接了 ChatGPT，智能回复
            q = re.sub(r"@.*?[\u2005|\s]", "", msg.content).strip()
            weather_pattern = r"^\$q (.+)天气$"
            if self.queryMode and re.match(weather_pattern, q) != None:
                    location = re.match(weather_pattern, q).group(1)
                    rsp = get_current_weather(
                        location=location,
                        special_error=self.roles.get(self.keyword, "default")["special_error"]
                    )
            # ddl功能暂时锁定
            # elif re.match("ddl\n(\d{10})\n(.+)", q) != None:
            #     mat = re.match("ddl\n(\d{10})\n(.+)", q)
            #     rsp = deadline(mat.group(1),
            #         mat.group(2),
            #         self.roles.get(self.keyword, "default")["special_ddl"],
            #         self.roles.get(self.keyword, "default")["special_error"]
            #     )
            else:
                #at = msg.sender if msg.is_at(self.wxid) else ""
                rsp = self.chat.get_answer(q, (msg.roomid if msg.from_group() else msg.sender))

        if rsp:
            if msg.from_group():
                # self.sendTextMsg(rsp, msg.roomid, msg.sender)
                self.sendTextMsg(rsp, msg.roomid)
                if self.emojiMode:
                    self.wcf.send_emotion(self.getRandomEmoji(), msg.roomid)
            else:
                self.sendTextMsg(rsp, msg.sender)
                if self.emojiMode:
                    self.wcf.send_emotion(self.getRandomEmoji(), msg.sender)

            return True
        else:
            self.LOG.error(f"无法获得答案")
            return False

    def processMsg(self, msg: WxMsg) -> None:
        """当接收到消息的时候，会调用本方法。如果不实现本方法，则打印原始消息。
        此处可进行自定义发送的内容,如通过 msg.content 关键字自动获取当前天气信息，并发送到对应的群组@发送者
        群号：msg.roomid  微信ID：msg.sender  消息内容：msg.content
        content = "xx天气信息为："
        receivers = msg.roomid
        self.sendTextMsg(content, receivers, msg.sender)
        """

        # 群聊消息
        if msg.from_group():
            # 如果在群里被 @
            if msg.roomid not in self.config.GROUPS:  # 不在配置的响应的群列表里，忽略
                return

            if msg.is_at(self.wxid):  # 被@
                self.toAt(msg)

            # else:  # 其他消息
            #     self.toChengyu(msg)

            return  # 处理完群聊信息，后面就不需要处理了

        # 非群聊信息，按消息类型进行处理
        # 不接受好友请求
        if msg.type == 37:  # 好友请求
            # self.autoAcceptFriendRequest(msg)

        # elif msg.type == 10000:  # 系统信息
            # self.sayHiToNewFriend(msg)
            pass

        elif msg.type == 0x01:  # 文本消息
            # 让配置加载更灵活，自己可以更新配置。也可以利用定时任务更新。
            if not msg.from_group():
                if msg.sender == self.admin:
                    if self.cmdMode == False and msg.content == r"$cmd":
                        self.cmdMode = True
                        self.sendTextMsg("进入命令模式", self.admin)
                    elif self.cmdMode == True and msg.content == r"$exit":
                        self.cmdMode = False
                        self.sendTextMsg("退出命令模式", self.admin)
                    elif self.cmdMode == True:
                        flag = False
                        for key, value in self.cmd.items():
                            if re.match(key, msg.content) != None:
                                flag = True
                                match = re.match(key, msg.content).groups()
                                if len(match) > 0:
                                    if len(match) == 5 and (match[0] == "add" or match[2] == "show" or match[3] == "del"):
                                        if match[0] == "add":
                                            value(*match[0:2])
                                        elif match[2] == "show":
                                            value(match[2])
                                        elif match[3] == "del":
                                            value(match[3], int(match[4]))
                                    else:
                                        value(*match)
                                else:
                                    value()
                        if not flag:
                            self.sendTextMsg("无效命令，输入$help以获取可用命令", self.admin)                        
                    else:
                        self.toChitchat(msg)
            else:
                if not self.lock:
                    self.toChitchat(msg)  # 闲聊


    def onMsg(self, msg: WxMsg) -> int:
        try:
            self.LOG.info(msg)  # 打印信息
            self.processMsg(msg)
        except Exception as e:
            self.LOG.error(e)

        return 0


    def enableRecvMsg(self) -> None:
        self.wcf.enable_recv_msg(self.onMsg)

    def enableReceivingMsg(self) -> None:
        def innerProcessMsg(wcf: Wcf):
            while wcf.is_receiving_msg():
                try:
                    msg = wcf.get_msg()
                    self.LOG.info(msg)
                    self.processMsg(msg)
                except Empty:
                    continue  # Empty message
                except Exception as e:
                    self.LOG.error(f"Receiving message error: {e}")

        self.wcf.enable_receiving_msg()
        Thread(target=innerProcessMsg, name="GetMessage", args=(self.wcf,), daemon=True).start()

    def sendTextMsg(self, msg: str, receiver: str, at_list: str = "") -> None:
        """ 发送消息
        :param msg: 消息字符串
        :param receiver: 接收人wxid或者群id
        :param at_list: 要@的wxid, @所有人的wxid为：notify@all
        """
        # msg 中需要有 @ 名单中一样数量的 @
        ats = ""
        if at_list:
            if at_list == "notify@all":  # @所有人
                ats = " @所有人"
            else:
                wxids = at_list.split(",")
                for wxid in wxids:
                    # 根据 wxid 查找群昵称
                    ats += f" @{self.wcf.get_alias_in_chatroom(wxid, receiver)}"

        # {msg}{ats} 表示要发送的消息内容后面紧跟@，例如 北京天气情况为：xxx @张三
        if ats == "":
            self.LOG.info(f"To {receiver}: {msg}")
            self.wcf.send_text(f"{msg}", receiver, at_list)
            # self.wcf.send_emotion("")
        else:
            self.LOG.info(f"To {receiver}: {ats}\r{msg}")
            self.wcf.send_text(f"{ats} {msg}", receiver, at_list)

    def getAllContacts(self) -> dict:
        """
        获取联系人（包括好友、公众号、服务号、群成员……）
        格式: {"wxid": "NickName"}
        """
        contacts = self.wcf.query_sql("MicroMsg.db", "SELECT UserName, NickName FROM Contact;")
        return {contact["UserName"]: contact["NickName"] for contact in contacts}

    def keepRunningAndBlockProcess(self) -> None:
        """
        保持机器人运行，不让进程退出
        """
        while True:
            self.runPendingJobs()
            time.sleep(1)

    def autoAcceptFriendRequest(self, msg: WxMsg) -> None:
        try:
            xml = ET.fromstring(msg.content)
            v3 = xml.attrib["encryptusername"]
            v4 = xml.attrib["ticket"]
            scene = int(xml.attrib["scene"])
            self.wcf.accept_new_friend(v3, v4, scene)

        except Exception as e:
            self.LOG.error(f"同意好友出错：{e}")

    def sayHiToNewFriend(self, msg: WxMsg) -> None:
        nickName = re.findall(r"你已添加了(.*)，现在可以开始聊天了。", msg.content)
        if nickName:
            # 添加了好友，更新好友列表
            self.allContacts[msg.sender] = nickName[0]
            self.sendTextMsg(f"Hi {nickName[0]}，我自动通过了你的好友请求。", msg.sender)

    def newsReport(self) -> None:
        receivers = self.config.NEWS
        if not receivers:
            return

        news = News().get_important_news()
        for r in receivers:
            self.sendTextMsg(news, r)
