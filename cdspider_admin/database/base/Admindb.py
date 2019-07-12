#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2019/4/10 13:43
"""
{
    "admin": {
        "uuid": int,
        "account": str,
        "password": str,
        "status": int,
        "ruleid": int,
        "ctime": int,
        "utime": int,
    }
}

from cdspider.database.base import Base

class AdminDB(Base):

    ADMIN_RULE_NONE = 0
    ADMIN_RULE_ROOT = 1
    ADMIN_RULE_MANAGER = 2

    def insert(self, obj={}):
        raise NotImplementedError

    def update(self, id, obj={}):
        raise NotImplementedError

    def update_many(self,obj, where=None):
        raise NotImplementedError

    def active(self, id, where={}):
        raise NotImplementedError

    def disable(self, id, where={}):
        raise NotImplementedError

    def delete(self, id, where={}):
        raise NotImplementedError

    def get_detail(self, id):
        raise NotImplementedError

    def get_detail_by_account(self, account):
        raise NotImplementedError

    def verify_user(self, mail, password):
        raise NotImplementedError

    def get_count(self, where={}, select = None, **kwargs):
        raise NotImplementedError

    def get_list(self, where={}, select = None, sort=[("pid", 1)], **kwargs):
        raise NotImplementedError
