# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import time
import logging
logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from redis_manager import RedisManager
from . import config
from .crawler import Crawler


class ProxyPool(object):

    rd_session = RedisManager.get_instance()

    @classmethod
    def monitor(cls):
        while 1:
            if cls.rd_session.scard(config.redis_set()) == 0:
                logger.info("crawl proxy begin")
                cls._crawl()
                logger.info("crawl proxy end")
            time.sleep(1)

    @classmethod
    def _crawl(cls):
        Crawler().run()

    @classmethod
    def get(cls, block=True, timeout=None):
        if not block:
            return cls.rd_session.srandmember(config.redis_set())
        elif timeout is None:
            proxy = cls.rd_session.srandmember(config.redis_set())
            while proxy is None:
                proxy = cls.rd_session.srandmember(config.redis_set())
            return proxy
        elif timeout < 0:
            raise ValueError("'timeout' must be a non-negative number")
        else:
            endtime = time.time() + timeout
            proxy = cls.rd_session.srandmember(config.redis_set())
            while proxy is None:
                if time() > endtime:
                    return None
                proxy = cls.rd_session.srandmember(config.redis_set())
            return proxy

    @classmethod
    def size(cls):
        return cls.rd_session.scard(config.redis_set())

    @classmethod
    def delete(cls, proxy):
        cls.rd_session.srem(config.redis_set(), proxy)

    @classmethod
    def empty(cls):
        cls.rd_session.delete(config.redis_set())


if __name__ == "__main__":
    ProxyPool.monitor()
