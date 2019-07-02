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
        tid = int(request.args.get('tid', 0))
        current_page = int(request.args.get('page', 1))
        hits = int(request.args.get('hits', 10))
        keyworddb_obj=app.config.get('db')["KeywordsDB"]
        if tid > 0:
            where={"$and": [{'status': {"$in": [keyworddb_obj.STATUS_INIT, keyworddb_obj.STATUS_ACTIVE]}},
                            {"$or": [{"tid": 0}, {"tid": None}, {"tid": tid}]}]}
        else:
            where={'status': [keyworddb_obj.STATUS_INIT, keyworddb_obj.STATUS_ACTIVE]}
        keyword_count=keyworddb_obj.count(where)
        content = page_obj.page_list(current_page, keyword_count)
        keyword_list = keyworddb_obj.get_list(where=where, offset=(current_page - 1) * hits, sort=[("kid", -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/keyword/list.html', tid=tid, keyword_list=keyword_list, content=content, app_config=app_config)


@app.route('/keyword/add', methods=['POST', 'GET'])
def keyword_add():
    if request.method=='GET':
        tid = int(request.args.get('tid', 0))
        app_config = app.config['app_config']
        return render_template('/keyword/add.html', app_config=app_config, tid=tid)
    else:
        tid = request.form.get('tid', 0)
        arr = request.form.get('word').split('\r\n')
        keyworddb_obj = app.config.get('db')["KeywordsDB"]
        try:
            for word in arr:
                dic={
                    'tid': int(tid),
                    'word': word,
                    'src_txt':'后台',
                    'status': keyworddb_obj.STATUS_ACTIVE,
                    'frequency': request.form.get('frequency', '4'),
                    'expire': int(request.form.get('expire', 0))
                }
                try:
                    kwid = keyworddb_obj.insert(dic)
                    app.config['newtask']({'mode': 'search', 'kid': kwid})
                    app.config['newtask']({'mode': 'site-search', 'kid': kwid})
                except DuplicateKeyError:
                    continue
            return redirect('/keyword/list?tid=%s'% tid)
        except Exception as e:
            return render_template('/error.html', message=str(e))

@app.route('/keyword/<int:id>/edit', methods=['POST', 'GET'])
def keyword_upd(id):
    keyworddb_obj = app.config.get('db')["KeywordsDB"]
    tid = int(request.args.get('tid', 0))
    task_info = None
    if tid:
        task_obj = app.config.get('db')["TaskDB"]
        task_info = task_obj.get_detail(tid)
        if not task_info:
            return render_template('error.html', message="无效的任务")
    keyword_info = keyworddb_obj.get_detail(id)
    if not id or not keyword_info:
        return render_template('error.html', message="无效的关键词")
    if request.method=='GET':
        app_config = app.config['app_config']
        return render_template('/keyword/update.html', app_config=app_config, keyword=keyword_info, id=id, tid=tid)
    else:
        try:
            word=request.form.get('word')
            frequency = request.form.get('frequency', '4')
            expire = int(request.form.get('expire', 0))
            dic = {
                'word': word,
                'frequency': frequency,
                'expire': expire
            }
            keyworddb_obj = app.config.get('db')["KeywordsDB"]
            ret = keyworddb_obj.update(id, dic)
            if ret:
                if frequency != keyword_info.get("frequency"):
                    if task_info:
                        app.config['frequency']({'kid': id, 'mode': task_info['type'], "frequency": frequency})
                    else:
                        app.config['frequency']({'kid': id, 'mode': "search", "frequency": frequency})
                        app.config['frequency']({'kid': id, 'mode': "site-search", "frequency": frequency})

                if expire != keyword_info.get("expire"):
                    if task_info:
                        app.config['expire']({'kid': id, 'mode': task_info['type'], "expire": expire})
                    else:
                        app.config['expire']({'kid': id, 'mode': "search", "expire": expire})
                        app.config['expire']({'kid': id, 'mode': "site-search", "expire": expire})

            return redirect('/keyword/list?tid=%s' % tid)
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
