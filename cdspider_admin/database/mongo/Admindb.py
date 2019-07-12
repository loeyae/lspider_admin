#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2019/4/10 13:43
"""
import time
from cdspider.libs import utils
from cdspider_admin.database.base import AdminDB as BaseAdmin
from cdspider.database.mongo.Mongo import Mongo

class AdminDB(Mongo, BaseAdmin):

    __tablename__ = 'admin'

    incr_key = 'admin'

    def __init__(self, connector, table=None, **kwargs):
        super(AdminDB, self).__init__(connector, table = table, **kwargs)
        collection = self._db.get_collection(self.table)
        indexes = collection.index_information()
        if 'uuid' not in indexes:
            collection.create_index('uuid', unique=True, name='uuid')
        if 'account' not in indexes:
            collection.create_index('account', unique=True, name='account')
        if 'status' not in indexes:
            collection.create_index('status', name='status')
        if 'ruleid' not in indexes:
            collection.create_index('ruleid', name='ruleid')
        user = self.get(where={"ruleid": self.ADMIN_RULE_ROOT})
        if not user:
            self.insert({"account": "admin@spider.me", "password": "2019@spider", "name": "admin", "ruleid":
                self.ADMIN_RULE_ROOT, "status": self.STATUS_ACTIVE})

    def insert(self, obj={}):
        obj['uuid'] = self._get_increment(self.incr_key)
        obj['password'] = self.build_password(obj['password'])
        obj.setdefault('status', self.STATUS_INIT)
        obj.setdefault('ctime', int(time.time()))
        obj.setdefault('utime', 0)
        obj.setdefault("ruleid", self.ADMIN_RULE_MANAGER)
        super(AdminDB, self).insert(obj);
        return obj['uuid']
    
    def update(self, id, obj):
        if "password" in obj and obj['password']:
            obj['password'] = self.build_password(obj['password'])
        obj['utime'] = int(time.time())
        return super(AdminDB, self).update(setting=obj, where={"uuid": int(id)}, multi=False)
    
    def update_many(self,obj, where=None):
        if where==None or where=={}:
            return
        if "password" in obj and obj['password']:
            obj['password'] = self.build_password(obj['password'])
        obj['utime'] = int(time.time())
        return super(AdminDB, self).update(setting=obj, where=where, multi=False)
    
    def active(self, id, where={}):
        if not where:
            where = {'uuid': int(id)}
        else:
            where.update({'uuid': int(id)})
        return super(AdminDB, self).update(setting={"status": self.STATUS_ACTIVE},
                                              where=where, multi=False)
    
    def disable(self, id, where={}):
        if not where:
            where = {'uuid': int(id)}
        else:
            where.update({'uuid': int(id)})
        return super(AdminDB, self).update(setting={"status": self.STATUS_INIT},
                                              where=where, multi=False)
    
    def delete(self, id, where={}):
        if not where:
            where = {'uuid': int(id)}
        else:
            where.update({'uuid': int(id)})
        return super(AdminDB, self).update(setting={"status": self.STATUS_DELETED},
                                              where=where, multi=False)
    
    def get_detail(self, id):
        return self.get(where={"uuid": int(id)})

    def get_detail_by_account(self, account):
        return self.get(where={"account": account})

    def get_list(self, where={}, select=None, **kwargs):
        kwargs.setdefault('sort', [('uuid', 1)])
        return self.find(where=where, select=select, **kwargs)

    def verify_user(self, account, password):
        user = self.get(where={"account": account})
        return self.build_password(password) == user['password'], user

    def build_password(self, password):
        md5str = "%s%s" % (password, utils.base64encode(password))
        return utils.md5(md5str);