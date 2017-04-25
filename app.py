import re
import shutil

import requests
import json

import itchat
from itchat.content import *
from config import id_secrets


last_id = ''
last_path = ''
last_user = ''


@itchat.msg_register([TEXT, SHARING])
def simple_reply(msg):
    global last_id, last_path, last_user

    if 'Content' in msg:
        result = re.search('<pagepath><!\[CDATA\[([0-9A-Za-z/.?=]+)]]></pagepath>', msg['Content'])
        test = re.search('<pkginfo>[\r\n\s]*<type>([1-2])</type>', msg['Content'])
        if result:
            path = result.group(1).replace('.html', '')
            reply = '[自动回复] 小程序页面路径: \n' + path
            if test:
                reply += '\n! 该小程序为开发或测试版本，页面可能与线上版本不一致，请慎用。'

            appid = re.search('<appid><!\[CDATA\[([0-9WwXxA-Fa-f]+)]]></appid>', msg['Content'])
            if appid:
                appid = appid.group(1)
                if appid in id_secrets:
                    reply += '\n! 检测到小程序管理权限，回复2可生成该页面二维码。带参二维码只有 10w 个，请谨慎调用。'

                    last_path = path
                    last_id = appid
                    last_user = msg['FromUserName']

            reply += '\n[MinaDog机器人]'
            itchat.send(reply, msg['FromUserName'])

        elif msg['FromUserName'] == last_user:
            if msg['Content'].strip() == '2' and last_id != '' and last_path != '':
                generate_qrcode(last_id, last_path, last_user)
                last_id = ''
                last_path = ''
                last_user = ''
            else:
                last_id = ''
                last_path = ''
                last_user = ''


def generate_qrcode(appid, path, sendto):
    itchat.send('[自动回复] 正在生成二维码…\n[MinaDog机器人]', sendto)
    secret = id_secrets[appid]
    request = requests.get('https://api.weixin.qq.com/cgi-bin/token' +
                           '?grant_type=client_credential' +
                           '&appid=' + appid +
                           '&secret=' + secret)
    token = json.loads(request.content)
    if 'access_token' not in token:
        itchat.send('[自动回复] 获取 access_token 失败，请检查 AppSecret 是否有效。\n[MinaDog机器人]', sendto)
        return
    token = token['access_token']

    request = requests.post('https://api.weixin.qq.com/wxa/getwxacode?access_token=' + token, json={
        'path': path,
        'width': 1200
    }, stream=True)
    f = open('qrcode.jpg', 'wb')
    shutil.copyfileobj(request.raw, f)
    f.close()
    del request

    itchat.send_image('qrcode.jpg', sendto)


itchat.auto_login()

itchat.run()