# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime
import time
import os
from StringIO import StringIO
import imghdr
import uuid
import redis
import logging

from PIL import Image
import requests
from qiniu import Auth, BucketManager

from django.conf import settings

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

COMPRESSED_DIR = os.path.join(settings.STATIC_ROOT, "images/compressed")
GZH_IMAGE_ABS = os.path.join(settings.STATIC_ROOT, "images/gzh")
POST_IMAGE_ABS = os.path.join(settings.STATIC_ROOT, "images/post")
GZH_STATIC_URL = os.path.join(settings.STATIC_URL, "images/gzh")
POST_STATIC_URL = os.path.join(settings.STATIC_URL, "images/post")

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:34.0) Gecko/20100101 Firefox/34.0'

REDIS_SESSION = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD
)

IMG_HASH = "images"


def request_with_proxy(url, params=None):
    pass


def format_date(timestamp):
    offset_seconds = 8 * 60 * 60
    day_seconds = 24 * 60 * 60
    now = int(time.time())
    offset_day = (now + offset_seconds) / day_seconds - \
                 (timestamp + offset_seconds) / day_seconds
    if offset_day == 0:
        day = u'今天'
    elif offset_day == 1:
        day = u'昨天'
    elif time.localtime(timestamp).tm_year == datetime.now().year:
        day = time.strftime('%m月%d日', time.localtime(timestamp))
    else:
        day = time.strftime('%Y年%m月%d日', time.localtime(timestamp))
    minitues = time.strftime("%H:%M", time.localtime(timestamp))
    return "%s %s" % (day, minitues)


def download_img_content(url, retry_times=3):
    if url.endswith('?tp=webp'):
        url = url.replace('?tp=webp', '')
    while True:
        try:
            r = requests.get(url, timeout=25,
                             headers={"user-agent": USER_AGENT})
            return StringIO(r.content)
        except Exception as ex:
            retry_times -= 1
            if retry_times > 0:
                continue
            else:
                logging.warning("download image failed =>%s" % url)
                logging.exception(ex)
                raise ex


def grab_low_quality_img(url, quality=30):
    try:
        content = download_img_content(url)
    except:
        return None
    im_format = imghdr.what(content)
    im = Image.open(content)
    filename = str(uuid.uuid1()) + ".%s" % im_format
    file_path = os.path.join(COMPRESSED_DIR, filename)
    im.convert('L').save(file_path, quality=quality)
    REDIS_SESSION.hset(IMG_HASH, url, file_path)


def grab_img_with_qiniu(url, name):
    key = "images/%s.jpeg" % name
    q = Auth(settings.QINIU_ACCESSKEY.encode('ascii'),
             settings.QINIU_SECRETKEY.encode('ascii'))
    bucket = BucketManager(q)
    try:
        ret, info = bucket.fetch(url, settings.QINIU_BUCKET_NAME, key)
    except Exception:
        pass
    return key
