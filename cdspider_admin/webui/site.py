#!/usr/bin/env python
# -*- encoding: utf-8 -*-

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
@app.route('/site/list',methods=['GET'])
def site_list():
    try:
        pid = request.args.get('pid', None)
        if not pid:
            return render_template('/error.html', message="无效的项目或站点类型")
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        sitedb_obj=app.config.get('db')["SitesDB"]
        where = {'status': [sitedb_obj.STATUS_INIT, sitedb_obj.STATUS_ACTIVE]}
        if pid:
            where['pid'] = int(pid)

        site_count = sitedb_obj.count(where)
        content = page_obj.page_list(current_page, site_count, hits)

        site_list=sitedb_obj.get_list(where,offset=(current_page-1) * hits, hits=hits, sort=[('uuid', -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/site/list.html', app_config=app_config, site_list=site_list, content=content, pid=pid)

# 禁用页
@app.route('/site/dis', methods=['GET'])
def site_disable_list():
    try:
        pid = request.args.get('pid', None)
        if not pid:
            return render_template('/error.html', message="无效的项目或站点类型")
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        sitedb_obj = app.config.get('db')["SitesDB"]
        where = {'status': sitedb_obj.STATUS_DISABLE}
        if pid:
            where['pid'] = int(pid)

        site_count = sitedb_obj.count(where=where)
        content = page_obj.page_list(current_page, site_count, hits)
        site_list = sitedb_obj.get_list(where=where, offset=(current_page - 1)*hits, hits=hits, sort=[('sid', -1)])

        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))

    return render_template('/site/disable.html', app_config=app_config, site_list=site_list, content=content, pid=pid)

#删除
@app.route('/site/<int:id>/delete', methods=['GET'])
def site_delete(id):
    try:
        sitedb_obj = app.config.get('db')["SitesDB"]
        site_info = sitedb_obj.get_detail(id)
        if not site_info:
            return jsonify({"status": 500, "message": "无效的站点", "error": "error"})
        ret = sitedb_obj.delete(id)
        if ret:
            app.config['status'](
                {'sid': id, "status": sitedb_obj.STATUS_DELETED})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#删除
@app.route('/site/delete', methods=['POST'])
def site_list_delete():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        pid = request.form.get('pid')
        project_obj = app.config.get('db')['ProjectsDB']
        project_info = project_obj.get_detail(pid)
        if not pid or not project_info:
            return jsonify({"status": 500, "message": "无效的项目", "error": ""})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        sitedb_obj = app.config.get('db')["SitesDB"]
        site_list = sitedb_obj.get_list(where={'uuid': arr, 'status': [sitedb_obj.STATUS_INIT, sitedb_obj.STATUS_ACTIVE,
                                                                    sitedb_obj.STATUS_DISABLE], 'pid': int(pid)})
        i = 0
        for item in list(site_list):
            ret = sitedb_obj.delete(item['uuid'])
            if ret:
                app.config['status'](
                    {'sid': item['uuid'], "status": sitedb_obj.STATUS_DELETED})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#激活
@app.route('/site/<int:id>/active', methods=['GET'])
def site_active(id):
    try:
        sitedb_obj = app.config.get('db')["SitesDB"]
        site_info = sitedb_obj.get_detail(id)
        if not site_info:
            return jsonify({"status": 500, "message": "无效的站点", "error": "error"})
        project_obj = app.config.get('db')['ProjectsDB']
        project_info = project_obj.get_detail(site_info['pid'])
        if not project_info:
            return jsonify({"status": 500, "message": "无效的项目", "error": "error"})
        if project_info['status'] != project_obj.STATUS_ACTIVE:
            return jsonify({"status": 500, "message": "项目未激活，请先激活项目", "error": "error"})
        sitedb_obj.active(id)
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#激活
@app.route('/site/active', methods=['POST'])
def site_list_active():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        pid = request.form.get('pid')
        project_obj = app.config.get('db')['ProjectsDB']
        project_info = project_obj.get_detail(pid)
        if not pid or not project_info:
            return jsonify({"status": 500, "message": "无效的项目", "error": ""})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        sitedb_obj = app.config.get('db')["SitesDB"]
        site_list = sitedb_obj.get_list(where={'uuid': arr, 'status': sitedb_obj.STATUS_INIT, 'pid': int(pid)})
        i = 0
        for item in list(site_list):
            ret = sitedb_obj.active(item['uuid'])
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#禁用
@app.route('/site/<int:id>/enable', methods=['GET'])
def site_enable(id):
    try:
        sitedb_obj = app.config.get('db')["SitesDB"]
        site_info = sitedb_obj.get_detail(id)
        if not site_info:
            return jsonify({"status": 500, "message": "无效的站点", "error": "error"})
        ret = sitedb_obj.enable(id)
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#激活
@app.route('/site/enable', methods=['POST'])
def site_list_enable():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        pid = request.form.get('pid')
        project_obj = app.config.get('db')['ProjectsDB']
        project_info = project_obj.get_detail(pid)
        if not pid or not project_info:
            return jsonify({"status": 500, "message": "无效的项目", "error": ""})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        sitedb_obj = app.config.get('db')["SitesDB"]
        site_list = sitedb_obj.get_list(where={'uuid': arr, 'status': sitedb_obj.STATUS_DISABLE, 'pid': int(pid)})
        i = 0
        for item in list(site_list):
            ret = sitedb_obj.enable(item['uuid'])
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#禁用
@app.route('/site/<int:id>/disable', methods=['GET'])
def site_disable(id):
    try:
        sitedb_obj = app.config.get('db')["SitesDB"]
        site_info = sitedb_obj.get_detail(id)
        if not site_info:
            return jsonify({"status": 500, "message": "无效的站点", "error": "error"})
        ret = sitedb_obj.disable(id)
        if ret:
            app.config['status']({'sid': id, "status": sitedb_obj.STATUS_DISABLE})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#激活
@app.route('/site/disable', methods=['POST'])
def site_list_disable():
    try:
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        pid = request.form.get('pid')
        project_obj = app.config.get('db')['ProjectsDB']
        project_info = project_obj.get_detail(pid)
        if not pid or not project_info:
            return jsonify({"status": 500, "message": "无效的项目", "error": ""})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        sitedb_obj = app.config.get('db')["SitesDB"]
        site_list = sitedb_obj.get_list(where={'uuid': arr, 'status': [sitedb_obj.STATUS_INIT,
                                                                    sitedb_obj.STATUS_ACTIVE], 'pid': int(pid)})
        i = 0
        for item in list(site_list):
            ret = sitedb_obj.disable(item['uuid'])
            if ret:
                app.config['status'](
                    {'sid': item['uuid'], "status": sitedb_obj.STATUS_DISABLE})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#创建站点
@app.route('/site/add', methods=['POST', 'GET'])
def site_add():
    pid = request.args.get('pid')
    project_obj = app.config.get('db')['ProjectsDB']
    project = project_obj.get_detail(pid)
    app_config = app.config.get('app_config')
    if request.method=='GET':
        if not pid or not project:
            return render_template('/error.html', message="无效的项目")
        site_info = {}
        return render_template('/site/site_form.html', app_config=app_config, project=project, pid=pid, site_info=site_info)
    else:
        try:
            if not pid or not project:
                return jsonify({"status": 500, "message": "无效的项目"})
            sitedb_obj = app.config.get('db')["SitesDB"]
            data = request.form.to_dict()
            mode = data.pop('mode', 'site-base')
            data['pid'] = int(pid)
            url = data['url']
            typeinfo = cdutils.typeinfo(url)
            domain = typeinfo['domain']
            subdomain = typeinfo['subdomain']
            data['domain'] = domain
            data['subdomain'] = subdomain

            sid = sitedb_obj.insert(data)
            if not sid:
                return jsonify({"status": 200, "message": "Ok", "data": {}})
            return jsonify({"status": 200, "message": "Ok", "data": {"sid": sid}})
        except Exception as e:
            app.logger.error(traceback.format_exc())
            return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

#编辑项目
@app.route('/site/<int:sid>/edit', methods=['POST', 'GET'])
def site_update(sid):
    sitedb_obj = app.config.get('db')["SitesDB"]
    site = sitedb_obj.get_detail(sid)
    project_obj = app.config.get('db')['ProjectsDB']
    project = project_obj.get_detail(site['pid'])
    if request.method=='GET':
        if not site:
            return render_template('/error.html', message="无效的站点")
        app_config = app.config.get('app_config')
        return render_template('/site/update.html',site_info=site, app_config=app_config, sid=sid, project=project)

    else:
        try:
            if not site:
                return jsonify({"status": 500, "message": "无效的站点。"})
            data = request.form.to_dict()
            data['status'] = sitedb_obj.STATUS_INIT
            ret = sitedb_obj.update(sid, data)
            if ret:
                app.config['status'](
                    {'sid': sid, 'pid': project['uuid'], "status": sitedb_obj.STATUS_INIT})
            return jsonify({"status": 200, "message": "Ok", "data": {"update": True}})
        except Exception as e:
            app.logger.error(traceback.format_exc())
            return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/site/search', methods=['GET'])
def site_search():
    try:
        title = request.args.get('q')
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        sitedb_obj=app.config.get('db')["SitesDB"]
        where = [("name", "$regex", title), ('status', "$in", [sitedb_obj.STATUS_INIT, sitedb_obj.STATUS_ACTIVE])]

        site_count = sitedb_obj.count(where)
        content = page_obj.page_list(current_page, site_count, hits)

        site_list=sitedb_obj.get_list(where,offset=(current_page-1) * hits, hits=hits, sort=[('uuid', -1)])
        app_config = app.config.get('app_config')
        return render_template('/site/list.html', app_config=app_config, content=content, site_list=site_list, stid=None, pid=None)
    except Exception as e:
        return render_template('/error.html', message=str(e))
