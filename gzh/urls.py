# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import cache_page

from django.contrib import admin
admin.autodiscover()

from .views import (AddGzhView, index, update_post, subscribe, show, show_post,
                    entries_api, entry_api, search_gzh)

urlpatterns = patterns('',
    url(r'^$', index, name='index'),
    #url(r'^update', update_post),
    url(r'cat/(?P<category_id>\d+)$', index),
    url(r'^subscribe', subscribe),
    url(r'^(?P<id>\d+)/entries/$', entries_api),
    url(r'^entry/(?P<id>\d+)', cache_page(60 * 60)(entry_api)),

    url(r'^add/$',  AddGzhView.as_view()),
    url(r'^(?P<id>\d+)', cache_page(60 * 10)(show), name="show_gzh"),
    url(r'^post/(?P<id>\d+)', cache_page(60 * 60)(show_post), name="show_post"),
    url(r'^search', search_gzh, name="search_gzh"),
    url(r'^update', update_post, name="update_post"),
)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

