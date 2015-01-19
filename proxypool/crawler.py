# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
import random
import logging
import requests
from gevent import monkey
monkey.patch_all(thread=False)
from gevent.pool import Pool

from . import config
from .redis_manager import RedisManager

RE_FOR_IP_PORT1 = re.compile(
    r'(?P<ip>(?:\d{1,3}\.){3}\d{1,3})</td>\n?\s*<td.*?>\s*(?P<port>\d{1,4})')
RE_FOR_IP_PORT2 = re.compile(
    r'(?:\d{1,3}\.){1,3}\d{1,3}:\d{1,3}')

SITE_POOL = Pool(2)
PROXY_CHECK_POOL = Pool(30)


def exception_handler(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return []
    return handler


class Crawler(object):

    def __init__(self):
        pass

    def run(self):
        proxy_sites = config.proxy_sites()
        random.shuffle(proxy_sites)
        proxies_list = SITE_POOL.map(self.crawl, proxy_sites)
        proxies = [item for sublist in proxies_list for item in sublist]
        avaliable_proxies = filter(
            lambda x: x,
            PROXY_CHECK_POOL.map(
                self._check_proxy_avaliable,
                proxies
            )
        )
        logging.info("Get %s avaliable proxies" % len(avaliable_proxies))
        self._save_to_redis(avaliable_proxies)

    @exception_handler
    def crawl(self, site_url):
        proxies = []
        config.HEADER.update({'Host': site_url.split('/')[2]})
        response = requests.get(site_url, headers=config.HEADER)

        if not response.ok:
            return []
        for match in RE_FOR_IP_PORT1.finditer(response.text):
            ip = match.groupdict()['ip']
            port = match.groupdict()['port']
            proxies.append("%s:%s" % (ip, port))
        for proxy in RE_FOR_IP_PORT2.findall(response.text):
            proxies.append(proxy)
        return proxies

    def _check_proxy_avaliable(self, proxy):
        test_url = 'http://www.google.cn/'
        try:
            r = requests.get(test_url, proxies={'http': proxy}, timeout=15)
            if '<title>Google</title>' in r.text[:100]:
                return proxy
            else:
                return None
        except Exception:
            return None

    def _save_to_redis(self, proxies):
        redis_session = RedisManager.get_instance()
        redis_session.sadd(config.redis_set(), *proxies)
