# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2019/6/20 17:02
"""
import traceback
from flask import request, render_template, redirect, json, jsonify
try:
    import flask_login as login
except ImportError:
    from flask.ext import login
from .app import app
from .utils.page_class import page_obj


#启用页
@app.route('/project/list', methods=['GET'])
def project_list():
    try:
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        projectdb_obj=app.config.get('db')["ProjectsDB"]

        project_count = projectdb_obj.get_count(where={'status': [projectdb_obj.STATUS_INIT, projectdb_obj.STATUS_ACTIVE]})
        content = page_obj.page_list(current_page, project_count, hits)

        project_list=projectdb_obj.get_list(where={'status':[projectdb_obj.STATUS_INIT, projectdb_obj.STATUS_ACTIVE]}, offset= (current_page-1) * hits, hits = hits, sort=[('pid', -1)])

        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))

    return render_template('/project/list.html', app_config=app_config, project_list=project_list, content=content)



# 创建项目
@app.route('/project/add', methods=['POST', 'GET'])
def project_add():
    if request.method=='GET':
        app_config = app.config.get('app_config')
        return render_template('/project/add.html', app_config=app_config)

    else:
        try:
            projectdb_obj = app.config.get('db')["ProjectsDB"]
            data = request.form.to_dict()
            data['status'] = projectdb_obj.STATUS_ACTIVE
            pid = projectdb_obj.insert(data)

            return jsonify({"status": 200, "message": "Ok", "data": {"id": pid}})
        except Exception as e:
            app.logger.error(traceback.format_exc())
            return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


# 编辑
@app.route('/project/<int:id>/edit', methods=['POST', 'GET'])
def project_update(id):
    projectdb_obj = app.config.get('db')["ProjectsDB"]
    project_info = projectdb_obj.get_detail(id)
    if request.method == 'GET':
        if not project_info:
            return render_template('/error.html', message="无效的项目")
        return render_template('/project/update.html', project_info=project_info, id=id)
    else:
        if not project_info:
            return jsonify({"status": 500, "message": "无效的项目。"})
        try:
            data = request.form.to_dict()
            if not data:
                return jsonify({"status": 200, "message": "Ok", "data": {"update": False}})
            ret = projectdb_obj.update(id, data)
            if ret:
                return jsonify({"status": 500, "message": "更新失败", "data": {"update": False}})
            return jsonify({"status": 200, "message": "Ok", "data": {"update": True}})
        except Exception as e:
            app.logger.error(traceback.format_exc())
            return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/project/<int:id>/delete', methods=['GET'])
def project_delete(id):
    try:
        projectdb_obj = app.config.get('db')["ProjectsDB"]
        ret=projectdb_obj.delete(id)
        if ret:
            app.config['status']({'pid': id, "status": projectdb_obj.STATUS_DELETED})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/project/<int:id>/disable', methods=['GET'])
def project_disable(id):
    try:
        projectdb_obj = app.config.get('db')["ProjectsDB"]
        ret=projectdb_obj.disable(id)
        if ret:
            app.config['status']({'pid': id, "status": projectdb_obj.STATUS_DISABLE})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/project/<int:id>/active', methods=['GET'])
def project_active(id):
    try:
        projectdb_obj = app.config.get('db')["ProjectsDB"]
        ret=projectdb_obj.active(id)
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/project/<int:id>/enable', methods=['GET'])
def project_enable(id):
    try:
        projectdb_obj = app.config.get('db')["ProjectsDB"]
        ret=projectdb_obj.enable(id)
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


# 删除,页面删除后数据库状态改为3
@app.route('/project/delete', methods=['POST'])
def project_list_delete():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        projectdb_obj = app.config.get('db')["ProjectsDB"]
        project_list = projectdb_obj.get_list(where={'uuid': arr, 'status': [projectdb_obj.STATUS_INIT, projectdb_obj.STATUS_DISABLE]})
        i = 0
        for item in list(project_list):
            ret = projectdb_obj.delete(item['pid'])
            if ret:
                app.config['status']({'pid': item['uuid'], "status": projectdb_obj.STATUS_DELETED})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


# 激活
@app.route('/project/active', methods=['POST'])
def project_list_active():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        projectdb_obj = app.config.get('db')["ProjectsDB"]
        project_list = projectdb_obj.get_list(where={'uuid': arr, 'status': projectdb_obj.STATUS_INIT})
        i = 0
        for item in list(project_list):
            ret = projectdb_obj.active(item['pid'])
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


# 禁用
@app.route('/project/disable', methods=['POST'])
def project_list_disable():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        projectdb_obj = app.config.get('db')["ProjectsDB"]
        project_list = projectdb_obj.get_list(where={'uuid': arr, 'status': [projectdb_obj.STATUS_INIT, projectdb_obj.STATUS_ACTIVE]})
        i = 0
        for item in list(project_list):
            ret = projectdb_obj.disable(item['uuid'])
            if ret:
                app.config['status']({'pid': item['uuid'], "status": projectdb_obj.STATUS_DISABLE})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


# 启用
@app.route('/project/enable', methods=['POST'])
def project_list_enable():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        projectdb_obj = app.config.get('db')["ProjectsDB"]
        project_list = projectdb_obj.get_list(where={'uuid': arr, 'status': projectdb_obj.STATUS_DISABLE})
        i = 0
        for item in list(project_list):
            ret = projectdb_obj.enable(item['pid'])
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


# 禁用页
@app.route('/project/dis', methods=['get'])
def project_disable_list():
    try:
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        projectdb_obj = app.config.get('db')["ProjectsDB"]
        project_count = projectdb_obj.get_count(where={'status': projectdb_obj.STATUS_DISABLE})
        content = page_obj.page_list(current_page, project_count, hits)
        project_list = projectdb_obj.get_list(where={'status': projectdb_obj.STATUS_DISABLE}, offset=(current_page - 1) * hits, hits = hits, sort=[('pid', -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/project/disabled.html', app_config=app_config, project_list=project_list, content=content)
