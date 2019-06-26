#!/usr/bin/python
# -*- coding:utf-8 -*-
import traceback
from pymongo.errors import *
from flask import request, render_template, redirect, jsonify
try:
    import flask_login as login
except ImportError:
    from flask.ext import login
from .app import app
from .utils.page_class import page_obj

@app.route('/keyword/list', methods=['GET'])
def keyword_list():
    try:
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        keyworddb_obj=app.config.get('db')["KeywordsDB"]
        keyword_count=keyworddb_obj.count(where={'status': [keyworddb_obj.STATUS_INIT, keyworddb_obj.STATUS_ACTIVE]})
        content = page_obj.page_list(current_page, keyword_count)
        keyword_list = keyworddb_obj.get_list(where={'status': [keyworddb_obj.STATUS_INIT, keyworddb_obj.STATUS_ACTIVE]}, offset=(current_page - 1) * hits, sort=[("kid", -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/keyword/list.html',keyword_list=keyword_list, content=content, app_config=app_config)


@app.route('/keyword/add', methods=['POST', 'GET'])
def keyword_add():
    if request.method=='GET':
        return render_template('/keyword/add.html')
    else:
        arr = request.form.get('word').split('\r\n')
        keyworddb_obj = app.config.get('db')["KeywordsDB"]
        try:
            for word in arr:
                dic={
                    'word': word,
                    'src_txt':'后台',
                    'status': keyworddb_obj.STATUS_ACTIVE,
                    'creator':'admin',
                    'updator':'admin'
                }
                try:
                    kwid = keyworddb_obj.insert(dic)
                    app.config['newtask']({'mode': 'search', 'kid': kwid})
                    app.config['newtask']({'mode': 'site-search', 'kid': kwid})
                except DuplicateKeyError:
                    continue
            return redirect('/keyword/list')
        except Exception as e:
            return render_template('/error.html', message=str(e))

@app.route('/keyword/<int:id>/edit', methods=['POST', 'GET'])
def keyword_upd(id):
    keyworddb_obj = app.config.get('db')["KeywordsDB"]
    if request.method=='GET':
        keyword_info = keyworddb_obj.get_detail(id)

        return render_template('/keyword/update.html',keyword=keyword_info, id=id)
    else:
        try:
            word=request.form.get('word')
            dic = {
                'word': word,
            }
            keyworddb_obj = app.config.get('db')["KeywordsDB"]
            ret = keyworddb_obj.update(id, dic)
            if ret:
                return jsonify({"status": 500, "message": "更新失败", "data": {"update": False}})
            return redirect('/keyword/list')
        except Exception as e:
            return render_template('/error.html', message=str(e))


@app.route('/keyword/<int:id>/delete', methods=['GET'])
def keyword_del(id):
    try:
        keyworddb_obj = app.config.get('db')["KeywordsDB"]
        keyword_info = keyworddb_obj.get_detail(id)
        if not id or not keyword_info:
            return jsonify({"status": 500, "message": "无效的关键词！", "error": "error"})
        ret=keyworddb_obj.delete(id)
        if ret:
            app.config['status'](
                {'kid': id, "mode": 'search', "status": keyworddb_obj.STATUS_DELETED})
            app.config['status'](
                {'kid': id, "mode": 'site-search', "status": keyworddb_obj.STATUS_DELETED})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/keyword/delete', methods=['POST'])
def keyword_list_del():
    try:
        keyworddb_obj = app.config.get('db')["KeywordsDB"]
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        project_list = keyworddb_obj.get_list(where={'uuid': arr, 'status': [keyworddb_obj.STATUS_INIT, keyworddb_obj.STATUS_ACTIVE, keyworddb_obj.STATUS_DISABLE]})
        i = 0
        for item in list(project_list):
            ret=keyworddb_obj.delete(item['uuid'])
            if ret:
                app.config['status'](
                    {'kid': item['uuid'], "mode": 'search', "status": keyworddb_obj.STATUS_DELETED})
                app.config['status'](
                    {'kid': item['uuid'], "mode": 'site-search', "status": keyworddb_obj.STATUS_DELETED})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/keyword/<int:id>/disable', methods=['GET'])
def keyword_disable(id):
    try:
        keyworddb_obj = app.config.get('db')["KeywordsDB"]
        keyword_info = keyworddb_obj.get_detail(id)
        if not id or not keyword_info:
            return jsonify({"status": 500, "message": "无效的关键词！", "error": "error"})
        ret=keyworddb_obj.disable(id)
        if ret:
            app.config['status'](
                {'kid': id, "mode": 'search', "status": keyworddb_obj.STATUS_DISABLE})
            app.config['status'](
                {'kid': id, "mode": 'site-search', "status": keyworddb_obj.STATUS_DISABLE})
            return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/keyword/disable', methods=['POST'])
def keyword_list_disable():
    try:
        keyworddb_obj = app.config.get('db')["KeywordsDB"]
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        project_list = keyworddb_obj.get_list(where={'uuid': arr, 'status': [keyworddb_obj.STATUS_ACTIVE]})
        i = 0
        for item in list(project_list):
            ret=keyworddb_obj.disable(item['uuid'])
            if ret:
                app.config['status'](
                    {'kid': item['uuid'], "mode": 'search', "status": keyworddb_obj.STATUS_DISABLE})
                app.config['status'](
                    {'kid': item['uuid'], "mode": 'site-search', "status": keyworddb_obj.STATUS_DISABLE})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/keyword/<int:id>/enable', methods=['GET'])
def keyword_enable(id):
    try:
        keyworddb_obj = app.config.get('db')["KeywordsDB"]
        keyword_info = keyworddb_obj.get_detail(id)
        if not id or not keyword_info:
            return jsonify({"status": 500, "message": "无效的关键词！", "error": "error"})
        ret=keyworddb_obj.enable(id)
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/keyword/<int:id>/active', methods=['GET'])
def keyword_active(id):
    try:
        keyworddb_obj = app.config.get('db')["KeywordsDB"]
        keyword_info = keyworddb_obj.get_detail(id)
        if not id or not keyword_info:
            return jsonify({"status": 500, "message": "无效的关键词！", "error": "error"})
        ret=keyworddb_obj.active(id)
        if ret:
            app.config['status'](
                {'kid': id, "mode": 'search', "status": keyworddb_obj.STATUS_ACTIVE})
            app.config['status'](
                {'kid': id, "mode": 'site-search', "status": keyworddb_obj.STATUS_ACTIVE})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": id}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/keyword/active', methods=['POST'])
def keyword_list_active():
    try:
        keyworddb_obj = app.config.get('db')["KeywordsDB"]
        ids = request.form.get('id')
        if not ids:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        arr = ids.split(',')
        arr = [int(k) for k in arr]
        project_list = keyworddb_obj.get_list(where={'uuid': arr, 'status': [keyworddb_obj.STATUS_INIT, keyworddb_obj.STATUS_DISABLE]})
        i = 0
        for item in list(project_list):
            ret=keyworddb_obj.active(item['uuid'])
            if ret:
                app.config['status'](
                    {'kid': item['uuid'], "mode": 'search', "status": keyworddb_obj.STATUS_ACTIVE})
                app.config['status'](
                    {'kid': item['uuid'], "mode": 'site-search', "status": keyworddb_obj.STATUS_ACTIVE})
            i += 1
        if i == 0:
            return jsonify({"status": 400, "message": "Ok", "data": {"id": ids}})
        return jsonify({"status": 200, "message": "Ok", "data": {"id": ids}})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({"status": 500, "message": "出错了！", "error": str(e)})


@app.route('/keyword/dis', methods=['GET'])
def keyword_disable_list():
    try:
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        keyworddb_obj = app.config.get('db')["KeywordsDB"]
        keyword_count = keyworddb_obj.count(where={'status': keyworddb_obj.STATUS_DISABLE})
        content = page_obj.page_list(current_page, keyword_count)
        keyword_list = keyworddb_obj.get_list(where={'status': keyworddb_obj.STATUS_DISABLE}, offset=(current_page - 1) * hits,sort=[("kid", -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/keyword/disabled.html', keyword_list=keyword_list, content=content, app_config=app_config)
