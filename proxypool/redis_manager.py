# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import redis
import config


class RedisManager(object):

    rdb = None

    @staticmethod
    def get_instance():
        conf = config.redis_conf()
        if not RedisManager.rdb:
            RedisManager.rdb = redis.StrictRedis(
                host=conf['host'],
                port=conf['port'],
                db=conf['db'],
                password=conf['password']
            )
        return RedisManager.rdb
