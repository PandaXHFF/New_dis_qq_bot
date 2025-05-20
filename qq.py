"""
    QQ机器人后端
    Flask框架
    PandaBOT
    https://pandaxhff.cn
    UTF-8
    支持 OneBotV11
"""

from flask import Flask, request ,jsonify
import json
import requests
from Config import *
import io
import base64
import time
import traceback

app = Flask(__name__)

@app.route('/to_dis', methods=['POST'])
def to_dis():
    data = request.get_json()
    self_id = data.get('self_id')
    # 检测来源
    if self_id != qq_bot_id:
        return jsonify({'error': 'Invalid qq'}), 400
    # 检测消息类型
    message_type = data.get('message_type')
    messages = data.get("message", [])
    if not messages or message_type != 'group':
        return jsonify({'code': '200'}), 200
    # 检测q群和避免递归
    sender_id = data.get('sender', {}).get('user_id')
    group_id = data['group_id']
    if int(group_id) != qq_group or sender_id == self_id:
        return jsonify({'code': '200'}), 200
    # 获取qq成员昵称
    card = data.get('sender', {}).get('card', '') or data.get('sender', {}).get('nickname', '')
    # message_id = data.get('message_id')

    image_count = 0
    embeds = []
    files = {}
    current_text = ""
    replied_block = ""

    # ==== 处理引用回复 ====
    if messages and messages[0].get("type") == "reply":
        reply_message_id = messages[0]["data"].get("id")
        get_message = get_msg(qq_ip, reply_message_id)
        reply_data = get_message.get("data", {})
        reply_sender = reply_data.get("sender", {})
        reply_user = reply_sender.get("card") or reply_sender.get("nickname") or f"QQ{reply_sender.get('user_id')}"
        reply_message_list = reply_data.get("message", [])

        reply_text = ""
        for i in reply_message_list:
            if i.get("type") == "text":
                reply_text += i["data"].get("text", "")
        reply_text = reply_text.strip()
        if reply_text:
            replied_block = f"**{reply_user}：**\n> {reply_text}\n\n\n"
        else:
            replied_block = f"**{reply_user}：**\n> ...\n\n\n"

    # ==== 解析消息 ====
    replied_used = False

    for item in messages:
        if item.get("type") == "text":
            current_text += item["data"].get("text", "")
        elif item.get("type") == "image" and image_count < 5:
            url = item["data"].get("url")
            try:
                base64_data = get_qq_http_image(url)
                if not base64_data:
                    continue
                image_data = base64.b64decode(base64_data)
                unix_timestamp = int(time.time())
                filename = f"{unix_timestamp}_{image_count}.jpg"
                files[f'file{image_count}'] = (filename, io.BytesIO(image_data), 'image/jpeg')

                embed = {}
                desc = current_text.strip()
                # 只在第一个图片embed插入回复引用，并标记为已用
                if image_count == 0 and replied_block:
                    desc = replied_block + desc
                    replied_used = True

                if desc:
                    embed["description"] = desc
                    current_text = ""

                embed["image"] = {"url": f"attachment://{filename}"}
                embeds.append(embed)
                image_count += 1
            except Exception as e:
                print(f"图片处理出错: {url}, 错误: {e}")

    # 发送剩余文本时，如果引用框还没用过，才加上
    if current_text.strip() or (replied_block and not replied_used):
        desc = ""
        if replied_block and not replied_used:
            desc += replied_block
        desc += current_text.strip()
        embeds.append({"description": desc})

    # ==== 发送到 Discord ====
    try:
        status_code = send_to_dis(embeds, card, sender_id, files)
        """
        204为发送文字成功
        200为发送文件成功
        429为请求过多
        """
        return jsonify({'code': '200'}),status_code
    except Exception as e:
        print("发送失败：", e)
        traceback.print_exc()
        return jsonify({'error': '发送到 Discord 失败', 'detail': str(e)}), 500


def send_to_dis(embeds, sender_name, sender_id, files=None):
    data = {
        "username": sender_name,
        "avatar_url": f"http://q.qlogo.cn/headimg_dl?dst_uin={sender_id}&spec=640&img_type=jpg",
        "embeds": embeds
    }
    if files:
        response = requests.post(webhook_url, data={"payload_json": json.dumps(data)}, files=files)
    else:
        response = requests.post(webhook_url, json=data)
    return response.status_code


def get_msg(sender_ip, message_id):
    url = f'http://{sender_ip}:{port}/get_msg'
    data = {
        'message_id': message_id
    }
    response = requests.post(url, json=data)
    return response.json()

def get_qq_http_image(url):
    url = url.replace("https://", "http://")
    response = requests.get(url)
    # 检查响应状态码
    if response.status_code == 200:
        # 将图片数据保存在内存中
        image_data = io.BytesIO(response.content)
        # 将图片转换为 base64 编码
        base64_image = base64.b64encode(image_data.getvalue()).decode('utf-8')
        return base64_image
    else:
        print("获取image失败",response.json())
        return None


@app.route('/to_qq', methods=['POST'])
def to_qq():
    data = request.get_json()
    qq_to_ip = data.get('sender_ip',None)
    message = data.get('message',None)
    group_id = data.get('group_id',None)
    keyword = data.get('keyword',None)
    if qq_keyword and keyword != qq_keyword:
        return jsonify({'error': 'Invalid keyword'}), 400
    if not qq_to_ip:
        qq_to_ip = qq_ip  # 默认值
    data = {
        'group_id': group_id,
        'message': message,
        'auto_escape': False
    }
    def post_message(ip):
        url = f"http://{ip}:{port}/send_group_msg"
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()  # 检查是否返回 HTTP 错误状态码
            return response
        except requests.exceptions.RequestException:
            return None

    res = post_message(qq_to_ip)
    return res.json()



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=to_port)