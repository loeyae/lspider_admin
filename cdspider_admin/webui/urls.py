#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import traceback
from flask import request, render_template, redirect, json, jsonify
try:
    import flask_login as login
except ImportError:
    from flask.ext import login
from .app import app
from .utils.page_class import page_obj
from cdspider.libs.utils import iterator2list


@app.route('/urls/list', methods=['GET'])
def urls_list():
    try:
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        tid=request.args.get('tid')
        task_obj = app.config.get('db')["TaskDB"]
        task_info = task_obj.get_detail(tid)
        if not tid or not task_info:
            return render_template('error.html', message="无效的任务")
        urls_obj = app.config.get('db')["UrlsDB"]
        keyword_count = urls_obj.count(where={'status': [urls_obj.STATUS_INIT, urls_obj.STATUS_ACTIVE],'tid': int(tid)})
        content = page_obj.page_list(current_page, keyword_count)
        urls_list = urls_obj.get_list(where={'status': [urls_obj.STATUS_INIT, urls_obj.STATUS_ACTIVE],'tid': int(
            tid)}, offset=(current_page-1) * hits, sort=[("uuid", -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/urls/list.html', urls_list=urls_list, app_config=app_config, content=content, pid=task_info['pid'], tid=tid, task_info=task_info)

@app.route('/urls/add', methods=['POST', 'GET'])
def urls_add():
    tid=request.args.get('tid')
    task_obj = app.config.get('db')['TaskDB']
    task_info = task_obj.get_detail(tid)
    if not tid or not task_info:
        return render_template('error.html', message="无效的任务")
    if request.method=='GET':
        listruledb = app.config.get('db')['ListRuleDB']
        listrule = listruledb.get_list({"tid": int(tid)})
        app_config = app.config.get('app_config')
        return render_template('/urls/add.html', app_config=app_config, task_info=task_info, rule_list=listrule,
                               tid=tid)
    else:
        try:
            title = request.form.get('title')
            ruleId = request.form.get("ruleId", 0)
            arr = request.form.get('url').split('\r\n')
            frequency = request.form.get('frequency')
            urls_obj = app.config.get('db')["UrlsDB"]
            for item in arr:
                l = item.split("|")
                dic = {
                    'title': title if len(l) < 2 else l[1],
                    'url': l[0],
                    'status': urls_obj.STATUS_INIT,
                    'pid': task_info['pid'],
                    'sid': task_info['sid'],
                    'tid': int(tid),
                    'ruleId': int(ruleId),
                    'frequency': frequency,
                    'ruleStatus': urls_obj.STATUS_INIT,
                }
                uid = urls_obj.insert(dic)
                if uid:
                    app.config['newtask']({'uid': uid, "mode": task_info['type']})
            return redirect('/urls/list?tid=%s' % tid)
        except Exception as e:
            app.logger.error(traceback.format_exc())
            return render_template('error.html', message="新增URL出错了")

@app.route('/urls/<int:id>/edit', methods=['POST', 'GET'])
def urls_update(id):
    urls_obj = app.config.get('db')["UrlsDB"]
    urls_info = urls_obj.get_detail(id)
    if not id or not urls_info:
        return render_template('error.html', message="无效的URL")
    tid = urls_info['tid']
    task_obj = app.config.get('db')["TaskDB"]
    task_info = task_obj.get_detail(tid)
    if request.method=='GET':
        listruledb = app.config.get('db')['ListRuleDB']
        listrule = listruledb.get_list({"tid": int(tid)})
        app_config = app.config.get('app_config')
        return render_template('/urls/update.html', rule_list=listrule, urls_info=urls_info, app_config=app_config,
                               task_info=task_info)
    else:
        try:
            dic = request.form.to_dict()
            title = dic.get('title')
            url = dic.get('url').strip()
            frequency = dic.get('frequency')
            ruleId = int(dic.get('ruleId', 0))
            urlsdb_obj = app.config.get('db')["UrlsDB"]
            ret=urlsdb_obj.update(id, {"title": title, "url": url, "ruleId": ruleId, "frequency": frequency,
                                       "updatetime": int(time.time()), "status": urlsdb_obj.STATUS_INIT})
            if ret:
                spidertask_obj = app.config.get('db')['SpiderTaskDB']
                spidertask_obj.update_many(task_info['type'], {"ulr": dic['url'], "frequency": frequency},
                {"uid": id})
                app.config['status'](
                    {'uid': id, "mode": task_info['type'],  "status": urlsdb_obj.STATUS_INIT})
            return redirect('/urls/list?tid=%s' % tid)
        except Exception as e:
            app.logger.error(traceback.format_exc())
            return render_template('error.html', message="编辑URL出错了")

@app.route('/urls/<int:id>/enable', methods=['GET'])
def urls_enable(id):
    try:
        urls_obj = app.config.get('db')["UrlsDB"]
        urls_info = urls_obj.get_detail(id)
        if not id or not urls_info:
            return jsonify({"status": 500, "message": "无效的URL", "error": "error"})
        ret=urls_obj.enable(id)
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/urls/enable', methods=['POST'])
def urls_list_enable():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        tid = request.form.get('tid')
        task_obj = app.config.get('db')["TaskDB"]
        task_info = task_obj.get_detail(tid)
        if not tid or not task_info:
            return jsonify({"status": 500, "message": "无效的任务", "error": ""})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        urls_obj = app.config.get('db')["UrlsDB"]
        url_list = urls_obj.get_list(where={'uid': arr, 'status': urls_obj.STATUS_DISABLE, 'tid': int(tid)})
        i = 0
        for item in iterator2list(url_list):
            ret=urls_obj.enable(item['uuid'])
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/urls/<int:id>/delete', methods=['GET'])
def urls_delete(id):
    try:
        urls_obj = app.config.get('db')["UrlsDB"]
        urls_info = urls_obj.get_detail(id)
        if not id or not urls_info:
            return jsonify({"status": 500, "message": "无效的URL", "error": "error"})
        ret=urls_obj.delete(id)
        if ret:
            task_obj = app.config.get('db')["TaskDB"]
            task_info = task_obj.get_detail(urls_info['tid'])
            app.config['status'](
                {'uid': id, 'mode': task_info['type'], "status": urls_obj.STATUS_DELETED})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/urls/delete', methods=['POST'])
def urls_list_delete():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        tid = request.form.get('tid')
        task_obj = app.config.get('db')["TaskDB"]
        task_info = task_obj.get_detail(tid)
        if not tid or not task_info:
            return jsonify({"status": 500, "message": "无效的任务", "error": ""})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        urls_obj = app.config.get('db')["UrlsDB"]
        url_list = urls_obj.get_list(where={'uid': arr, 'status': [urls_obj.STATUS_INIT, urls_obj.STATUS_ACTIVE, urls_obj.STATUS_DISABLE], 'tid': int(tid)})
        i = 0
        for item in iterator2list(url_list):
            ret=urls_obj.delete(item['uuid'])
            if ret:
                app.config['status'](
                    {'uid': item['uuid'],  'mode': task_info['type'], "status": urls_obj.STATUS_DELETED})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/urls/<int:id>/disable', methods=['GET'])
def urls_disable(id):
    try:
        urls_obj = app.config.get('db')["UrlsDB"]
        urls_info = urls_obj.get_detail(id)
        if not id or not urls_info:
            return jsonify({"status": 500, "message": "无效的URL", "error": "error"})
        task_obj = app.config.get('db')["TaskDB"]
        task_info = task_obj.get_detail(urls_info['tid'])
        ret=urls_obj.disable(id)
        if ret:
            app.config['status'](
                {'uid': id, 'mode': task_info['type'], "status": urls_obj.STATUS_DISABLE})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/urls/disable', methods=['POST'])
def urls_list_disable():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        tid = request.form.get('tid')
        task_obj = app.config.get('db')["TaskDB"]
        task_info = task_obj.get_detail(tid)
        if not tid or not task_info:
            return jsonify({"status": 500, "message": "无效的任务", "error": ""})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        urls_obj = app.config.get('db')["UrlsDB"]
        url_list = urls_obj.get_list(where={'uid': arr, 'status': [urls_obj.STATUS_INIT, urls_obj.STATUS_ACTIVE], 'tid': int(tid)})
        i = 0
        for item in iterator2list(url_list):
            ret=urls_obj.disable(item['uuid'])
            if ret:
                app.config['status'](
                    {'uid': item['uuid'], 'mode': task_info['type'], "status": urls_obj.STATUS_DISABLE})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/urls/<int:id>/active/rule', methods=['GET'])
def urls_active_rule(id):
    try:
        urls_obj = app.config.get('db')["UrlsDB"]
        urls_info = urls_obj.get_detail(id)
        if not id or not urls_info:
            return jsonify({"status": 500, "message": "无效的URL", "error": "error"})
        rule_obj = app.config.get('db')["ListRuleDB"]
        rule_info = rule_obj.get_detail(urls_info["ruleId"])
        if not id or not rule_info:
            return jsonify({"status": 500, "message": "无效的规则", "error": "error"})
        if rule_info['status'] != rule_obj.STATUS_ACTIVE:
            return jsonify({"status": 500, "message": "请先激活规则", "error": "error"})
        ret=urls_obj.active_rule(id)
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/urls/active/rule', methods=['POST'])
def urls_list_active_rule():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        urls_obj = app.config.get('db')["UrlsDB"]
        url_list = urls_obj.get_list(where={'uid': arr, 'ruleStatus': urls_obj.STATUS_INIT})
        rule_obj = app.config.get('db')["ListRuleDB"]
        rule_dict = {}
        i = 0
        for item in iterator2list(url_list):
            rule = rule_dict.get(str(item['ruleId']))
            if not rule:
                rule = rule_obj.get_detail(item['ruleId'])
                rule_dict.update({str(item['ruleId']), rule})
            if not rule or rule.get('status') != rule_obj.STATUS_ACTIVE:
                continue
            ret=urls_obj.active_rule(item['uuid'])
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/urls/<int:id>/active', methods=['GET'])
def urls_active(id):
    try:
        urls_obj = app.config.get('db')["UrlsDB"]
        urls_info = urls_obj.get_detail(id)
        if not id or not urls_info:
            return jsonify({"status": 500, "message": "无效的URL", "error": "error"})
        task_obj = app.config.get('db')["TaskDB"]
        task_info = task_obj.get_detail(urls_info['tid'])
        if not task_info:
            return jsonify({"status": 500, "message": "无效的任务", "error": "error"})
        if task_info['status'] != task_obj.STATUS_ACTIVE:
            return jsonify({"status": 500, "message": "请先激活任务", "error": "error"})
        if urls_info['ruleStatus'] != urls_obj.STATUS_ACTIVE:
            return jsonify({"status": 500, "message": "规则未验证通过", "error": "error"})
        ret=urls_obj.active(id)
        if ret:
            app.config['status'](
                {'uid': id, 'mode': task_info['type'], "status": urls_obj.STATUS_ACTIVE})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/urls/active', methods=['POST'])
def urls_list_active():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        tid = request.form.get('tid')
        task_obj = app.config.get('db')["TaskDB"]
        task_info = task_obj.get_detail(tid)
        if not tid or not task_info:
            return jsonify({"status": 500, "message": "无效的任务", "error": ""})
        if task_info['status'] != task_obj.STATUS_ACTIVE:
            return jsonify({"status": 500, "message": "请先激活任务", "error": "error"})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        urls_obj = app.config.get('db')["UrlsDB"]
        url_list = urls_obj.get_list(where={'uid': arr, 'status': urls_obj.STATUS_INIT, 'ruleStatus': urls_obj.STATUS_ACTIVE, 'tid': int(tid)})
        i = 0
        for item in iterator2list(url_list):
            ret=urls_obj.active(item['uuid'])
            if ret:
                app.config['status'](
                    {'uid': item['uuid'], 'mode': task_info['type'], "status": urls_obj.STATUS_ACTIVE})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/urls/dis', methods=['GET'])
def urls_disable_list():
    try:
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        tid = request.args.get('tid')
        task_obj = app.config.get('db')["TaskDB"]
        task_info = task_obj.get_detail(tid)
        if not tid or not task_info:
            return render_template('error.html', message="无效的任务")
        urls_obj = app.config.get('db')["UrlsDB"]
        urls_count = urls_obj.count(where={'status': urls_obj.STATUS_DISABLE, 'tid': int(tid)})
        content = page_obj.page_list(current_page, urls_count)
        urls_list = urls_obj.get_list(where={'status': urls_obj.STATUS_DISABLE, 'tid': int(tid)}, offset=(current_page-1) * hits, sort=[("uid", -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/urls/disabled.html', app_config=app_config, task_info=task_info, urls_list=urls_list, content=content)
