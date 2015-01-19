# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import time
import re

from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Category(models.Model):
    value = models.CharField(max_length=255)

    def __unicode__(self):
        return self.value

class GongZhongHao(models.Model):
    wx_name = models.CharField(max_length=50, db_index=True)
    wx_id   = models.CharField(max_length=30, db_index=True, unique=True)
    openid  = models.CharField(max_length=50, db_index=True, unique=True)
    summary = models.TextField()
    logo    = models.CharField(max_length=255)
    qr_code = models.CharField(max_length=255)
    last_updated = models.BigIntegerField(default=0)
    category = models.ForeignKey(Category)
    hots = models.BigIntegerField(default=0)

    def __unicode__(self):
        return self.wx_name

    def hot_plus(self, plus=1):
        self.hots += plus
        self.save()

    def yesterday_posts(self):
        now = int(time.time())
        return self.post_set.filter(last_modified__gte=now - 60*60*24)

class Post(models.Model):
    doc_id = models.CharField(max_length=100, db_index=True, unique=True)
    title  = models.CharField(max_length=200)
    url    = models.CharField(max_length=255, unique=True)
    summary= models.TextField()
    content = models.TextField()
    # ALTER TABLE gzh_post CHANGE content content longtext
        # CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    cover   = models.CharField(max_length=255)
    last_modified = models.BigIntegerField()
    ups = models.BigIntegerField(default=0)
    gongzhonghao = models.ForeignKey(GongZhongHao)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['-last_modified']

    def up_plus(self, plus=1):
        self.ups += plus
        self.save()

class WeiBoProfile(models.Model):
    access_token = models.CharField(max_length=64)
    uid = models.BigIntegerField()
    screen_name = models.CharField(max_length=191)
    avatar = models.CharField(max_length=255)

class UserProfile(models.Model):
    # This line is required. Links UserProfile to a User model instance.
    user = models.OneToOneField(User)
    weiboprofile = models.OneToOneField(WeiBoProfile, null=True)

    # The additional attributes we wish to include.
    subscribes = models.ManyToManyField(GongZhongHao)
    readed_posts = models.ManyToManyField(Post, related_name="readed_user_set")
    liked_posts = models.ManyToManyField(Post, related_name="liked_user_set")
    kindle_email = models.EmailField(max_length=255, blank=True)
    delivery = models.BooleanField(default=False)
    last_send = models.BigIntegerField(default=0)

    def __unicode__(self):
        return self.user.username

    def is_kindle_user(self):
        return re.search(r"\w+@kindle\.c", self.kindle_email) is not None

    def delivery_is_on(self):
        return self.delivery

    def need_delivery(self):
        return self.delivery_is_on()

    def yesterday_updated_feeds(self):
        feeds = []
        for feed in self.subscribes.all():
            if feed.last_updated >= int(time.time()) - 60*60*24:
                feeds.append(feed)
        return feeds

    def yesterday_updated_entries(self):
        return [feed.yesterday_posts() for feed in self.subscribes.all()]

    def is_weibo_user(self):
        return self.weiboprofile is not None

    def weibo_uid(self):
        return self.weiboprofile.uid

    def weibo_screen_name(self):
        return self.weiboprofile.screen_name

    def weibo_avatar(self):
        return self.weiboprofile.avatar

    def weibo_access_token(self):
        return self.weiboprofile.access_token
