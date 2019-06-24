# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2019/6/23 8:41
"""
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
from .utils.form_data_format import build_rule_data, build_form_data


@app.route('/rule/list', methods=['GET'])
def rule_list():
    try:
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        tid=request.args.get('tid')
        task_obj = app.config.get('db')["TaskDB"]
        task_info = task_obj.get_detail(tid)
        if not tid or not task_info:
            return render_template('error.html', message="无效的任务")
        rule_obj = app.config.get('db')["ListRuleDB"]
        keyword_count = rule_obj.count(where={'status': [rule_obj.STATUS_INIT, rule_obj.STATUS_ACTIVE],'tid': int(tid)})
        content = page_obj.page_list(current_page, keyword_count)
        rule_list = rule_obj.get_list(where={'status': [rule_obj.STATUS_INIT, rule_obj.STATUS_ACTIVE],'tid': int(
            tid)}, offset=(current_page-1) * hits, sort=[("uuid", -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/rule/list.html', rule_list=rule_list, app_config=app_config, content=content, pid=task_info['pid'], tid=tid, task_info=task_info)

@app.route('/rule/add', methods=['POST', 'GET'])
def rule_add():
    tid=request.args.get('tid')
    task_obj = app.config.get('db')['TaskDB']
    task_info = task_obj.get_detail(tid)
    if not tid or not task_info:
        return render_template('error.html', message="无效的任务")
    if request.method=='GET':
        app_config = app.config.get('app_config')
        return render_template('/rule/add.html', app_config=app_config, task_info=task_info, rule={}, tid=tid)
    else:
        try:
            rule_obj = app.config.get('db')["ListRuleDB"]
            data = request.form.to_dict()
            mode = data.pop("mode")
            if mode == "rule-base":
                dic = build_rule_data(mode, data);
                dic['pid'] = task_info['pid']
                dic['sid'] = task_info['sid']
                dic['tid'] = task_info['uuid']
                dic['request'] = None
                dic['paging'] = None
                dic['unique'] = None
                dic['parse'] = None
                dic['url'] = None
                dic['script'] = None
                rid = rule_obj.insert(dic)
                return jsonify({"status": 200, "message": "Ok", "data": {"rid": rid}})
            else:
                end = False
                if mode == 'rule-script':
                    end = True
                rid = data.pop('id', 0)
                if not rid:
                    return jsonify({"status": 500, "message": "规则基本信息未保存成功,请重新设置。"})
                data = build_rule_data(mode, data)
                if not data:
                    return jsonify({"status": 200, "message": "Ok", "data": {"update": False, 'end': end}})
                rule_obj.update(int(rid), data)
                return jsonify({"status": 200, "message": "Ok", "data": {"update": True, 'end': end}})
        except Exception as e:
            app.logger.error(traceback.format_exc())
            return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/rule/<int:id>/edit', methods=['POST', 'GET'])
def rule_update(id):
    rule_obj = app.config.get('db')["ListRuleDB"]
    rule_info = rule_obj.get_detail(id)
    if not id or not rule_info:
        return render_template('error.html', message="无效的URL")
    tid = rule_info['tid']
    task_obj = app.config.get('db')["TaskDB"]
    task_info = task_obj.get_detail(tid)
    if request.method=='GET':
        app_config = app.config.get('app_config')
        return render_template('/rule/update.html', rule=build_form_data(rule_info), app_config=app_config,
                                                                         task_info=task_info)
    else:
        try:
            data = request.form.to_dict()
            mode = data.pop('mode', 'rule-base')
            data = build_rule_data(mode, data)
            end = False
            if mode == 'rule-script':
                end = True
            if not data:
                return jsonify({"status": 200, "message": "Ok", "data": {"update": False, 'end': end}})
            data['status'] = rule_obj.STATUS_INIT
            ret = rule_obj.update(int(id), data)
            if ret:
                app.config['status'](
                    {'rid': id, "mode": task_info['type'], "status": rule_obj.STATUS_INIT})
            return jsonify({"status": 200, "message": "Ok", "data": {"update": True, 'end': end}})
        except Exception as e:
            app.logger.error(traceback.format_exc())
            return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/rule/<int:id>/enable', methods=['GET'])
def rule_enable(id):
    try:
        rule_obj = app.config.get('db')["ListRuleDB"]
        rule_info = rule_obj.get_detail(id)
        if not id or not rule_info:
            return jsonify({"status": 500, "message": "无效的URL", "error": "error"})
        ret=rule_obj.enable(id)
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/rule/enable', methods=['POST'])
def rule_list_enable():
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
        rule_obj = app.config.get('db')["ListRuleDB"]
        url_list = rule_obj.get_list(where={'uid': arr, 'status': rule_obj.STATUS_DISABLE, 'tid': int(tid)})
        i = 0
        for item in iterator2list(url_list):
            ret=rule_obj.enable(item['uid'])
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/rule/<int:id>/delete', methods=['GET'])
def rule_delete(id):
    try:
        rule_obj = app.config.get('db')["ListRuleDB"]
        rule_info = rule_obj.get_detail(id)
        if not id or not rule_info:
            return jsonify({"status": 500, "message": "无效的URL", "error": "error"})
        ret=rule_obj.delete(id)
        if ret:
            task_obj = app.config.get('db')["TaskDB"]
            task_info = task_obj.get_detail(rule_info['tid'])
            app.config['status'](
                {'uid': id, 'mode': task_info['type'], "status": rule_obj.STATUS_DELETED})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/rule/delete', methods=['POST'])
def rule_list_delete():
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
        rule_obj = app.config.get('db')["ListRuleDB"]
        url_list = rule_obj.get_list(where={'uid': arr, 'status': [rule_obj.STATUS_INIT, rule_obj.STATUS_ACTIVE, rule_obj.STATUS_DISABLE], 'tid': int(tid)})
        i = 0
        for item in iterator2list(url_list):
            ret=rule_obj.delete(item['uid'])
            if ret:
                app.config['status'](
                    {'uid': item['uid'],  'mode': task_info['type'], "status": rule_obj.STATUS_DELETED})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/rule/<int:id>/disable', methods=['GET'])
def rule_disable(id):
    try:
        rule_obj = app.config.get('db')["ListRuleDB"]
        rule_info = rule_obj.get_detail(id)
        if not id or not rule_info:
            return jsonify({"status": 500, "message": "无效的URL", "error": "error"})
        task_obj = app.config.get('db')["TaskDB"]
        task_info = task_obj.get_detail(rule_info['tid'])
        ret=rule_obj.disable(id)
        if ret:
            app.config['status'](
                {'urlid': id, 'mode': task_info['type'], "status": rule_obj.STATUS_DISABLE})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/rule/disable', methods=['POST'])
def rule_list_disable():
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
        rule_obj = app.config.get('db')["ListRuleDB"]
        url_list = rule_obj.get_list(where={'uid': arr, 'status': [rule_obj.STATUS_INIT, rule_obj.STATUS_ACTIVE], 'tid': int(tid)})
        i = 0
        for item in iterator2list(url_list):
            ret=rule_obj.disable(item['uid'])
            if ret:
                app.config['status'](
                    {'urlid': item['uid'], 'mode': task_info['type'], "status": rule_obj.STATUS_DISABLE})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/rule/<int:id>/active', methods=['GET'])
def rule_active(id):
    try:
        rule_obj = app.config.get('db')["ListRuleDB"]
        rule_info = rule_obj.get_detail(id)
        if not id or not rule_info:
            return jsonify({"status": 500, "message": "无效的URL", "error": "error"})
        task_obj = app.config.get('db')["TaskDB"]
        task_info = task_obj.get_detail(rule_info['tid'])
        if not task_info:
            return jsonify({"status": 500, "message": "无效的任务", "error": "error"})
        if task_info['status'] != task_obj.STATUS_ACTIVE:
            return jsonify({"status": 500, "message": "请先激活任务", "error": "error"})
        ret=rule_obj.active(id)
        if ret:
            app.config['status'](
                {'urlid': id, 'mode': task_info['type'], "status": rule_obj.STATUS_ACTIVE})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/rule/active', methods=['POST'])
def rule_list_active():
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
        rule_obj = app.config.get('db')["ListRuleDB"]
        url_list = rule_obj.get_list(where={'uid': arr, 'status': rule_obj.STATUS_INIT, 'tid': int(tid)})
        i = 0
        for item in iterator2list(url_list):
            ret=rule_obj.active(item['uid'])
            if ret:
                app.config['status'](
                    {'urlid': item['uid'], 'mode': task_info['type'], "status": rule_obj.STATUS_ACTIVE})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/rule/dis', methods=['GET'])
def rule_disable_list():
    try:
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        tid = request.args.get('tid')
        task_obj = app.config.get('db')["TaskDB"]
        task_info = task_obj.get_detail(tid)
        if not tid or not task_info:
            return render_template('error.html', message="无效的任务")
        rule_obj = app.config.get('db')["ListRuleDB"]
        rule_count = rule_obj.count(where={'status': rule_obj.STATUS_DISABLE, 'tid': int(tid)})
        content = page_obj.page_list(current_page, rule_count)
        rule_list = rule_obj.get_list(where={'status': rule_obj.STATUS_DISABLE, 'tid': int(tid)}, offset=(current_page-1) * hits, sort=[("uid", -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/rule/disabled.html', app_config=app_config, task_info=task_info, rule_list=rule_list, content=content)
