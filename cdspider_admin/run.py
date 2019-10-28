#! /usr/bin/python
#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

__author__="Zhang Yi <loeyae@gmail.com>"
__date__ ="$2019-04-09 23:10$"
import time
from cdspider.libs.constants import *
from cdspider.run import *

@cli.command()
@click.option('-w', '--where', callback=load_param, help="condition")
@click.option('-c', '--created', default=0, help="create time")
@click.pass_context
def build_result_work(ctx, where, created):
    if created == 0:
        created = int(time.time())
    rid = "0"
    while True:
        has_item = False
        where["rid"] = {"$gt": rid}
        result = ctx.obj['db']['ArticlesDB'].get_list(created, where=where, sort=[("rid", 1)])
        for item in result:
            has_item = True
            rid = item['rid']
            task = dict({
                "rid": item['rid'],
            })
            ctx.obj['queue'][QUEUE_NAME_SPIDER_TO_RESULT].put_nowait(task)
        if has_item is False:
            break


@cli.command()
@click.option('--spider_cls', default='cdspider.spider.Spider', callback=load_cls, help='spider name',
              show_default=True)
@click.option('-w', '--where', callback=load_param, help="condition")
@click.option('-c', '--created', default=0, help="create time")
@click.option('-i', '--interval', default=1, help="create time")
@click.option('-o', '--output', default=None, help='数据保存的文件', show_default=True)
@click.pass_context
def fetch_result_list(ctx, spider_cls, where, created, interval, output):
    """
    抓取文章测试结果
    """
    spider = load_cls(ctx, None, spider_cls)
    spider = spider(ctx, no_sync=True, handler=None, inqueue=False)
    if created == 0:
        created = int(time.time())
    rid = "0"
    while True:
        has_item = False
        where["rid"] = {"$gt": rid}
        result = ctx.obj['db']['ArticlesDB'].get_list(created, where=where, sort=[("rid", 1)])
        for item in result:
            has_item = True
            rid = item['rid']
            task = dict({
                "rid": item['rid'],
                "mode": (item.get("crawlinfo") or {}).get("mode", HANDLER_MODE_DEFAULT_ITEM)
            })
            task['return_result'] = False
            return_result = False
            if output:
                return_result = True
            ret = spider.fetch(task=task, return_result=return_result)
            if output:
                if output == "print":
                    print(ret)
                else:
                    f = open(output, 'w')
                    f.write(json.dumps(ret))
                    f.close()
            time.sleep(int(interval))
        if has_item is False:
            break


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
    app.config['runtime_dir'] = g.get('runtime_dir')
    app.config['need_auth'] = need_auth
    app.config['process_time_limit'] = process_time_limit
    app.config['context'] = ctx
    app.config['db'] = g.get("db")
    app.config['app_config'] = g.get('app_config', {})

    if 'frequencymap' in app.config['app_config'] and app.config['app_config']['frequencymap']:
        app.config['app_config']['frequencymap_sorted'] = sorted(app.config['app_config']['frequencymap'].items(), key=lambda d: int(d[0]))
    if 'sitetype' in app.config['app_config'] and app.config['app_config']['sitetype']:
            app.config['app_config']['sitetype_sorted'] = sorted(app.config['app_config']['sitetype'].items(),
                                                                  key=lambda d: int(d[0]))
    if 'expiremap' in app.config['app_config'] and app.config['app_config']['expiremap']:
            app.config['app_config']['expiremap_sorted'] = sorted(app.config['app_config']['expiremap'],
                                                                  key=lambda d: int(d[0]))

    if isinstance(scheduler_rpc, six.string_types):
        scheduler_rpc = connect_rpc(ctx, None, scheduler_rpc)
        app.config['scheduler_rpc'] = scheduler_rpc
        app.config['newtask'] = lambda x: scheduler_rpc.newtask(json.dumps(x))
        app.config['status'] = lambda x: scheduler_rpc.status(json.dumps(x))
        app.config['frequency'] = lambda x: scheduler_rpc.frequency(json.dumps(x))
        app.config['expire'] = lambda x: scheduler_rpc.expire(json.dumps(x))
    else:
        webui_scheduler = ctx.invoke(route, get_object=True)

        def newtask(x):
            return webui_scheduler.newtask(x)

        app.config['newtask'] = lambda x: newtask(x)

        def status(x):
            return webui_scheduler.status(x)
        app.config['status'] = lambda x: status(x)

        def frequency(x):
            return webui_scheduler.frequency(x)
        app.config['frequency'] = lambda x: frequency(x)

        def expire(x):
            return webui_scheduler.expire(x)
        app.config['expire'] = lambda x: expire(x)

    if isinstance(spider_rpc, six.string_types):
        spider_rpc = connect_rpc(ctx, None, spider_rpc)
        app.config['spider_rpc'] = spider_rpc
        app.config['fetch'] = lambda x: spider_rpc.fetch(json.dumps(x))
        app.config['task'] = lambda x: spider_rpc.task(json.dumps(x))
    else:
        webui_fetcher = ctx.invoke(fetch, get_object=True, no_input=True)

        def gfetch(x):
            r_obj = utils.__redirection__()
            sys.stdout = r_obj
            parsed = broken_exc = last_source = final_url = save = errmsg = None
            try:
                return_result = x.pop('return_result', False)
                ret = webui_fetcher.fetch(x, True)
                if ret and isinstance(ret, (list, tuple)) and isinstance(ret[0], (list, tuple)):
                    parsed, broken_exc, last_source, final_url, save = ret[0]
                else:
                    g['logger'].error(str(ret))
                if last_source:
                    last_source = utils.decode(last_source)
                if parsed and not return_result:
                    parsed = True
            except Exception as exc:
                errmsg = str(exc)
                broken_exc = traceback.format_exc()
                g['logger'].error(broken_exc)
            output = sys.stdout.read()
            result = {"parsed": parsed, "broken_exc": broken_exc, "source": last_source, "url": final_url, "save": save, "stdout": output, "errmsg": errmsg}

            return json.dumps(result)

        app.config['fetch'] = lambda x: gfetch(x)

        def gtask(x):
            message = x
            task = webui_fetcher.get_task(message, no_check_status=True)
            return task
        app.config['task'] = lambda x: gtask(x)

    app.config['queue'] = g.get("queue")
    app.config['queue_setting'] = g.get("message_queue")

    app.debug = g.get("debug", False)
    g['instances'].append(app)
    if get_object:
        return app

    app.run(host=host, port=port)

if __name__ == "__main__":
    main()