# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2019/6/22 16:54
"""

import traceback
from flask import request, render_template, jsonify
try:
    import flask_login as login
except ImportError:
    from flask.ext import login
from .app import app
from .utils.page_class import page_obj
from cdspider.libs import utils as cdutils


#启用页
@app.route('/task/list',methods=['GET'])
def task_list():
    try:
        sid = request.args.get('sid', None)
        site_obj = app.config.get('db')['SitesDB']
        site_info = site_obj.get_detail(sid)
        if not sid or not site_info:
            return render_template('/error.html', message="无效的站点")
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        taskdb_obj=app.config.get('db')["TaskDB"]
        where = {'status': [taskdb_obj.STATUS_INIT, taskdb_obj.STATUS_ACTIVE]}
        if sid:
            where['sid'] = int(sid)

        task_count = taskdb_obj.count(where)
        content = page_obj.page_list(current_page, task_count, hits)

        task_list=taskdb_obj.get_list(where, offset=(current_page-1) * hits, hits=hits, sort=[('uuid', -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/task/list.html', app_config=app_config, task_list=task_list, content=content,
                           site_info=site_info, sid=sid)

# 禁用页
@app.route('/task/dis', methods=['GET'])
def task_disable_list():
    try:
        sid = request.args.get('sid', None)
        site_obj = app.config.get('db')['SitesDB']
        site_info = site_obj.get_detail(sid)
        if not sid or not site_info:
            return render_template('/error.html', message="无效的站点")
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        taskdb_obj = app.config.get('db')["TaskDB"]
        where = {'status': taskdb_obj.STATUS_DISABLE}
        if sid:
            where['sid'] = int(sid)

        task_count = taskdb_obj.count(where=where)
        content = page_obj.page_list(current_page, task_count, hits)
        task_list = taskdb_obj.get_list(where=where, offset=(current_page - 1)*hits, hits=hits, sort=[('sid', -1)])

        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))

    return render_template('/task/disable.html', app_config=app_config, task_list=task_list, content=content,
                           site_info=site_info, sid=sid)

#删除
@app.route('/task/<int:id>/delete', methods=['GET'])
def task_delete(id):
    try:
        taskdb_obj = app.config.get('db')["TaskDB"]
        task_info = taskdb_obj.get_detail(id)
        if not task_info:
            return jsonify({"status": 500, "message": "无效的任务", "error": "error"})
        ret = taskdb_obj.delete(id)
        if ret:
            app.config['status']({'tid': id, "mode": task_info['type'], "status": taskdb_obj.STATUS_DELETED})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#删除
@app.route('/task/delete', methods=['POST'])
def task_list_delete():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        sid = request.form.get('sid')
        site_obj = app.config.get('db')['SitesDB']
        site_info = site_obj.get_detail(sid)
        if not sid or not site_info:
            return jsonify({"status": 500, "message": "无效的站点", "error": ""})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        taskdb_obj = app.config.get('db')["TaskDB"]
        task_list = taskdb_obj.get_list(where={'uuid': arr, 'status': [taskdb_obj.STATUS_INIT, taskdb_obj.STATUS_ACTIVE,
                                                                    taskdb_obj.STATUS_DISABLE], 'sid': int(sid)})
        i = 0
        for item in list(task_list):
            ret = taskdb_obj.delete(item['uuid'])
            if ret:
                app.config['status'](
                    {'tid': item['uuid'], "mode": item['type'], "status": taskdb_obj.STATUS_DELETED})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#激活
@app.route('/task/<int:id>/active', methods=['GET'])
def task_active(id):
    try:
        taskdb_obj = app.config.get('db')["TaskDB"]
        task_info = taskdb_obj.get_detail(id)
        if not task_info:
            return jsonify({"status": 500, "message": "无效的任务", "error": "error"})
        site_obj = app.config.get('db')['SitesDB']
        site_info = site_obj.get_detail(task_info['sid'])
        if not site_info:
            return jsonify({"status": 500, "message": "无效的站点", "error": "error"})
        if site_info['status'] != site_obj.STATUS_ACTIVE:
            return jsonify({"status": 500, "message": "站点未激活，请先激活站点", "error": "error"})
        taskdb_obj.active(id)
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#激活
@app.route('/task/active', methods=['POST'])
def task_list_active():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        sid = request.form.get('sid')
        site_obj = app.config.get('db')['SitesDB']
        site_info = site_obj.get_detail(sid)
        if not sid or not site_info:
            return jsonify({"status": 500, "message": "无效的站点", "error": ""})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        taskdb_obj = app.config.get('db')["TaskDB"]
        task_list = taskdb_obj.get_list(where={'uuid': arr, 'status': taskdb_obj.STATUS_INIT, 'sid': int(sid)})
        i = 0
        for item in list(task_list):
            ret = taskdb_obj.active(item['uuid'])
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#禁用
@app.route('/task/<int:id>/enable', methods=['GET'])
def task_enable(id):
    try:
        taskdb_obj = app.config.get('db')["TaskDB"]
        task_info = taskdb_obj.get_detail(id)
        if not task_info:
            return jsonify({"status": 500, "message": "无效的站点", "error": "error"})
        ret = taskdb_obj.enable(id)
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#激活
@app.route('/task/enable', methods=['POST'])
def task_list_enable():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        sid = request.form.get('sid')
        site_obj = app.config.get('db')['SitesDB']
        site_info = site_obj.get_detail(sid)
        if not sid or not site_info:
            return jsonify({"status": 500, "message": "无效的站点", "error": ""})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        taskdb_obj = app.config.get('db')["TaskDB"]
        task_list = taskdb_obj.get_list(where={'uuid': arr, 'status': taskdb_obj.STATUS_DISABLE, 'sid': int(sid)})
        i = 0
        for item in list(task_list):
            ret = taskdb_obj.enable(item['uuid'])
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#禁用
@app.route('/task/<int:id>/disable', methods=['GET'])
def task_disable(id):
    try:
        taskdb_obj = app.config.get('db')["TaskDB"]
        task_info = taskdb_obj.get_detail(id)
        if not task_info:
            return jsonify({"status": 500, "message": "无效的站点", "error": "error"})
        ret = taskdb_obj.disable(id)
        if ret:
            app.config['status']({'tid': id, "mode": task_info['type'], "status": taskdb_obj.STATUS_DISABLE})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#激活
@app.route('/task/disable', methods=['POST'])
def task_list_disable():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        sid = request.form.get('sid')
        site_obj = app.config.get('db')['SitesDB']
        site_info = site_obj.get_detail(sid)
        if not sid or not site_info:
            return jsonify({"status": 500, "message": "无效的站点", "error": ""})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        taskdb_obj = app.config.get('db')["TaskDB"]
        task_list = taskdb_obj.get_list(where={'uuid': arr, 'status': [taskdb_obj.STATUS_INIT,
                                                                       taskdb_obj.STATUS_ACTIVE], 'sid': int(sid)})
        i = 0
        for item in list(task_list):
            ret = taskdb_obj.disable(item['uuid'])
            if ret:
                app.config['status'](
                    {'tid': item['uuid'], "mode": item['type'], "status": taskdb_obj.STATUS_DISABLE})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#创建任务
@app.route('/task/add', methods=['POST', 'GET'])
def task_add():
    sid = request.args.get('sid')
    site_obj = app.config.get('db')['SitesDB']
    site_info = site_obj.get_detail(sid)
    app_config = app.config.get('app_config')
    if request.method == 'GET':
        if not sid or not site_info:
            return render_template('/error.html', message="无效的站点")
        return render_template('/task/task_form.html', app_config=app_config, sid=sid, site_info=site_info)
    else:
        try:
            if not sid or not site_info:
                return jsonify({"status": 500, "message": "无效的站点"})
            taskdb_obj = app.config.get('db')["TaskDB"]
            data = request.form.to_dict()
            data['pid'] = site_info['pid']
            data['sid'] = int(sid)

            sid = taskdb_obj.insert(data)
            if not sid or not site_info:
                return jsonify({"status": 200, "message": "Ok", "data": {}})
            return jsonify({"status": 200, "message": "Ok", "data": {"sid": sid}})
        except Exception as e:
            app.logger.error(traceback.format_exc())
            return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#编辑项目
@app.route('/task/<int:tid>/edit', methods=['POST', 'GET'])
def task_update(tid):
    taskdb_obj = app.config.get('db')["TaskDB"]
    task = taskdb_obj.get_detail(tid)
    site_obj = app.config.get('db')['SitesDB']
    site_info = site_obj.get_detail(task['sid'])
    if request.method == 'GET':
        if not task:
            return render_template('/error.html', message="无效的任务")
        app_config = app.config.get('app_config')
        return render_template('/task/update.html', task_info=task, app_config=app_config, site_info=site_info)

    else:
        try:
            if not task:
                return jsonify({"status": 500, "message": "无效的任务。"})
            data = request.form.to_dict()
            data['status'] = taskdb_obj.STATUS_INIT
            ret = taskdb_obj.update(tid, data)
            if ret:
                app.config['status'](
                    {'tid': tid, "status": taskdb_obj.STATUS_INIT})
            return jsonify({"status": 200, "message": "Ok", "data": {"update": True}})
        except Exception as e:
            app.logger.error(traceback.format_exc())
            return jsonify({"status": 500, "message": "出错了！", "error": str(e)})