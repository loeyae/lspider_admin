#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2019-04-09 23:19
"""

import os
import sys
import logging
import base64

from six import reraise
from six.moves import builtins
from six.moves.urllib.parse import urljoin
from flask import Flask, render_template, request, Response, redirect, url_for, g
try:
    import flask_login as login
except ImportError:
    from flask.ext import login
from cdspider_admin.database.base import AdminDB
from cdspider.libs import utils

if os.name == 'nt':
    import mimetypes
    mimetypes.add_type("text/css", ".css", True)


class CDSpiderFlask(Flask):

    @property
    def logger(self):
        logger = logging.getLogger("webui")
        if self.debug:
            logger.setLevel(logging.DEBUG)
        return logger

    def run(self, host=None, port=None, debug=None, **options):
        import tornado.wsgi
        import tornado.ioloop
        import tornado.httpserver
        import tornado.web

        if host is None:
            host = '127.0.0.1'
        if port is None:
            server_name = self.config['SERVER_NAME']
            if server_name and ':' in server_name:
                port = int(server_name.rsplit(':', 1)[1])
            else:
                port = 5000
        if debug is not None:
            self.debug = bool(debug)

        hostname = host
        application = self
        use_reloader = self.debug
        use_debugger = self.debug

        if use_debugger:
            from werkzeug.debug import DebuggedApplication
            application = DebuggedApplication(application, True)

        try:
            from .webdav import dav_app
        except ImportError as e:
            self.logger.warning('WebDav interface not enabled: %r', e)
            dav_app = None
        if dav_app:
            from werkzeug.wsgi import DispatcherMiddleware
            application = DispatcherMiddleware(application, {
                '/dav': dav_app
            })

        container = tornado.wsgi.WSGIContainer(application)
        self.http_server = tornado.httpserver.HTTPServer(container)
        self.http_server.listen(port, hostname)
        if use_reloader:
            from tornado import autoreload
            autoreload.start()

        self.logger.info('webui running on %s:%s', hostname, port)
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.ioloop.start()

    def quit(self):
        if hasattr(self, 'ioloop'):
            self.ioloop.add_callback(self.http_server.stop)
            self.ioloop.add_callback(self.ioloop.stop)
        self.logger.info('webui exiting...')


app = CDSpiderFlask('webui',
                    static_folder=os.path.join(os.path.dirname(__file__), 'static'),
                    template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = os.urandom(24)
app.jinja_env.line_statement_prefix = '#'
app.jinja_env.globals.update(builtins.__dict__)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

def error_url_handler(error, endpoint, kwargs):
    exc_type, exc_value, tb = sys.exc_info()
    if exc_value is error:
        reraise(exc_type, exc_value, tb)
    else:
        raise error
app.handle_url_build_error = error_url_handler



@app.before_request
def before_request(*args, **kwargs):
    app.logger.debug(request.endpoint)
    if request.endpoint in ('signin', 'signup', 'static', 'attach', "article_export"):
        return
    need_auth = app.config.get('need_auth', False)
    if need_auth:
        if not login.current_user.is_active:
            if need_auth == 'header':
                return app.login_response
            else:
                return redirect(url_for("signin"))
        g.user = login.current_user


login_manager = login.LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"

class AnonymousUser(login.AnonymousUserMixin):
    pass


class User(login.UserMixin):

    def __init__(self, id, password):
        self.id = id
        self.password = password
        self.name = None
        self.ruleid = 0

    @property
    def is_authenticated(self):
        need_auth = app.config.get('need_auth', False)
        if need_auth == "header":
            if not app.config.get('webui_username'):
                return True
            if self.id == app.config.get('webui_username') \
                    and self.password == app.config.get('webui_password'):
                self.name = app.config.get('webui_username')
                self.ruleid = AdminDB.ADMIN_RULE_ROOT
                return True
        else:
            Admindb = app.config.get("db")["AdminDB"]
            res, info = Admindb.verify_user(self.id, self.password)
            if res:
                self.name = info['name']
                self.ruleid = info['ruleid']
                return True
        return False

    @property
    def is_active(self):
        need_auth = app.config.get('need_auth', False)
        if need_auth == "header":
            return self.is_authenticated
        else:
            Admindb = app.config.get("db")["AdminDB"]
            info = Admindb.get_detail_by_account(account=self.id)
            if info['ruleid'] != AdminDB.ADMIN_RULE_NONE and info['status'] == AdminDB.STATUS_ACTIVE:
                self.name = info['name']
                self.ruleid = info['ruleid']
                return True
            return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(userid):
    return User(id=userid, password=None)

@login_manager.request_loader
def load_user_from_request(request):
    need_auth = app.config.get('need_auth', False)
    if need_auth == "header":
        api_key = request.headers.get('Authorization')
        if api_key:
            api_key = api_key[len("Basic "):]
            try:
                api_key = base64.b64decode(api_key).decode('utf8')
                return User(*api_key.split(":", 1))
            except Exception as e:
                app.logger.error('wrong api key: %r, %r', api_key, e)
                return None
    return None
app.login_response = Response(
    "need auth.", 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}
)

@app.context_processor
def utility_processor():
    def format_paging_url(url, query, page):
        if not query:
            query = {"page": str(page)}
        else:
            query['page'] = str(page)
        return utils.build_query(url, utils.url_encode(query))
    return dict(format_paging_url=format_paging_url)

@app.template_filter()
def time_func(ti):
    import time
    # ti=1516954700
    t=time.localtime(ti)
    return time.strftime('%Y-%m-%d %H:%M:%S',t)