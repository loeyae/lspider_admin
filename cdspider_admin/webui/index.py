#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2019-04-09 23:19
"""

import sys
import time
import socket
import re
import cgi
import traceback
from urllib.parse import urljoin
from six import iteritems, itervalues
from flask import render_template, request, json

try:
    import flask_login as login
except ImportError:
    from flask.ext import login

from .app import app
from cdspider.libs.utils import dictjoin, get_current_month_days, __redirection__

index_fields = ['pid', 'type', 'status', 'comments', 'rate', 'updatetime']


@app.route('/', methods=['GET'])
def index():
    db = app.config.get("db")
    projectdb = db["ProjectsDB"]
    sitedb = db["SitesDB"]
    taskdb = db["TaskDB"]
    urlsdb = db["UrlsDB"]
    keywordsdb = db["KeywordsDB"]
    resultdb = db["ArticlesDB"]
    ctime = int(time.time())
#    aggregate = resultdb.aggregate_by_day(ctime, where = {"status": 1})

    aggregate = {}
    aggregate = dict((item['day'], item['count']) for item in aggregate)
    app.logger.debug("aggregate from db: %s" % aggregate)
    days = range(1, int(get_current_month_days()) +1)
    days = [str(i) if len(str(i)) > 1 else "0%s" %i for i in days]
    aggregate_by_day = dict.fromkeys(days, 0)
    app.logger.debug("aggregate from default: %s" % aggregate_by_day)
    aggregate_by_day.update(aggregate)
    app.logger.debug("aggregate from db union default: %s" % aggregate_by_day)
    count = {
        "project": projectdb.get_count() if projectdb else 0,
        "site": sitedb.count(where={}) if sitedb else 0,
        "urls": urlsdb.count(where={}) if urlsdb else 0,
        "tasks": taskdb.count(where={}) if taskdb else 0,
        "keywords": keywordsdb.count(where={}) if keywordsdb else 0,
        "result": resultdb.get_count(ctime, {'status': resultdb.STATUS_PARSED}) if resultdb else 0,
        "queues": get_queues(),
        "aggregate_by_day": [i for k, i in sorted(aggregate_by_day.items())]
    }
    app.logger.debug("aggregate sored: %s" % count['aggregate_by_day'])
    queue_setting = app.config.get('queue_setting')
    queue_maxsize = int(queue_setting.get('maxsize')) or 100
    queues = app.config.get('app_config', {}).get("queues", {})
    return render_template("index.html", count=count, queues=queues, queue_maxsize = queue_maxsize, days = days)

def get_queues():
    def try_get_qsize(queue):
        if queue is None:
            return 'None'
        try:
            return queue.qsize()
        except Exception as e:
            return "%r" % e

    result = {}
    queues = app.config.get('queues', {})
    for key in queues:
        result[key] = try_get_qsize(queues[key])
    return result

@app.route('/queues', methods=['GET',])
def queues():
    import random
    try:
        result = get_queues()
        return json.dumps({"status":200, "message": "Ok", "data": result}), 200, {'Content-Type': 'application/json'}
    except:
        return json.dumps({"status":500, "message": "获取队列数据失败！"}), 200, {'Content-Type': 'application/json'}

@app.route('/run', methods=['POST',])
def runtask():
    fetch = app.config.get('fetch')
    gtask = app.config.get('task')
    if fetch is None or gtask is None:
        return json.dumps({})


    data = request.form.to_dict()
    task = {
            "return_result": True,
            "mode": data['mode'],
            "url": data['url'],
            "keyword": {"word": data.get("keyword", None)},
            "rule": int(data['rule']),
            "save": {"current_page": data.get("page", 1)}
        }

    try:
        task = gtask(task)
        ret = json.loads(fetch(task))
    except socket.error as e:
        app.logger.warning('connect to fetcher rpc error: %r', e)
        return json.dumps({"result": None, "status": 500}), 200, {'Content-Type': 'application/json'}
    except:
        app.logger.warning('fetcher error: %r', traceback.format_exc())
        return json.dumps({"result":
        {"parsed": None, "broken_exc": None, "source": None, "url": None, "save": None, "stdout": None, "errmsg": traceback.format_exc()}, "status": 500}), 200, {'Content-Type': 'application/json'}
    return json.dumps({"result": ret, "status": 200}), 200, {'Content-Type': 'application/json'}


@app.route('/robots.txt')
def robots():
    return """User-agent: *
Disallow: /
Allow: /$
Allow: /debug
Disallow: /debug/*?taskid=*
""", 200, {'Content-Type': 'text/plain'}
