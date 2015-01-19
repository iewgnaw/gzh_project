# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def redis_conf():
    return {
        'host': '127.0.0.1',
        'port': '6379',
        'db': 0,
    }


def redis_set():
    return "proxy_pool"

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:31.0) Gecko/20100101\
             Firefox/31.0'
HEADER = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Accept-Encoding': 'gzip, deflate',
}


def proxy_sites():
    return [
        #'http://www.kuaidaili.com/free/inha/1/',
        #'http://www.kuaidaili.com/free/inha/2/',
        #'http://www.kuaidaili.com/free/inha/3/',
        #'http://www.kuaidaili.com/free/inha/4/',
        #'http://www.kuaidaili.com/free/inha/5/',

        #'http://proxy.com.ru/gaoni/list_1.html',
        #'http://proxy.com.ru/gaoni/list_2.html',
        #'http://proxy.com.ru/gaoni/list_3.html',
        #'http://proxy.com.ru/gaoni/list_4.html',
        'http://proxy.com.ru/gaoni/list_5.html',

        'http://cn-proxy.com/',
        #'http://proxy.ipcn.org/proxylist.html',

        #'http://www.nianshao.me/?page=1',
        #'http://www.nianshao.me/?page=2',
        #'http://www.nianshao.me/?page=3',
        #'http://www.nianshao.me/?page=4',
        'http://www.nianshao.me/?page=5',
        'http://www.71https.com/?stype=1',
    ]
