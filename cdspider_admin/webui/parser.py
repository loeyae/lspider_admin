# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2019/4/21 11:17
"""
import traceback

from flask import jsonify, redirect, render_template, request

try:
    import flask_login as login
except ImportError:
    from flask.ext import login

from .app import app
from .utils.form_data_format import build_form_data, build_parser_data
from .utils.page_class import page_obj


@app.route('/parser/list', methods=['GET'])
def parser_list():
    try:
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        parserdb_obj=app.config.get('db')["ParseRuleDB"]
        parser_count=parserdb_obj.count(where={'status': [parserdb_obj.STATUS_INIT, parserdb_obj.STATUS_ACTIVE]})
        content = page_obj.page_list(current_page, parser_count)
        parser_list = parserdb_obj.get_list(where={'status': [parserdb_obj.STATUS_INIT, parserdb_obj.STATUS_ACTIVE]}, offset=(current_page - 1) * hits, sort=[("kid", -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/parser/list.html',parser_list=parser_list, content=content, app_config=app_config)


@app.route('/parser/add', methods=['POST', 'GET'])
def parser_add():
    if request.method=='GET':
        app_config = app.config.get('app_config')
        return render_template('/parser/add.html', app_config=app_config, rule={})
    else:
        try:
            parserdb_obj = app.config.get('db')["ParseRuleDB"]
            data = request.form.to_dict()
            mode = data.pop("mode")
            if mode == "parser-base":
                dic = build_parser_data(mode, data)
                dic['request'] = None
                dic['paging'] = None
                dic['unique'] = None
                dic['parse'] = None
                dic['url'] = None
                dic['script'] = None
                rid = parserdb_obj.insert(dic)
                return jsonify({"status": 200, "message": "Ok", "data": {"rid": rid}})
            else:
                end = False
                if mode == 'parser-script':
                    end = True
                rid = data.pop('id', 0)
                if not rid:
                    return jsonify({"status": 500, "message": "规则基本信息未保存成功,请重新设置。"})
                data = build_parser_data(mode, data)
                if not data:
                    return jsonify({"status": 200, "message": "Ok", "data": {"update": False, 'end': end}})
                parserdb_obj.update(int(rid), data)
                return jsonify({"status": 200, "message": "Ok", "data": {"update": True, 'end': end}})
        except Exception as e:
            app.logger.error(traceback.format_exc())
            return jsonify({"status": 500, "message": "出错了！", "error": str(e)})

@app.route('/parser/<int:id>/edit', methods=['POST', 'GET'])
def parser_upd(id):
    parserdb_obj = app.config.get('db')["ParseRuleDB"]
    if request.method=='GET':
        app_config = app.config.get('app_config')
        parser_info = parserdb_obj.get_detail(id)
        return render_template('/parser/update.html', rule=build_form_data(parser_info), id=id, app_config=app_config)
    else:
        try:
            data = request.form.to_dict()
            mode = data.pop('mode', 'parser-base')
            data = build_parser_data(mode, data)
            end = False
            if mode == 'parser-script':
                end = True
            if not data:
                return jsonify({"status": 200, "message": "Ok", "data": {"update": False, 'end': end}})
            data['status'] = parserdb_obj.STATUS_INIT
            ret = parserdb_obj.update(int(id), data)
            return jsonify({"status": 200, "message": "Ok", "data": {"update": True, 'end': end}})
        except Exception as e:
            app.logger.error(traceback.format_exc())
            return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/parser/<int:id>/delete', methods=['GET'])
def parser_del(id):
    try:
        parserdb_obj = app.config.get('db')["ParseRuleDB"]
        parser_info = parserdb_obj.get_detail(id)
        if not id or not parser_info:
            return jsonify({"status": 500, "message": "无效的规则！", "error": "error"})
        ret=parserdb_obj.delete(id)
        if ret:
            return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
        return jsonify({"status": 500, "message": "删除失败！"})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/parser/<int:id>/disable', methods=['GET'])
def parser_disable(id):
    try:
        parserdb_obj = app.config.get('db')["ParseRuleDB"]
        parser_info = parserdb_obj.get_detail(id)
        if not id or not parser_info:
            return jsonify({"status": 500, "message": "无效的规则！", "error": "error"})
        ret=parserdb_obj.disable(id)
        if ret:
            return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
        return jsonify({"status": 500, "message": "禁用失败！"})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/parser/<int:id>/enable', methods=['GET'])
def parser_enable(id):
    try:
        parserdb_obj = app.config.get('db')["ParseRuleDB"]
        parser_info = parserdb_obj.get_detail(id)
        if not id or not parser_info:
            return jsonify({"status": 500, "message": "无效的规则！", "error": "error"})
        ret=parserdb_obj.enable(id)
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/parser/<int:id>/active', methods=['GET'])
def parser_active(id):
    try:
        parserdb_obj = app.config.get('db')["ParseRuleDB"]
        parser_info = parserdb_obj.get_detail(id)
        if not id or not parser_info:
            return jsonify({"status": 500, "message": "无效的规则！", "error": "error"})
        parserdb_obj.active(id)
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/parser/dis', methods=['GET'])
def parser_disable_list():
    try:
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        parserdb_obj = app.config.get('db')["ParseRuleDB"]
        parser_count = parserdb_obj.count(where={'status': parserdb_obj.STATUS_DISABLE})
        content = page_obj.page_list(current_page, parser_count)
        parser_list = parserdb_obj.get_list(where={'status': parserdb_obj.STATUS_DISABLE}, offset=(current_page - 1) * hits,sort=[("kid", -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/parser/disabled.html', parser_list=parser_list, content=content, app_config=app_config)
