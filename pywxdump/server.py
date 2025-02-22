# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         server.py
# Description:  
# Author:       xaoyaoo
# Date:         2024/01/04
# -------------------------------------------------------------------------------
import os
import subprocess
import sys
import time


def start_falsk(merge_path="", msg_path="", micro_path="", media_path="", wx_path="", key="", my_wxid="", port=5000,
                online=False, debug=False,isopenBrowser=True):
    """
    启动flask
    :param merge_path:  合并后的数据库路径
    :param msg_path:  MSG.db 的路径
    :param micro_path:  MicroMsg.db 的路径
    :param media_path:  MediaMSG.db 的路径
    :param wx_path:  微信文件夹的路径（用于显示图片）
    :param key:  密钥
    :param my_wxid:  微信账号(本人微信id)
    :param port:  端口号
    :param online:  是否在线查看(局域网查看)
    :param debug:  是否开启debug模式
    :return:
    """
    tmp_path = os.path.join(os.getcwd(), "wxdump_tmp")  # 临时文件夹,用于存放图片等
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)
        print(f"[+] 创建临时文件夹：{tmp_path}")

    session_file = os.path.join(tmp_path, "session")  # 用于存放各种基础信息

    from flask import Flask, g
    from flask_cors import CORS
    from pywxdump.api import api, read_session, save_session
    import logging

    if merge_path:
        msg_path = merge_path
        micro_path = merge_path
        media_path = merge_path

    # 检查端口是否被占用
    if online:
        host = '0.0.0.0'
    else:
        host = "127.0.0.1"

    app = Flask(__name__, template_folder='./ui/web', static_folder='./ui/web/assets/', static_url_path='/assets/')

    # 设置超时时间为 1000 秒
    app.config['TIMEOUT'] = 1000
    app.secret_key = 'secret_key'

    app.logger.setLevel(logging.ERROR)

    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)  # 允许所有域名跨域

    @app.before_request
    def before_request():

        g.tmp_path = tmp_path  # 临时文件夹,用于存放图片等
        g.sf = session_file  # 用于存放各种基础信息

    if msg_path: save_session(session_file, "msg_path", msg_path)
    if micro_path: save_session(session_file, "micro_path", micro_path)
    if media_path: save_session(session_file, "media_path", media_path)
    if wx_path: save_session(session_file, "wx_path", wx_path)
    if key: save_session(session_file, "key", key)
    if my_wxid: save_session(session_file, "my_wxid", my_wxid)
    save_session(session_file, "test", my_wxid)

    app.register_blueprint(api)
    if isopenBrowser:
        try:
            # 自动打开浏览器
            url = f"http://127.0.0.1:{port}/"
            # 根据操作系统使用不同的命令打开默认浏览器
            if sys.platform.startswith('darwin'):  # macOS
                subprocess.call(['open', url])
            elif sys.platform.startswith('win'):  # Windows
                subprocess.call(['start', url], shell=True)
            elif sys.platform.startswith('linux'):  # Linux
                subprocess.call(['xdg-open', url])
            else:
                print("Unsupported platform, can't open browser automatically.")
        except Exception as e:
            pass

    def is_port_in_use(host, port):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
            except socket.error:
                return True
        return False

    if is_port_in_use(host, port):
        print(f"Port {port} is already in use. Choose a different port.")
        input("Press Enter to exit...")
    else:
        time.sleep(1)
        print("[+] 请使用浏览器访问 http://127.0.0.1:5000/ 查看聊天记录")
        app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    msg_path = r"****.db"
    micro_path = r"****.db"
    media_path = r"****.db"

    wx_path = r"****"
    my_wxid = "****"

    start_falsk(msg_path=msg_path, micro_path=micro_path, media_path=media_path, wx_path=wx_path, my_wxid=my_wxid,
                port=5000, online=False, debug=False)
