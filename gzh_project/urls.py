# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required

from django.contrib import admin
admin.autodiscover()

import gzh.urls
from gzh.views import (signin, logout, welcome, set_account, home,
                       mark_as_readed, weibo_login, weibo_auth, entry_up)

urlpatterns = patterns('',
    url('^$', include(gzh.urls)),
    url(r'^entry_up', entry_up),
    url(r'^mark_as_readed', mark_as_readed),
    url(r'^weibo_login', weibo_login),
    url(r'^weibo_auth', weibo_auth),
    url(r'^gzh/', include(gzh.urls)),
    url(r'^signin', signin, name="signin"),
    url(r'^welcome/', login_required(welcome), name="welcome"),
    url(r'^logout/$', login_required(logout), name="signout"),
    url(r'^settings/account/', login_required(set_account), name="setting"),
    url(r'^home/', login_required(home), name="home"),
    url(r'^admin201501/', include(admin.site.urls)),
)
