#!/usr/bin/env python
# -*- coding: utf-8 -*-
TEMPLATES = {}
TEMPLATES['content.html'] = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>{{ user }}</title>
    <style type="text/css">
    body{
        font-size: 1.1em;
        margin:0 5px;
    }

    h1{
        font-size:4em;
        font-weight:bold;
    }

    h2 {
        font-size: 1.2em;
        font-weight: bold;
        margin:0;
    }
    a {
        color: inherit;
        text-decoration: inherit;
        cursor: default
    }
    a[href] {
        color: blue;
        text-decoration: underline;
        cursor: pointer
    }
    p{
        text-indent:1.5em;
        line-height:1.3em;
        margin-top:0;
        margin-bottom:0;
    }
    .italic {
        font-style: italic
    }
    .do_article_title{
        line-height:1.5em;
        page-break-before: always;
    }
    #cover{
        text-align:center;
    }
    #toc{
        page-break-before: always;
    }
    #content{
        margin-top:10px;
        page-break-after: always;
    }
    </style>
</head>
<body>
    <div id="cover">
        <h1 id="title">{{ user }}</h1>
        <a href="#content">Go straight to first item</a><br />
        {{ mobitime.strftime("%m/%d %H:%M") }}
    </div>
    <div id="toc">
        <h2>Feeds:</h2>
        <ol>
            {% set feed_count = 0 %}
            {% set feed_idx=0 %}
            {% for feed in feeds %}
            {% set feed_idx=feed_idx+1 %}
            {% if len(feed['entries']) > 0 %}
            {% set feed_count = feed_count + 1 %}
            <li>
              <a href="#sectionlist_{{ feed_idx }}">{{ feed['title'] }}</a>
              <br />
              {{ len(feed['entries']) }} items
            </li>
            {% end %}

            {% end %}
        </ol>

        {% set feed_idx=0 %}
        {% for feed in feeds %}
        {% set feed_idx=feed_idx+1 %}
        {% if len(feed['entries']) > 0 %}
        <mbp:pagebreak />
        <div id="sectionlist_{{ feed_idx }}" class="section">
            {% if feed_idx < feed_count %}
            <a href="#sectionlist_{{ feed_idx+1 }}">Next Feed</a> |
            {% end %}

            {% if feed_idx > 1 %}
            <a href="#sectionlist_{{ feed_idx-1 }}">Previous Feed</a> |
            {% end %}

            <a href="#toc">TOC</a> |
            {{ feed_idx }}/{{ feed_count }} |
            {{ len(feed['entries']) }} items
            <br />
            <h3>{{ feed['title'] }}</h3>
            <ol>
                {% for item in feed['entries'] %}
                <li>
                  <a href="#article_{{ feed_idx }}_{{ item['idx'] }}">{{ item['title'] }}</a><br/>
                  {% if item['published'] %}{{ item['published'] }}{% end %}
                </li>
                {% end %}
            </ol>
        </div>
        {% end %}
        {% end %}
    </div>
    <mbp:pagebreak />
    <div id="content">
        {% set feed_idx=0 %}
        {% for feed in feeds %}
        {% set feed_idx=feed_idx+1 %}
        {% if len(feed['entries']) > 0 %}
        <div id="section_{{ feed_idx }}" class="section">
        {% for item in feed['entries'] %}
        <div id="article_{{ feed_idx }}_{{ item['idx'] }}" class="article">
            <h2 class="do_article_title">
              {% if item['url'] %}
              <a href="{{ item['url'] }}">{{ item['title'] }}</a>
              {% else %}
              {{ item['title'] }}
              {% end %}
            </h2>
            {{ feed['title'] }}
            <br />
            {% if item['author'] %}{{ escape(item['author']) }}{% end %}   {% if item['published'] %}{{ item['published'] }}{% end %}

            <div>{{ item['content'] }}</div>
        </div>
        {% end %}
        </div>
        {% end %}
        {% end %}
    </div>
</body>
</html>
"""

TEMPLATES['toc.ncx'] = """<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="zh-CN">
<head>
<meta name="dtb:depth" content="4" />
<meta name="dtb:totalPageCount" content="0" />
<meta name="dtb:maxPageNumber" content="0" />
</head>
<docTitle><text>{{ user }}</text></docTitle>
<docAuthor><text>{{ user }}</text></docAuthor>
<navMap>
    {% if format == 'periodical' %}
    <navPoint class="periodical">
        <navLabel><text>{{ user }}</text></navLabel>
        <content src="content.html" />
        {% set feed_idx=0 %}
        {% for feed in feeds %}
        {% set feed_idx=feed_idx+1 %}
        {% if len(feed['entries']) > 0 %}
        <navPoint class="section" id="{{ feed_idx }}">
            <navLabel><text>{{ escape(feed['title']) }}</text></navLabel>
            <content src="content.html#section_{{ feed_idx }}" />
            {% for item in feed['entries'] %}
            <navPoint class="article" id="{{ feed_idx }}_{{ item['idx'] }}" playOrder="{{ item['idx'] }}">
              <navLabel><text>{{ escape(item['title']) }}</text></navLabel>
              <content src="content.html#article_{{ feed_idx }}_{{ item['idx'] }}" />
              <mbp:meta name="description">{{ escape(item['stripped']) }}</mbp:meta>
              <mbp:meta name="author">{{ escape(item['author']) }}</mbp:meta>
            </navPoint>
            {% end %}
        </navPoint>
        {% end %}
        {% end %}
    </navPoint>
    {% else %}
    <navPoint class="book">
        <navLabel><text>{{ user }}</text></navLabel>
        <content src="content.html" />
        {% set feed_idx=0 %}
        {% for feed in feeds %}
        {% set feed_idx=feed_idx+1 %}
        {% if len(feed['entries']) > 0 %}
            {% for item in feed['entries'] %}
            <navPoint class="chapter" id="{{ feed_idx }}_{{ item['idx'] }}" playOrder="{{ item['idx'] }}">
                <navLabel><text>{{ escape(item['title']) }}</text></navLabel>
                <content src="content.html#article_{{ feed_idx }}_{{ item['idx'] }}" />
            </navPoint>
            {% end %}
        {% end %}
        {% end %}
    </navPoint>
    {% end %}
</navMap>
</ncx>
"""

TEMPLATES['content.opf'] = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uid">
<metadata>
<dc-metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    {% if format == 'periodical' %}
    <dc:title>{{ user }}</dc:title>
    {% else %}
    <dc:title>{{ user }}({{ mobitime.strftime("%m/%d %H:%M") }})</dc:title>
    {% end %}
    <dc:language>zh-CN</dc:language>
    <dc:identifier id="uid">{{ user }}</dc:identifier>
    <dc:creator>kindlereader</dc:creator>
    <dc:publisher>kindlereader</dc:publisher>
    <dc:subject>{{ user }}</dc:subject>
    <dc:date>{{ datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") }}</dc:date>
    <dc:description></dc:description>
</dc-metadata>
{% if format == 'periodical' %}
<x-metadata>
    <output encoding="utf-8" content-type="application/x-mobipocket-subscription-magazine"></output>
    </output>
</x-metadata>
{% end %}
</metadata>
<manifest>
    <item id="content" media-type="application/xhtml+xml" href="content.html"></item>
    <item id="toc" media-type="application/x-dtbncx+xml" href="toc.ncx"></item>
</manifest>

<spine toc="toc">
    <itemref idref="content"/>
</spine>

<guide>
    <reference type="start" title="start" href="content.html#content"></reference>
    <reference type="toc" title="toc" href="content.html#toc"></reference>
    <reference type="text" title="cover" href="content.html#cover"></reference>
</guide>
</package>
"""

import os
from datetime import datetime
import template
from .kindlestrip import SectionStripper
import logging

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = "/tmp/data/"
FORMAT = "periodical"
USER = "WeiRead"
KINDLEGEN   = os.path.join(BASE_DIR, "kindlegen")
STRIPPED = True

def generate_mobi_file(feed_data):
    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)
    for tpl in TEMPLATES:
        if tpl is 'book.html':
            continue
        t = template.Template(TEMPLATES[tpl])
        content = t.generate(
            user = USER,
            feeds = feed_data,
            format = FORMAT,
            mobitime = datetime.now()
        )

        with open(os.path.join(DATA_DIR, tpl), 'wb') as fp:
            fp.write(content)

    mobi8_file = "KindleReader8-%s.mobi" % (datetime.now().strftime('%Y%m%d-%H%M%S'))
    mobi6_file = "KindleReader-%s.mobi" % (datetime.now().strftime('%Y%m%d-%H%M%S'))
    opf_file = os.path.join(DATA_DIR, "content.opf")
    os.system("%s %s -o %s > log.txt" %(KINDLEGEN, opf_file, mobi8_file) )

    # kindlegen生成的mobi，含有v6/v8两种格式
    mobi8_file = os.path.join(DATA_DIR, mobi8_file)
    # kindlestrip处理过的mobi，只含v6格式
    mobi6_file = os.path.join(DATA_DIR, mobi6_file)
    if STRIPPED:
        # 调用kindlestrip处理mobi
        try:
            data_file = file(mobi8_file, 'rb').read()
            strippedFile = SectionStripper(data_file)
            file(mobi6_file, 'wb').write(strippedFile.getResult())
            mobi_file = mobi6_file
        except Exception, e:
            mobi_file = mobi8_file
            logging.error("Error: %s" % e)
    else:
        mobi_file = mobi8_file

    if not os.path.isfile(mobi_file):
        logging.error("failed!")
        return None
    else:
        logging.info(".mobi save as: {}({}KB)".format(mobi_file, os.path.getsize(mobi_file) / 1024))
        return mobi_file
