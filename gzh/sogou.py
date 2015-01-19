# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
import os
import time
import json
import random
import logging
from xml.etree import ElementTree as ET

#from PIL import Image
import requests
from bs4 import BeautifulSoup

from django.conf import settings

from proxypool.proxypool import ProxyPool
from utils import grab_img_with_qiniu

GZH_IMAGE_ABS = os.path.join(settings.STATIC_ROOT, "images/gzh")  #the absulute path to save pic
POST_IMAGE_ABS = os.path.join(settings.STATIC_ROOT, "images/post")
GZH_STATIC_URL = os.path.join(settings.STATIC_URL, "images/gzh")     #the static url for zgh pic(logo, qr_code)
POST_STATIC_URL = os.path.join(settings.STATIC_URL, "images/post")

INDEX_URL = "http://weixin.sogou.com/"
POST_URL  = "http://weixin.sogou.com/weixin"

USER_AGENTS = ["Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36",
               "Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0",
               "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:24.0) Gecko/20100101 Firefox/24.0",
               "Mozilla/5.0 (compatible; WOW64; MSIE 10.0; Windows NT 6.2)",
               "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)",
               "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)"]

class GZHSoGou(object):
    def __init__(self):
        self.request = requests.Session()
        self.request.headers.update({
            "Accept"            : "*/*",
            "Accept-Encoding"   : "gzip, deflate",
            "Connection"        : "keep-alive",
            "User-Agent"        : random.choice(USER_AGENTS),
            })
        if not os.path.isdir(GZH_IMAGE_ABS): os.makedirs(GZH_IMAGE_ABS)
        if not os.path.isdir(POST_IMAGE_ABS): os.makedirs(POST_IMAGE_ABS)

    def make_post_data(self, query):
        '''
        visit weixin.sogou.com first, make the query post data
        '''
        response = self.request.get(INDEX_URL)
        soup = BeautifulSoup(response.text)
        asf = soup.find("input", attrs={"name": "_asf"}).get('value')
        ast = soup.find("input", attrs={"name": "_ast"}).get('value')
        w   = soup.find("input", attrs={"name": "w"}).get('value')
        p   = soup.find("input", attrs={"name": "p"}).get('value')
        ie  = soup.find("input", attrs={"name": "ie"}).get('value')

        post_data = {"_asf"     : asf,
                     "_ast"     : ast,
                     "w"        : w,
                     "p"        : p,
                     "ie"       : ie,
                     "query"    : query.encode('gbk'),
                     "type"     :  "1"
                     }

        return post_data

    def get_gzh_data(self, query, query_id = None):
        '''
        make the search request, then parse the response html, get the wx_name wx_id openid logo_url qr_code_url
        '''
        post_data = self.make_post_data(query)
        r = self.request.post(POST_URL, data = post_data)
        if not r.ok:
            return None
        soup = BeautifulSoup(r.text)

        data = self.search_gzh(soup, query_id)
        if data: return data

        '''if the first page can not found the query, go to the next page '''
        next_page_tags = soup.find_all("a", id=re.compile("sogou_page_\d+"))
        for page_tag in next_page_tags:
            r = self.request.get("http://weixin.sogou.com/weixin" + page_tag['href'],
                        proxies={"http": ProxyPool.get()})
            soup = BeautifulSoup(r.text)
            data = self.search_gzh(soup, query_id)
            ''' if found the query, return '''
            if data:
                return data
        return None

    def search_gzh(self, soup, query_id):
        try:
            for item in soup.find_all(id=re.compile("sogou_vr_11002301_box")):
                openid =  re.search(r"/gzh\?openid=(.+$)", item.get('href')).group(1) #openid
                txt_box = item.select("div.txt-box")[0]
                wx_box = item.select("div.pos-box")[0]

                wx_name = txt_box.h3.text.strip()
                wx_id   = txt_box.h4.text.strip().replace(u'微信号：',"").strip()
                if wx_id != query_id: continue
                summary = txt_box.find("span",text="功能介绍：").next_sibling.text
                logo = grab_img_with_qiniu(wx_box('img')[0]['src'], "lg_%s" % wx_id)
                qr_code = grab_img_with_qiniu(wx_box('img')[1]['src'], "qr_%s" % wx_id)
                return {"wx_name": wx_name,
                        "wx_id":   wx_id,
                        "openid":  openid,
                        "summary":   summary,
                        "logo":    logo,
                        "qr_code": qr_code
                       }
        except Exception as ex:
            logging.warning("search gzh failed")
            logging.exception(ex)
        return None

    def _request_with_proxy(self, url, params, retry=10):
        while 1:
            proxy = ProxyPool.get()
            headers = {'Accept': '*/*',
                       'Accept-Encoding': '',
                       'Connection': 'keep-alive',
                       'Referer': 'http://weixin.sogou.com/gzh?openid=%s'
                                  %params['openid'],
                       'User-Agent': random.choice(USER_AGENTS)
                      }
            try:
                response = requests.get(url, params=params,
                                        proxies={"http":proxy},
                                        headers=headers,
                                        timeout=15
                                       )
                if "sogou.weixin.gzhcb" in response.text[:25]:
                    return response
                else:
                    raise Exception("html is not ok")
            except Exception as ex:
                ProxyPool.delete(proxy)
                logging.debug(ex)

    def update_post_list(self, openid, time_from=0):
        gzhjs_url = "http://weixin.sogou.com/gzhjs"
        p = {"cb": "sogou.weixin.gzhcb",
             "openid": openid,
             "page": 1,
             "t": int(round(time.time() * 1000))
            }
        response = self._request_with_proxy(gzhjs_url, p)

        updated_time_list= re.findall(r'\<lastModified\>(\d+)', response.text)
        last_updated = max([int(i) for i in updated_time_list])

        next_page = self.cleaning_data(response.text, time_from)
        #
        page = 1
        while next_page:
            #time.sleep(random.randint(50,200))
            page += 1
            p.update(page=page)
            p.update(t=int(round(time.time() * 1000)))
            response = self._request_with_proxy(gzhjs_url, p)
            next_page = self.cleaning_data(response.text, time_from)
        return last_updated

    def cleaning_data(self, text, time_from):
        '''
        返回解析之后的数据。
        '''
        from tasks import GrabPost
        next_page = True
        dic_text = re.search(r'sogou.weixin.gzhcb\(({.+})\)',text).group(1)
        data_utf8 = dic_text.replace('encoding=\\"gbk\\"','encoding=\\"utf-8\\"')
        dic_data = json.loads(data_utf8)

        #the last page
        if dic_data['totalPages'] == dic_data['page']:
            next_page = False
        for item in dic_data['items']:
            doc = ET.fromstring(item.encode('utf-8'))
            last_modified = int(doc.find('item/display/lastModified').text)
            openid = doc.find('item/display/openid').text
            if last_modified <= time_from:
                next_page = False
                continue
            url = doc.find('item/display/url').text
            GrabPost.delay(url, openid)
        return next_page
