# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         chat_api.py
# Description:  
# Author:       xaoyaoo
# Date:         2024/01/02
# -------------------------------------------------------------------------------
import base64
import logging
import os
import time
import shutil

from flask import Flask, request, render_template, g, Blueprint, send_file, make_response, session,send_file
from pywxdump import analyzer, read_img_dat, read_audio, get_wechat_db, get_core_db
from pywxdump.api.rjson import ReJson, RqJson
from pywxdump.api.utils import read_session, save_session, error9999
from pywxdump import read_info, VERSION_LIST, batch_decrypt, BiasAddr, merge_db, decrypt_merge
import pywxdump

# app = Flask(__name__, static_folder='../ui/web/dist', static_url_path='/')

api = Blueprint('api', __name__, template_folder='../ui/web', static_folder='../ui/web/assets/', )
api.debug = False


@api.route('/api/init', methods=["GET", 'POST'])
@error9999
def init():
    """
    初始化 设置微信数据库路径，图片路径，解密需要的数据库
    :return:
    """
    msg_path = request.json.get("msg_path", "").strip()
    micro_path = request.json.get("micro_path", "").strip()
    media_path = request.json.get("media_path", "").strip()
    wx_path = request.json.get("wx_path", "").strip()
    key = request.json.get("key", "").strip()
    my_wxid = request.json.get("my_wxid", "").strip()
    if key:  # 如果key不为空，表示是解密模式
        if not wx_path:
            return ReJson(1002)
        if not os.path.exists(wx_path):
            return ReJson(1001, body=wx_path)
        save_msg_path = read_session(g.sf, "msg_path")
        save_micro_path = read_session(g.sf, "micro_path")
        save_my_wxid = read_session(g.sf, "my_wxid")
        if save_msg_path and save_micro_path and os.path.exists(save_msg_path) and os.path.exists(
                save_micro_path) and save_my_wxid == my_wxid:
            return ReJson(0, {"msg_path": save_msg_path, "micro_path": save_micro_path, "is_init": True})

        out_path = os.path.join(g.tmp_path, "decrypted", my_wxid) if my_wxid else os.path.join(g.tmp_path,
                                                                                               "decrypted")
        code, merge_save_path = decrypt_merge(wx_path=wx_path, key=key, outpath=out_path)
        time.sleep(1)
        if code:
            save_session(g.sf, "msg_path", merge_save_path)
            save_session(g.sf, "micro_path", merge_save_path)
            save_session(g.sf, "media_path", merge_save_path)
            save_session(g.sf, "wx_path", wx_path)
            save_session(g.sf, "key", key)
            save_session(g.sf, "my_wxid", my_wxid)
            rdata = {
                "msg_path": merge_save_path,
                "micro_path": merge_save_path,
                "media_path": merge_save_path,
                "wx_path": wx_path,
                "key": key,
                "my_wxid": my_wxid,
                "is_init": True,
            }
            return ReJson(0, rdata)
        else:
            return ReJson(2001, body=merge_save_path)

    else:
        if not msg_path or not micro_path or not media_path or not wx_path or not my_wxid:
            return ReJson(1002)
        if not os.path.exists(msg_path) or not os.path.exists(micro_path) or not os.path.exists(
                media_path) or not os.path.exists(wx_path):
            return ReJson(1001)

        save_session(g.sf, "msg_path", msg_path)
        save_session(g.sf, "micro_path", micro_path)
        save_session(g.sf, "media_path", media_path)
        save_session(g.sf, "wx_path", wx_path)
        save_session(g.sf, "key", "")
        save_session(g.sf, "my_wxid", my_wxid)

        rdata = {
            "msg_path": msg_path,
            "micro_path": micro_path,
            "media_path": media_path,
            "wx_path": wx_path,
            "key": "",
            "my_wxid": my_wxid,
            "is_init": True,
        }
        return ReJson(0, rdata)


@api.route('/api/version', methods=["GET", 'POST'])
@error9999
def version():
    """
    版本
    :return:
    """
    return ReJson(0, pywxdump.__version__)


@api.route('/api/contact_list', methods=["GET", 'POST'])
@error9999
def contact_list():
    """
    获取联系人列表
    :return:
    """
    # 获取联系人列表
    # 从header中读取micro_path
    micro_path = request.headers.get("micro_path")
    if not micro_path:
        micro_path = read_session(g.sf, "micro_path")
    start = request.json.get("start")
    limit = request.json.get("limit")

    contact_list = analyzer.get_contact_list(micro_path)
    save_session(g.sf, "user_list", contact_list)
    if limit:
        contact_list = contact_list[int(start):int(start) + int(limit)]
    return ReJson(0, contact_list)


@api.route('/api/chat_count', methods=["GET", 'POST'])
def chat_count():
    """
    获取联系人列表
    :return:
    """
    try:
        # 获取联系人列表
        # 从header中读取micro_path
        msg_path = request.headers.get("msg_path")
        if not msg_path:
            msg_path = read_session(g.sf, "msg_path")
        username = request.json.get("username", "")
        contact_list = analyzer.get_chat_count(msg_path, username)
        return ReJson(0, contact_list)
    except Exception as e:
        return ReJson(9999, msg=str(e))


@api.route('/api/contact_count_list', methods=["GET", 'POST'])
def contact_count_list():
    """
    获取联系人列表
    :return:
    """
    try:
        # 获取联系人列表
        # 从header中读取micro_path
        msg_path = request.headers.get("msg_path")
        micro_path = request.headers.get("micro_path")
        if not msg_path:
            msg_path = read_session(g.sf, "msg_path")
        if not micro_path:
            micro_path = read_session(g.sf, "micro_path")
        start = request.json.get("start")
        limit = request.json.get("limit")
        word = request.json.get("word", "")

        contact_list = analyzer.get_contact_list(micro_path)
        chat_count = analyzer.get_chat_count(msg_path)
        for contact in contact_list:
            contact["chat_count"] = chat_count.get(contact["username"], 0)
        # 去重
        contact_list = [dict(t) for t in {tuple(d.items()) for d in contact_list}]
        # 降序
        contact_list = sorted(contact_list, key=lambda x: x["chat_count"], reverse=True)

        save_session(g.sf, "user_list", contact_list)

        if word and word != "" and word != "undefined" and word != "null":
            contact_list = [contact for contact in contact_list if
                            word in contact["account"] or word in contact["describe"] or word in contact[
                                "nickname"] or word in contact["remark"] or word in contact["username"]]
        if limit:
            contact_list = contact_list[int(start):int(start) + int(limit)]
        return ReJson(0, contact_list)
    except Exception as e:
        return ReJson(9999, msg=str(e))


@api.route('/api/msgs', methods=["GET", 'POST'])
@error9999
def get_msgs():
    msg_path = request.headers.get("msg_path")
    micro_path = request.headers.get("micro_path")
    if not msg_path:
        msg_path = read_session(g.sf, "msg_path")
    if not micro_path:
        micro_path = read_session(g.sf, "micro_path")
    start = request.json.get("start")
    limit = request.json.get("limit")
    wxid = request.json.get("wxid")
    msg_list = analyzer.get_msg_list(msg_path, wxid, start_index=start, page_size=limit)
    # row_data = {"MsgSvrID": MsgSvrID, "type_name": type_name, "is_sender": IsSender, "talker": talker,
    #             "room_name": StrTalker, "content": content, "CreateTime": CreateTime}
    contact_list = analyzer.get_contact_list(micro_path)

    userlist = {}
    my_wxid = read_session(g.sf, "my_wxid")
    if wxid.endswith("@chatroom"):
        # 群聊
        talkers = [msg["talker"] for msg in msg_list] + [wxid, my_wxid]
        talkers = list(set(talkers))
        for user in contact_list:
            if user["username"] in talkers:
                userlist[user["username"]] = user
    else:
        # 单聊
        for user in contact_list:
            if user["username"] == wxid or user["username"] == my_wxid:
                userlist[user["username"]] = user
            if len(userlist) == 2:
                break

    return ReJson(0, {"msg_list": msg_list, "user_list": userlist, "my_wxid": my_wxid})


@api.route('/api/img', methods=["GET", 'POST'])
@error9999
def get_img():
    """
    获取图片
    :return:
    """
    img_path = request.args.get("img_path")
    img_path = request.json.get("img_path", img_path)
    if not img_path:
        return ReJson(1002)
    wx_path = read_session(g.sf, "wx_path")
    img_path_all = os.path.join(wx_path, img_path)
    if os.path.exists(img_path_all):
        fomt, md5, out_bytes = read_img_dat(img_path_all)
        out_bytes = base64.b64encode(out_bytes).decode("utf-8")
        out_bytes = f"data:{fomt};base64,{out_bytes}"
        return ReJson(0, out_bytes)
    else:
        return ReJson(1001, body=img_path_all)
    
@api.route('/api/video/<path:videoPath>', methods=["GET", 'POST'])
def get_video(videoPath):
    wx_path = read_session(g.sf, "wx_path")
    all_video_path =  os.path.join(wx_path, videoPath)
    if not os.path.exists(all_video_path):
        return ReJson(5002)
    return send_file(all_video_path)

@api.route('/api/audio/<path:savePath>', methods=["GET", 'POST'])
def get_audio(savePath):
    # savePath = request.args.get("savePath")
    # savePath = request.json.get("savePath", savePath)
    savePath = "audio/" + savePath  # 这个是从url中获取的
    MsgSvrID = savePath.split("_")[-1].replace(".wav", "")
    if not savePath:
        return ReJson(1002)
    media_path = read_session(g.sf, "media_path")
    wave_data = read_audio(MsgSvrID, is_wave=True, DB_PATH=media_path)
    if not wave_data:
        return ReJson(1001)
    # 判断savePath路径的文件夹是否存在
    savePath = os.path.join(g.tmp_path, savePath)
    if not os.path.exists(os.path.dirname(savePath)):
        os.makedirs(os.path.dirname(savePath))
    with open(savePath, "wb") as f:
        f.write(wave_data)
    return send_file(savePath)


# 导出聊天记录
@api.route('/api/export', methods=["GET", 'POST'])
@error9999
def export():
    """
    导出聊天记录
    :return:
    """
    export_type = request.json.get("export_type")
    start_time = request.json.get("start_time", 0)
    end_time = request.json.get("end_time", 0)
    chat_type = request.json.get("chat_type")
    username = request.json.get("username")
    wx_path = request.json.get("wx_path", read_session(g.sf, "wx_path"))
    key = request.json.get("key", read_session(g.sf, "key"))

    if not export_type or not isinstance(export_type, str):
        return ReJson(1002)

    # 导出路径
    outpath = os.path.join(g.tmp_path, "export", export_type)
    if not os.path.exists(outpath):
        os.makedirs(outpath)

    if export_type == "endb":  # 导出加密数据库
        # 获取微信文件夹路径
        if not wx_path:
            return ReJson(1002)
        if not os.path.exists(wx_path):
            return ReJson(1001, body=wx_path)

        # 分割wx_path的文件名和父目录
        code, wxdbpaths = get_core_db(wx_path)
        if not code:
            return ReJson(2001, body=wxdbpaths)

        for wxdb in wxdbpaths:
            # 复制wxdb->outpath, os.path.basename(wxdb)
            shutil.copy(wxdb, os.path.join(outpath, os.path.basename(wxdb)))
        return ReJson(0, body=outpath)

    elif export_type == "dedb":
        if isinstance(start_time, int) and isinstance(end_time, int):
            msg_path = read_session(g.sf, "msg_path")
            micro_path = read_session(g.sf, "micro_path")
            media_path = read_session(g.sf, "media_path")
            dbpaths = [msg_path, msg_path, micro_path]
            dbpaths = list(set(dbpaths))
            mergepath = merge_db(dbpaths, os.path.join(outpath, "merge.db"), start_time, end_time)
            return ReJson(0, body=mergepath)
            # if msg_path == media_path and msg_path == media_path:
            #     shutil.copy(msg_path, os.path.join(outpath, "merge.db"))
            #     return ReJson(0, body=msg_path)
            # else:
            #     dbpaths = [msg_path, msg_path, micro_path]
            #     dbpaths = list(set(dbpaths))
            #     mergepath = merge_db(dbpaths, os.path.join(outpath, "merge.db"), start_time,  end_time)
            #     return ReJson(0, body=mergepath)
        else:
            return ReJson(1002, body={"start_time": start_time, "end_time": end_time})

    elif export_type == "csv":
        outpath = os.path.join(outpath, username)
        if not os.path.exists(outpath):
            os.makedirs(outpath)
        code, ret = analyzer.export_csv(username, outpath, read_session(g.sf, "msg_path"))
        if code:
            return ReJson(0, ret)
        else:
            return ReJson(2001, body=ret)
    elif export_type == "json":
        outpath = os.path.join(outpath, username)
        if not os.path.exists(outpath):
            os.makedirs(outpath)
        code, ret = analyzer.export_json(username, outpath, read_session(g.sf, "msg_path"))
        if code:
            return ReJson(0, ret)
        else:
            return ReJson(2001, body=ret)
    elif export_type == "html":
        chat_type_tups = []
        for ct in chat_type:
            tup = analyzer.get_name_typeid(ct)
            if tup:
                chat_type_tups += tup
        if not chat_type_tups:
            return ReJson(1002)

    elif export_type == "pdf":
        pass
    elif export_type == "docx":
        pass
    else:
        return ReJson(1002)

    return ReJson(9999, "")


# 这部分为专业工具的api
@api.route('/api/wxinfo', methods=["GET", 'POST'])
@error9999
def get_wxinfo():
    """
    获取微信信息
    :return:
    """
    import pythoncom
    pythoncom.CoInitialize()
    wxinfos = read_info(VERSION_LIST)
    pythoncom.CoUninitialize()
    return ReJson(0, wxinfos)


@api.route('/api/decrypt', methods=["GET", 'POST'])
@error9999
def decrypt():
    """
    解密
    :return:
    """
    key = request.json.get("key")
    if not key:
        return ReJson(1002)
    wxdb_path = request.json.get("wxdbPath")
    if not wxdb_path:
        return ReJson(1002)
    out_path = request.json.get("outPath")
    if not out_path:
        out_path = g.tmp_path
    wxinfos = batch_decrypt(key, wxdb_path, out_path=out_path)
    return ReJson(0, str(wxinfos))


@api.route('/api/biasaddr', methods=["GET", 'POST'])
@error9999
def biasaddr():
    """
    BiasAddr
    :return:
    """
    mobile = request.json.get("mobile")
    name = request.json.get("name")
    account = request.json.get("account")
    key = request.json.get("key", "")
    wxdbPath = request.json.get("wxdbPath", "")
    if not mobile or not name or not account:
        return ReJson(1002)
    rdata = BiasAddr(account, mobile, name, key, wxdbPath).run()
    return ReJson(0, str(rdata))


@api.route('/api/merge', methods=["GET", 'POST'])
@error9999
def merge():
    """
    合并
    :return:
    """
    wxdb_path = request.json.get("dbPath")
    if not wxdb_path:
        return ReJson(1002)
    out_path = request.json.get("outPath")
    if not out_path:
        return ReJson(1002)
    rdata = merge_db(wxdb_path, out_path)
    return ReJson(0, str(rdata))


# END 这部分为专业工具的api


@api.route('/')
@error9999
def index():
    return render_template('index.html')
