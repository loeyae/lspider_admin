#! /usr/bin/python
#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

__author__="Zhang Yi <loeyae@gmail.com>"
__date__ ="$2019-04-09 23:10$"

from cdspider.run import *

@cli.command()
@click.option('--webui-instance', default='cdspider_admin.webui.app.app', callback=load_cls,
              help='webui Flask Application instance to be used.')
@click.option('--host', default='0.0.0.0', help='webui bind to host')
@click.option('--port', default=5000, help='webui bind to host')
@click.option('--scheduler-rpc', default=None, help='schedule rpc server')
@click.option('--spider-rpc', default=None, help='spider rpc server')
@click.option('--need-auth', is_flag=True, default=False, help='need username and password')
@click.option('--username', help='username of lock -ed projects')
@click.option('--password', help='password of lock -ed projects')
@click.option('--process-time-limit', default=30, help='script process time limit in debug')
@click.pass_context
def web(ctx, webui_instance, host, port, scheduler_rpc, spider_rpc, need_auth, username, password,
        process_time_limit, get_object=False):
    """
    采集系统可视化管理
    """
    app = load_cls(None, None, webui_instance)
    g = ctx.obj
    if username:
        app.config['webui_username'] = username
    if password:
        app.config['webui_password'] = password

if __name__ == "__main__":
    main()