"""
    DISCORD BOT
    需要提前创建DISCORD机器人，并获取token
    PandaBOT
    https://pandaxhff.cn
    UTF-8
"""

import requests
from datetime import datetime
import discord
from discord.ext import commands
from Config import *

# 定义意图
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

now = datetime.now()
now_time = now.strftime('%Y-%m-%d %H:%M:%S')

@bot.event
async def on_ready():
    print(f"已登录为 {bot.user}")

# 事件: 每次收到消息时打印消息数据
@bot.event
async def on_message(message):
    global message_content,sender_id,gid,message_id
    # 排除机器人的消息，以避免递归
    if message.author == bot.user:
        return
    if message.author.bot == True:
        return

    print("-----------------------------------")
    # print(message)
    print(f"内容: {message.content}")
    # if message.content:
    #     message_translate = translate(message.content,'zh')
    #     print(f"翻译：{message_translate}")
    print(f"发送者: {message.author}")
    print(f"发送者ID: {message.author.id}")
    if isinstance(message.channel, discord.DMChannel):
        print("该消息来自私聊")
    elif isinstance(message.channel, discord.TextChannel):
        print(f"频道: {message.channel}")
        print(f"消息所在频道的 ID: {message.channel.id}")
    print(f"消息ID: {message.id}")
    print(now.strftime("%Y-%m-%d %H:%M:%S"))
    # 存储消息信息到全局变量
    message_content = message.content
    sender_id = message.author.id
    gid = message.channel.id
    message_id = message.id
    if int(message.channel.id) == to_discord_channel:
        send_to_qq(message_content)


def send_to_qq(message, group_id=qq_group, ip=qq_ip):
    if ip == qq_ip:
        data = {
            'group_id': group_id,
            'message': message,
            'auto_escape': False,

        }
        url = f"http://{ip}:{port}/send_group_msg"
    else:
        data = {
            'group_id': group_id,
            'message': message,
            'keyword': qq_keyword,
            'auto_escape': False
        }
        url = f"http://{ip}:{to_port}/to_qq"
    res = requests.post(url, json=data)
    return res.json()



@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await bot.tree.sync()
    print("已成功同步指令到 Discord！")

# 启动机器人
bot.run(bot_token)