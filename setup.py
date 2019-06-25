#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

__author__ = "Zhang Yi <loeyae@gmail.com>"
__date__ = "$2019-04-09 23:02$"

from setuptools import setup, find_packages

setup(
    name='cdspider_admin',
    version='0.1',
    packages=find_packages(),
    url='https://github.com/loeyae/lspider_admin.git',
    license='Apache License, Version 2.0',
    author='Zhang Yi',
    author_email='loeyae@gmail.com',
    description='数据采集框架管理后台',
    install_requires = [
        'flask>=0.12.2',
        'flask_login>=0.4.1',
        'WsgiDAV==2.3.0',
        'cdspider>=0.1',
    ],
    entry_points={
        'console_scripts': [
            'cdspider_admin = cdspider_admin.run:main',
        ],
        'cdspider.dao.mongo': [
            'AdminDB=cdspider_admin.database.mongo.AdminDB',
        ]
    }
)
