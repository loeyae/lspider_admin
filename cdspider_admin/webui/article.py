#-*- coding: utf-8 -*-

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    19-7-13 上午8:02
"""

import datetime
import io
import time

import xlwt
from flask import jsonify, redirect, render_template, request, send_file

try:
    import flask_login as login
except ImportError:
    from flask.ext import login

from cdspider.database.base import ArticlesDB
from cdspider.libs import utils

from .app import app
from .utils.page_class import page_obj


@app.route('/result/list', methods=['GET'])
def article_list():
    try:
        hits = int(request.args.get('hits', 10))
        articledb_obj=app.config.get('db')["ArticlesDB"]
        where = build_article_where(request.args)
        args = request.args.to_dict()
        cyear = int(args.pop("year", 0))
        month = int(args.pop("month", 0))
        current_page = int(args.pop("page", 1))
        if not cyear:
            ctime = int(time.time())
        else:
            time_arr = time.strptime("%s-%s" % (cyear, month), "%Y-%m")
            ctime = int(time.mktime(time_arr))

        now = datetime.datetime.now()
        if not month:
            month = int(now.month)
        year = int(now.year)
        if not cyear:
            cyear = year
        article_count=articledb_obj.get_count(ctime, where=where)
        content = page_obj.page_list(current_page, article_count)
        article_list = articledb_obj.get_list(ctime, where=where, offset=(current_page - 1) * hits,
                                              sort=[("pubtime", -1)])
        app_config = app.config.get('app_config')
    except Exception as e:
        return render_template('/error.html', message=str(e))
    return render_template('/article/list.html', query=utils.url_encode(args), article_list=article_list,
                           year=year, cyear=cyear, month=month, content=content, app_config=app_config)

def build_article_where(args):
    pid = int(request.args.get('pid', 0))
    sid = int(request.args.get('sid', 0))
    tid = int(request.args.get('tid', 0))
    uid = int(request.args.get('uid', 0))
    kid = int(request.args.get('kid', 0))
    if pid > 0:
        where = {"crawlinfo.pid": pid}
    elif sid > 0:
        where = {"crawlinfo.sid": sid}
    elif tid > 0:
        where = {"crawlinfo.tid": tid}
    elif uid > 0:
        where = {"crawlinfo.uid": uid}
    elif kid > 0:
        where = {"crawlinfo.kid": kid}
    else:
        where = {}
    where['status'] = {"$ne": ArticlesDB.STATUS_INIT}
    return where


@app.route('/result/export', methods=['GET'])
def article_export():
    try:
        rid = '0'
        articledb_obj=app.config.get('db')["ArticlesDB"]
        where = build_article_where(request.args)
        args = request.args.to_dict()
        cyear = int(args.pop("year", 0))
        month = int(args.pop("month", 0))
        detail = int(args.pop("detail", 0))
        field = args.pop("field", "") or ""
        fields = field.split("|")
        if not cyear:
            ctime = int(time.time())
        else:
            time_arr = time.strptime("%s-%s" % (cyear, month), "%Y-%m")
            ctime = int(time.mktime(time_arr))

        article_count=articledb_obj.get_count(ctime, where=where)
        if article_count > 0:
            file_name = "result_export_%s.xls" % time.strftime("%Y%m%d%H%M%S")
            book = xlwt.Workbook(encoding="utf-8")
            sheet = book.add_sheet('sheet 1')
            r = 1
            row = ['title', 'url']
            if fields:
                for item in fields:
                    row.append(item)
            if detail:
                row.append("content")
            row.append("pubtime")
            sheet_write_row(sheet, 0, row)
            while article_count > 0:
                where['rid'] = {"$gt": rid}
                article_list = articledb_obj.get_list(ctime, where=where, hits=1000, sort=[("rid", 1)])
                for article in article_list:
                    row = [article['title'], article['url']]
                    if fields:
                        for key in fields:
                            v = article.get(key, "") or article.get("result", {}).get(key, "") or article.get(
                                "detail", {}).get(key, "")
                            row.append(str(v))
                    if detail:
                        row.append(article['content'])
                    row.append(time.strftime("%Y-%m-%d %H:%M", time.localtime(article['pubtime'] or article['ctime'])))
                    sheet_write_row(sheet, r, row)
                    rid = article['rid']
                    r += 1
                article_count -= 1000
            fp=io.BytesIO()
            book.save(fp)
            fp.seek(0)
            return send_file(fp, attachment_filename=file_name, as_attachment=True)
        else:
            return render_template('/error.html', message="无符合的数据")
    except Exception as e:
        return render_template('/error.html', message=str(e))

def sheet_write_row(sheet, row, data):
    cell = 0
    for item in data:
        sheet.write(row, cell, item)
        cell += 1
