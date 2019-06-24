#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2019-04-09 23:19
"""

import base64
from flask import request, Response, url_for, render_template, redirect, flash, abort, g
try:
    import flask_login as login
except ImportError:
    from flask.ext import login

try:
    from flask_login.utils import login_user, logout_user
except ImportError:
    from flask.ext.login.utils import login_user, logout_user
from cdspider_admin.database.base import AdminDB
from .app import app, User

@app.route('/login', methods=['POST', 'GET'])
def signin():
    error = None
    if request.method == 'POST':
        user = User(request.form['email'], request.form['password'])
        if user.is_authenticated:
            login_user(user, remember=request.form.get('remember', False))
            flash('Logged in successfully.')

            next = request.args.get('next')
#            if not next_is_valid(next):
#                return abort(400)
            return redirect(next or url_for("index"))
        else:
            error = '无效的用户名/密码'
    return render_template('signin.html', error = error)

@app.route('/register', methods=['POST', 'GET'])
def signup():
    error = None
    if request.method == 'POST':
        admindb = app.config.get("admindb")
        aid = admindb.insert({
                    "email": request.form['email'],
                    "password": request.form['password'],
                    "ruleid": AdminDB.ADMIN_RULE_NONE,
                    })
        if aid:
            return redirect(url_for("signin"))
        else:
            error = '无效的用户名/密码'
    return render_template('signup.html', error=error)

@app.route("/logout", methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for("signin"))
