# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2019/6/20 15:23
"""
import re
import json
import copy
import urllib.parse
from cdspider.libs import utils as cdutils
from cdspider.exceptions import *

def build_parse_other(formdata, prefix):
    l = len(prefix)
    data = {}
    for k, v in formdata.items():
        if k.startswith(prefix) and v:
            _k = k[l:]
            if _k.startswith('name-'):
                _k = _k[5:]
                if _k in data:
                    data[_k]['name'] = v
                else:
                    data.update({_k: {"name": v}})
            else:
                if _k.endswith("-extract"):
                    _k = _k[:-8]
                    if _k in data:
                        data[_k].update({"extract": v})
                    else:
                        data.update({_k:{"extract": v}})

                else:
                    if _k in data:
                        data[_k].update({"filter": v, "type": "text"})
                    else:
                        data.update({_k:{"filter": v, "type": "text"}})
    return data

def build_get_data(data, formdata, prefix):
    key = "%s-get" % prefix
    if key in formdata and formdata[key]:
        carr = re.split('(?:(?:\r\n)|\r|\n)', formdata[key])
        if len(carr) > 1:
            if not "hard_code_list" in  data['request']:
                data['request']['hard_code_list'] = []
            for item in carr:
                query = cdutils.query2dict(item)
                posts = []
                for k, v in query.items():
                    posts.append({
                        'name': k,
                        'type': 'url',
                        'value': v,
                    })
                data['request']['hard_code_list'].append(posts)
        else:
            query = cdutils.query2dict(carr[0])
            for k, v in query.items():
                data['request']['hard_code'].append({
                    'name': k,
                    'type': 'url',
                    'value': v,
                })

def build_post_data(data, formdata, prefix):
    key = "%s-post" % prefix
    if key in formdata and formdata[key]:
        carr = re.split('(?:(?:\r\n)|\r|\n)', formdata[key])
        if len(carr) > 1:
            if not "hard_code_list" in  data['request']:
                data['request']['hard_code_list'] = []
            for item in carr:
                query = cdutils.query2dict(item)
                posts = []
                for k, v in query.items():
                    posts.append({
                        'name': k,
                        'type': 'data',
                        'value': v,
                    })
                data['request']['hard_code_list'].append(posts)
        else:
            query = cdutils.query2dict(carr[0])
            for k, v in query.items():
                data['request']['hard_code'].append({
                    'name': k,
                    'type': 'data',
                    'value': v,
                })

def build_headers_data(data, formdata, prefix):
    key = "%s-headers" % prefix
    if key in formdata and formdata[key]:
        carr = re.split('(?:(?:\r\n)|\r|\n)', formdata[key])
        if len(carr) > 1:
            data['request']['headers_list'] = []
            for item in carr:
                data['request']['headers'].append(cdutils.mgkeyconvert(cdutils.query2dict(item)))
        else:
            query = cdutils.query2dict(carr[0])
            data['request']['headers'] = cdutils.mgkeyconvert(query)

def build_cookies_data(data, formdata, prefix):
    key = "%s-cookies" % prefix
    if key in formdata and formdata[key]:
        carr = re.split('(?:(?:\r\n)|\r|\n)', formdata[key])
        if len(carr) > 1:
            data['request']['cookies_list'] = []
            for item in carr:
                data['request']['cookies'].append(cdutils.mgkeyconvert(cdutils.query2dict(item)))
        else:
            cookies = cdutils.query2dict(carr[0])
            data['request']['cookies'] = cdutils.mgkeyconvert(cookies)


def build_unique_data(formdata):
    data = {}
    if 'list-unique-url' in formdata and formdata['list-unique-url']:
        data['url'] = formdata['list-unique-url']
    if 'list-unique-query' in formdata and formdata['list-unique-query']:
        data['query'] = dict.fromkeys(formdata['list-unique-query'].split("|"))
    if 'list-unique-data' in formdata and formdata['list-unique-data']:
        data['data'] = dict.fromkeys(formdata['list-unique-data'].split("|"))
    if data:
        return data
    return None

def build_paging_data(data, formdata, prefix):
    data['paging'] = {
        "url": {
            "type": formdata.get("%s-url-type" % prefix, 'base'),
            "filter": formdata.get("%s-url-filter" % prefix, None),
        },
        "max": formdata.get("%s-max" % prefix, 0),
        "first": formdata.get("%s-first" % prefix, 0),
    }
    rule_name = formdata.get("%s-rule-name" % prefix, None)
    if rule_name:
        data['paging']["rule"] = [
            {
                "mode": formdata.get("%s-rule-mode" % prefix, None),
                "name": rule_name,
                "value": formdata.get("%s-rule-value" % prefix, 0),
                "step": formdata.get("%s-rule-step" % prefix, 0),
                "patch": formdata.get("%s-rule-patch" % prefix, 0),
                "first": formdata.get("%s-rule-first" % prefix, 0)
            }
        ]


def build_base_data(formdata):
    return formdata

def build_list_data(formdata):
    data = {
        "request": {
            "crawler": formdata.get('list-request-crawler', 'requests'),
            "method": formdata.get('list-request-method', 'GET').upper() if formdata.get('list-crawler', 'requests') == 'requests' else 'open',
            "url": 'base_url',
            "proxy": formdata.get('list-request-proxy', 'auto')
        }
    }
    data['request']['hard_code'] = []
    if 'list-request-keyword-key' in formdata and formdata['list-request-keyword-key']:
        data['request']['hard_code'].append({
            'key': formdata['list-request-keyword-key'],
            'mode': formdata.get('list-request-keyword-mode', 'url'),
            'attr': 'keyword',
        })

    build_get_data(data, formdata, 'list-request')
    build_post_data(data, formdata, 'list-request')
    build_headers_data(data, formdata, 'list-request')
    build_cookies_data(data, formdata, 'list-request')
    build_paging_data(data, formdata, 'list-paging')

    if 'list-parse-filter' in formdata and formdata['list-parse-filter']:
        data['parse'] = {
            'filter': formdata['list-parse-filter'],
            'onlyOne': 0,
            'item': {
                'title': {
                    'filter': formdata.get('list-parse-title', ''),
                    'extract': formdata.get('list-parse-title-extract', ''),
                    'type': 'text',
                },
                'url': {
                    'filter': formdata.get('list-parse-url', 'a'),
                    'type': 'attr',
                    'target': 'href',
                    'prefix': formdata.get('list-parse-url-prefix', ''),
                    'suffix': formdata.get('list-parse-url-prefix', ''),
                    'patch': formdata.get('list-parse-url-patch', ''),
                },
            }
        }
    elif 'list-parse-url' in formdata and formdata['list-parse-url']:
        data['parse'] = {
            'onlyOne': 0,
            'item': {
                'title': {
                    'filter': formdata.get('list-parse-title', ''),
                    'extract': formdata.get('list-parse-title-extract', ''),
                    'type': 'text',
                },
                'url': {
                    'filter': formdata['list-parse-url'],
                    'type': 'attr',
                    'target': 'href',
                    'prefix': formdata.get('list-parse-url-prefix', ''),
                    'suffix': formdata.get('list-parse-url-prefix', ''),
                    'patch': formdata.get('list-parse-url-patch', ''),
                },
            }
        }
    else:
        data['parse'] = {
            "onlyOne": 0,
            "item": {}
        }

    if 'list-parse-author' in formdata and formdata['list-parse-author']:
        data['parse']['item'].update({
            "author": {
                'filter': formdata.get('list-parse-author'),
                'extract': formdata.get('list-parse-author-extract', ''),
                'type': 'text',
            }
        })
    if 'list-parse-pubtime' in formdata and formdata['list-parse-pubtime']:
        data['parse']['item'].update({
            "pubtime": {
                'filter': formdata.get('list-parse-pubtime'),
                'extract': formdata.get('list-parse-pubtime-extract', ''),
                'type': 'text',
            }
        })
    other_parse = build_parse_other(formdata, 'list-parse-other-')
    if other_parse:
        data['parse']['item'].update(other_parse)
    data['url'] = {
        "base": formdata.get('list-url-base'),
        "mode": formdata.get('list-url-mode'),
        "name": formdata.get('list-url-name'),
    }
    list_url_parse = build_parse_other(formdata, 'list-url-parse-')
    if list_url_parse:
        data['url']['parse'] = list_url_parse
    data['unique'] = build_unique_data(formdata)
    return data

def build_item_data(formdata):
    data = {
        "request": {
            "crawler": formdata.get('item-request-crawler', 'requests'),
                "method": formdata.get('item-request-method', 'GET').upper() if formdata.get('item-crawler', 'requests') == 'requests' else 'open',
                "url": 'base_url',
                "proxy": formdata.get('item-request-proxy', 'auto'),
            }
    }
    data['request']['hard_code'] = []
    build_get_data(data, formdata, 'item-request')
    build_post_data(data, formdata, 'item-request')
    build_headers_data(data, formdata, 'item-request')
    build_cookies_data(data, formdata, 'item-request')
    build_paging_data(data, formdata, 'item-paging')

    data['parse'] = {
    }
    if 'item-parse-content' in formdata and formdata['item-parse-content']:
        data['parse'].update({
            'content': {
                'filter': formdata.get('item-parse-content'),
                'type': 'text',
            }
        })
    if 'item-parse-title' in formdata and formdata['item-parse-title']:
        data['parse'].update({
            "title": {
                'filter': formdata.get('item-parse-title'),
                'extract': formdata.get('list-parse-title-extract', ''),
                'type': 'text',
            }
        })
    if 'item-parse-author' in formdata and formdata['item-parse-author']:
        data['parse'].update({
            "author": {
                'filter': formdata.get('item-parse-author'),
                'extract': formdata.get('list-parse-author-extract', ''),
                'type': 'text',
            }
        })
    if 'item-parse-pubtime' in formdata and formdata['item-parse-pubtime']:
        data['parse'].update({
            "pubtime": {
                'filter': formdata.get('item-parse-pubtime'),
                'extract': formdata.get('list-parse-pubtime-extract', ''),
                'type': 'text',
            }
        })

    other_parse = build_parse_other(formdata, 'item-parse-other-')
    if other_parse:
        data['parse'].update(other_parse)
    return data

def build_script_data(formdata):
    script = urllib.parse.unquote(formdata.get('script'))
    #禁止使用的方法
    # os系列 sys系列 file系列 commands系列
    # eavl dir open globals locals
    # 数据库 和 queue 操作系列
    # connect方法 mongo mysql
    g = re.search(r'\s(?:(?:(?:os|sys|file|commands)\040*\.\040*(?:[a-z\.]+\040*)+\()|(?:eval|dir|open|globals|locals)\040*\(|self\040*\.\040*[a-z]+(?:db|queue)\040*\.\040*[a-z]+\040*\(|(?:connect|mongo|mysql|redis))', script)
    if g:
        raise CDSpiderHandlerForbiddenWord()
    data = {"script": script.strip()}
    if 'type' in formdata:
        data['type'] = formdata['type']
    return data

def build_rule_data(mode, formdata):
    if mode == 'rule-list':
        return build_list_data(formdata)
    elif mode == 'rule-script':
        return build_script_data(formdata)
    return build_base_data(formdata)

def build_parser_data(mode, formdata):
    if mode == 'parser-item':
        return build_item_data(formdata)
    elif mode == 'parser-script':
        return build_script_data(formdata)
    return build_base_data(formdata)


def build_form_unique_data(data):
    if 'unique' in data and data['unique']:
        return {
            'url': data['unique'].get('url', ''),
            'query': '|'.join(data['unique']['query'].keys()) if "query" in data['unique'] and data['unique']['query'] else '',
            'data': '|'.join(data['unique']['data'].keys()) if "data" in data['unique'] and data['unique']['data'] else '',
        }
    return {'url': '', 'query': '', 'data': ''}

def build_form_params_data(data):
    data['request']['keyword'] = {}
    data['request']['get_data'] = ''
    data['request']['post_data'] = ''
    data['request']['headers_data'] = ''
    data['request']['cookies_data'] = ''
    if 'hard_code_list' in data['request']:
        get_data_list = []
        post_data_list = []
        for hard_code in data['request']['hard_code_list']:
            get_data = {}
            post_data = {}
            for item in hard_code:
                if item['type'] == 'url':
                    get_data[item['name']] = item['value']
                elif item['type'] == 'data':
                    post_data[item['name']] = item['value']
            if get_data:
                get_data_list.append(cdutils.url_encode(get_data))
            if post_data:
                post_data_list.append(cdutils.url_encode(post_data))
        if get_data_list:
            data['request']['get_data'] = '\r\n'.join(get_data_list)
        if post_data_list:
            data['request']['post_data'] = '\r\n'.join(post_data_list)
    elif 'hard_code' in data['request']:
        get_data = {}
        post_data = {}
        for item in data['request']['hard_code']:
            if 'attr' in item and item['attr'] == 'keyword':
                data['request']['keyword'] = {
                    'key': item['key'],
                    'mode': item['mode'],
                }
            elif item['type'] == 'url':
                get_data[item['name']] = item['value']
            elif item['type'] == 'data':
                post_data[item['name']] = item['value']
        if get_data:
            data['request']['get_data'] = cdutils.url_encode(get_data)
        if post_data:
            data['request']['post_data'] = cdutils.url_encode(post_data)
    if 'headers_list' in data['request']:
        headers_list = []
        for headers in data['request']['headers_list']:
            headers_list.append(cdutils.url_encode(headers))
        if headers_list:
            data['request']['headers_data'] = '\r\n'.join(headers_list)
    elif 'headers' in data['request']:
        data['request']['headers_data'] = cdutils.url_encode(data['request']['headers'])
    if 'cookies_list' in data['request']:
        cookies_list = []
        for cookies in data['request']['cookies_list']:
            cookies_list.append('&'.join(cdutils.url_encode(cookies)))
        if cookies_list:
            data['request']['cookies_data'] = '\r\n'.join(cookies)
    elif 'cookies' in data['request']:
        data['request']['cookies_data'] = cdutils.url_encode(data['request']['cookies'])

def build_form_data(data):
    data['unique'] = build_form_unique_data(data)
    if 'request' in data and data['request']:
        build_form_params_data(data)
    else:
        data['request'] = {}
    if not 'paging' in data or not data['paging']:
        data['paging'] = {}
    if not 'url' in data or not data['url']:
        data['url'] = {}
    if 'parse' in data and data['parse']:
        parser = data['parse']
        data['parse'] = {}
        data['parse']['filter'] = parser.get('filter', '')
        if 'item' in parser and 'title' in parser['item']:
            title_rule = parser['item'].pop('title', {})
            data['parse']['title'] = title_rule.get('filter', '')
            data['parse']['title_extract'] = title_rule.get('extract', '')
        else:
            data['parse']['title'] = parser.get('title', {}).get('filter', '')
            data['parse']['title_extract'] = parser.get('title', {}).get('extract', '')
        if 'item' in parser and "url" in parser['item']:
            url_rule = parser['item'].pop('url', {})
            data['parse']['url'] = url_rule.get('filter', '')
            data['parse']['url_patch'] = url_rule.get('patch', '')
        else:
            data['parse']['content'] = parser.get('content', {}).get('filter', '')
            data['parse']['content_extract'] = parser.get('content', {}).get('extract', '')
        if 'item' in parser and 'author' in parser['item']:
            author_rule = parser['item'].pop('author', {})
            data['parse']['author'] = author_rule.get('filter', '')
            data['parse']['author_extract'] = author_rule.get('extract', '')
        else:
            data['parse']['author'] = parser.get('author', {}).get('filter', '')
            data['parse']['author_extract'] = parser.get('author', {}).get('extract', '')
        if 'item' in parser and 'pubtime' in parser['item']:
            pubtime_rule = parser['item'].pop('pubtime', {})
            data['parse']['pubtime'] = pubtime_rule.get('filter', '')
            data['parse']['pubtime_extract'] = pubtime_rule.get('extract', '')
        else:
            data['parse']['pubtime'] = parser.get('pubtime', {}).get('filter', '')
            data['parse']['pubtime_extract'] = parser.get('pubtime', {}).get('extract', '')

        data['parse']['other'] = {}
        if 'item' in parser and parser['item']:
            for _k, val in parser['item'].items():
                data['parse']['other'][_k] = val
        elif parser:
            for _k, val in parser.items():
                data['parse']['other'][_k] = val
    else:
        data['parse'] = {}
    return data
