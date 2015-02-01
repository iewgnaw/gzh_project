# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import time
import re
import logging
import redis

from django.core.mail import EmailMessage
from django.conf import settings
from django.db import IntegrityError
from django.core.paginator import Paginator
from gzh.kindlemobi.kindlereader import generate_mobi_file
import smtplib

import requests
from celery import shared_task
from celery.task import PeriodicTask, Task
from celery.task.schedules import crontab
from bs4 import BeautifulSoup
from gevent import monkey
monkey.patch_all(thread=False)
from gevent.pool import Pool
# python manage.py celeryd -l info

from .sogou import GZHSoGou
from proxypool.proxypool import ProxyPool
from utils import grab_low_quality_img
from .models import GongZhongHao, Post, UserProfile

REDIS_SESSION = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD
)

IMG_HASH = "images"

from celery.utils.log import get_task_logger
logger = get_task_logger('celery_task')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
file_handler = logging.handlers.RotatingFileHandler(
    '/var/log/celery_task.log',
    maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


@shared_task
def add_gzh(wx_id, wx_name, category):
    logger.info(wx_name)
    if not GongZhongHao.objects.filter(wx_id=wx_id):
        data = GZHSoGou().get_gzh_data(wx_name, wx_id)
        if not data:
            logger.info("can not get info for %s-%s" % (wx_name, wx_id))
        else:
            GongZhongHao.objects.create(
                wx_id=data.get('wx_id'), wx_name=data.get('wx_name'),
                openid=data.get('openid'), summary=data.get('summary'),
                logo=data.get('logo'), qr_code=data.get('qr_code'),
                category=category)


class UpdatePost(PeriodicTask):
    run_every = crontab(**settings.UPDATE_CRONTAB)

    def run(self, *kwargs):
        update_pool = Pool(5)
        logger.info("update posts start")
        gzhs = GongZhongHao.objects.all()
        update_pool.map(self.update_gzh, gzhs)
        logger.info("update posts end")

    def update_gzh(self, gzh):
        logger.info("update %s start" % gzh.wx_name)
        last_updated = GZHSoGou().update_post_list(
            gzh.openid,
            time_from=gzh.last_updated)
        logger.info("update %s end" % gzh.wx_name)
        gzh.last_updated = int(last_updated) + 1
        gzh.save(update_fields=['last_updated'])


class GrabPost(Task):

    def run(self, url, openid):
        data = self._grab_post_data(url)
        self.save_to_db(openid, data)

    def _request_with_proxy(self, url):
        while 1:
            proxy = ProxyPool.get()
            use_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X)\
                         AppleWebKit/600.1.4 (KHTML, like Gecko)\
                         Mobile/12A365 MicroMessenger/6.0 NetType/WIFI"
            headers = {"User-Agent": use_agent}
            try:
                response = requests.get(url,
                                        proxies={"http": proxy},
                                        headers=headers,
                                        timeout=15)
                if "<!DOCTYPE html>" in response.text[:20]:
                    return response.text
                else:
                    ProxyPool.delete(proxy)
            except:
                ProxyPool.delete(proxy)

    def _grab_post_data(self, url):

        html = self._request_with_proxy(url)
        soup = BeautifulSoup(html)
        article = soup.find(id="js_article")

        # re
        re_for_last_modified = re.compile(r'var ct = \"(\d+)\"')
        re_for_cover = re.compile(r'var msg_cdn_url = \"(.+)\"')
        re_for_summary = re.compile(r'var msg_desc = \"(.+)\"')
        re_for_title = re.compile(r'var msg_title = \"(.+)\"')
        re_for_biz = re.compile(r'__biz=(.+?)==')
        re_for_msgid = re.compile(r'(mid|appmsgid)=(?P<mid>\d+).+'
                                  r'(idx|itemidx)=(?P<idx>\d+)')
        biz = re_for_biz.search(url).group(1)
        doc_id = "_".join([biz] + re_for_msgid.search(url).groupdict().values())
        last_modified = re_for_last_modified.search(html).group(1)
        summary = BeautifulSoup(re_for_summary.search(html).group(1)).text
        title = BeautifulSoup(re_for_title.search(html).group(1)).text
        cover = re_for_cover.search(html).group(1)
        # ih = ImageHandler(cover_url)
        # cover = ih.download("%s_0" %doc_id)
        # ih.compress()

        # parse content
        clean_tags = ['script']
        clean_ids = ['js_toobar', 'js_pc_qr_code', 'js_ad_area']
        for tag_id in clean_ids:
            tag = article.find(id=tag_id)
            if tag:
                tag.decompose()
        for tag in clean_tags:
            for s in article.find_all(tag):
                s.decompose()

        for img_tag in article.find_all("img"):
            if img_tag.has_attr("src"):
                img_tag['data-src'] = img_tag['src'].replace('?tp=webp', '')
                del img_tag['src']
            elif img_tag.has_attr("data-src"):
                img_tag['data-src'] = img_tag['data-src'].replace('?tp=webp', '')
            else:
                img_tag.decompose()
        div_media = article.find(id="media")
        if div_media is not None:
            div_cover = BeautifulSoup('''<img class="rich_media_thumb"
                            id="js_cover" data-src="%s"/>''' % cover)
            div_media.insert(1, div_cover)
        content = unicode(article)
        data = {"doc_id":        doc_id,
                "title":         title,
                "url":           url,
                "summary":       summary,
                "cover":         cover,
                "last_modified": last_modified,
                "content":      content}
        return data

    def save_to_db(self, openid, data):
        try:
            gongzhonghao = GongZhongHao.objects.get(openid=openid)
            data.update({'gongzhonghao_id': gongzhonghao.id})
            Post(**data).save()
        except IntegrityError as ex:
            old_post = Post.objects.get(doc_id=data['doc_id'])
            if old_post.last_modified < data['last_modified']:
                for(key, value) in data.items():
                    setattr(old_post, key, value)
                old_post.save()
            else:
                pass
        except Exception as ex:
            logger.warning("save to db falied: %s" % data.get('url'))
            logger.exception(ex)


class MakeMobiTask(PeriodicTask):
    run_every = crontab(**settings.EMAIL_CRONTAB)

    def run(self, **kwargs):
        for userprofile in UserProfile.objects.filter(delivery=True):
            mail_to = userprofile.kindle_email

            if not userprofile.yesterday_updated_feeds():
                return None

            updated_feeds = [
                {'idx': index,
                 'entries': self.get_formated_entries(gzh),
                 'title': gzh.wx_name}
                for (index, gzh) in enumerate(userprofile.yesterday_updated_feeds())
            ]

            try:
                mobi_file = generate_mobi_file(updated_feeds)
            except Exception as ex:
                logger.warning("generate mobi falied for user %s" % mail_to)
                logger.exception(ex)
                return
            if mobi_file is not None:
                try:
                    logger.info('START: send email -> %s' % mail_to)
                    self.send_mail(mobi_file, mail_to)
                    logger.info('END: send email -> %s' % mail_to)
                except smtplib.SMTPException, ex:
                    logger.warning("send email falied for user %s" % mail_to)
                    logger.exception(ex)

    def get_formated_entries(self, gzh):
        entries = [
            {'idx': index,
             'title': post.title,
             'url':  post.url,
             'published': time.strftime(
                             "%Y-%m-%d",
                             time.localtime(post.last_modified)),
             'content': self.parse_content(post.content),
             'author': gzh.wx_name,
             'stripped': post.summary}
             for (index, post) in enumerate(gzh.yesterday_posts())
        ]
        return entries

    def parse_content(self, content):
        remove_tags = ['script', 'object', 'video', 'embed', 'iframe',
                       'noscript', 'style']
        remove_attributes = ['class', 'id', 'title', 'style', 'width',
                             'height', 'onclick']

        soup = BeautifulSoup(content).find(id="page-content")
        for span in list(soup.find_all(attrs={"style": "display: none;"})):
            span.extract()
        for attr in remove_attributes:
            for x in soup.find_all(attrs={attr: True}):
                del x[attr]
        for tag in soup.find_all(remove_tags):
            tag.extract()
        for img in soup.find_all("img"):
            if img.has_attr("data-src"):
                img['src'] = self._local_img_path(img['data-src'])
                del img['data-src']
            elif img.has_attr("src"):
                img['src'] = self._local_img_path(img['src'])
            else:
                img.extract()
        return unicode(soup)

    def _local_img_path(self, url):
        return REDIS_SESSION.hget(IMG_HASH, url)

    def send_mail(self, attach, mail_to):
        kwargs = {'subject':    u'%s_%s'
                        % (settings.MOBI_TITLE,
                          time.strftime('%y-%m-%d', time.localtime(time.time()))),
                  'body':       u'hello',
                  'to':         [mail_to]
                 }
        msg = EmailMessage(**kwargs)
        msg.attach_file(attach)
        try:
            msg.send(fail_silently=False)
        except smtplib.SMTPException:
            logger.warning("send %s failed" % attach)
            raise


class MakeLocalImage(PeriodicTask):

    run_every = crontab(**settings.LIMAGE_CRONTAB)

    def run(self):
        all_gzhs = GongZhongHao.objects.all()
        paginator = Paginator(all_gzhs, 50)
        for page in xrange(1, paginator.num_pages+1):
            per_page_gzhs = paginator.page(page)
            for gzh in per_page_gzhs:
                self._make_yesterday_local_image(gzh)

    def _make_yesterday_local_image(self, gzh):
        pool = Pool()
        for post in gzh.yesterday_posts():
            imgs_src = [img_tag['data-src'] for img_tag in
                        BeautifulSoup(post.content).find_all('img')]
            pool.map(grab_low_quality_img, imgs_src)
