# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2019/4/21 11:17
"""
import traceback
from flask import request, render_template, redirect, jsonify
try:
    import flask_login as login
except ImportError:
    from flask.ext import login
from .app import app
from .utils.page_class import page_obj
from .utils.form_data_format import build_extra_data, build_form_data

@app.route('/extra/list', methods=['GET'])
def extra_list():
    try:
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        extradb_obj=app.config.get('db')["ExtendRuleDB"]
        extra_count=extradb_obj.count(where={'status': [extradb_obj.STATUS_INIT, extradb_obj.STATUS_ACTIVE]})
        content = page_obj.page_list(current_page, extra_count)
        extra_list = extradb_obj.get_list(where={'status': [extradb_obj.STATUS_INIT, extradb_obj.STATUS_ACTIVE]}, offset=(current_page - 1) * hits, sort=[("kid", -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/extra/list.html',extra_list=extra_list, content=content, app_config=app_config)


@app.route('/extra/add', methods=['POST', 'GET'])
def extra_add():
    if request.method=='GET':
        app_config = app.config.get('app_config')
        return render_template('/extra/add.html', app_config=app_config, rule={})
    else:
        try:
            extradb_obj = app.config.get('db')["ExtendRuleDB"]
            data = request.form.to_dict()
            mode = data.pop("mode")
            if mode == "extra-base":
                dic = build_extra_data(mode, data)
                dic['request'] = None
                dic['paging'] = None
                dic['unique'] = None
                dic['parse'] = None
                dic['script'] = None
                rid = extradb_obj.insert(dic)
                return jsonify({"status": 200, "message": "Ok", "data": {"rid": rid}})
            else:
                end = False
                if mode == 'extra-script':
                    end = True
                rid = data.pop('id', 0)
                if not rid:
                    return jsonify({"status": 500, "message": "规则基本信息未保存成功,请重新设置。"})
                data = build_extra_data(mode, data)
                if not data:
                    return jsonify({"status": 200, "message": "Ok", "data": {"update": False, 'end': end}})
                extradb_obj.update(int(rid), data)
                return jsonify({"status": 200, "message": "Ok", "data": {"update": True, 'end': end}})
        except Exception as e:
            app.logger.error(traceback.format_exc())
            return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/extra/<int:id>/edit', methods=['POST', 'GET'])
def extra_upd(id):
    extradb_obj = app.config.get('db')["ExtendRuleDB"]
    if request.method=='GET':
        app_config = app.config.get('app_config')
        extra_info = extradb_obj.get_detail(id)
        return render_template('/extra/update.html', rule=build_form_data(extra_info), id=id, app_config=app_config)
    else:
        try:
            data = request.form.to_dict()
            mode = data.pop('mode', 'extra-base')
            data = build_extra_data(mode, data)
            end = False
            if mode == 'extra-script':
                end = True
            if not data:
                return jsonify({"status": 200, "message": "Ok", "data": {"update": False, 'end': end}})
            data['status'] = extradb_obj.STATUS_INIT
            ret = extradb_obj.update(int(id), data)
            return jsonify({"status": 200, "message": "Ok", "data": {"update": True, 'end': end}})
        except Exception as e:
            app.logger.error(traceback.format_exc())
            return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/extra/<int:id>/delete', methods=['GET'])
def extra_del(id):
    try:
        extradb_obj = app.config.get('db')["ExtendRuleDB"]
        extra_info = extradb_obj.get_detail(id)
        if not id or not extra_info:
            return jsonify({"status": 500, "message": "无效的规则！", "error": "error"})
        ret=extradb_obj.delete(id)
        if ret:
            return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
        return jsonify({"status": 500, "message": "删除失败！"})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/extra/<int:id>/disable', methods=['GET'])
def extra_disable(id):
    try:
        extradb_obj = app.config.get('db')["ExtendRuleDB"]
        extra_info = extradb_obj.get_detail(id)
        if not id or not extra_info:
            return jsonify({"status": 500, "message": "无效的规则！", "error": "error"})
        ret=extradb_obj.disable(id)
        if ret:
            return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
        return jsonify({"status": 500, "message": "禁用失败！"})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/extra/<int:id>/enable', methods=['GET'])
def extra_enable(id):
    try:
        extradb_obj = app.config.get('db')["ExtendRuleDB"]
        extra_info = extradb_obj.get_detail(id)
        if not id or not extra_info:
            return jsonify({"status": 500, "message": "无效的规则！", "error": "error"})
        ret=extradb_obj.enable(id)
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/extra/<int:id>/active', methods=['GET'])
def extra_active(id):
    try:
        extradb_obj = app.config.get('db')["ExtendRuleDB"]
        extra_info = extradb_obj.get_detail(id)
        if not id or not extra_info:
            return jsonify({"status": 500, "message": "无效的规则！", "error": "error"})
        extradb_obj.active(id)
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/extra/dis', methods=['GET'])
def extra_disable_list():
    try:
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        extradb_obj = app.config.get('db')["ExtendRuleDB"]
        extra_count = extradb_obj.count(where={'status': extradb_obj.STATUS_DISABLE})
        content = page_obj.page_list(current_page, extra_count)
        extra_list = extradb_obj.get_list(where={'status': extradb_obj.STATUS_DISABLE}, offset=(current_page - 1) * hits,sort=[("kid", -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/extra/disabled.html', extra_list=extra_list, content=content, app_config=app_config)
