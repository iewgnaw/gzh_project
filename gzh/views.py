# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import logging

from django.shortcuts import (render, HttpResponse, HttpResponseRedirect,
                              get_object_or_404)
from django.views.generic import View
#from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.conf import settings

import requests
from bs4 import BeautifulSoup

from .models import GongZhongHao, Post, Category, UserProfile, WeiBoProfile
from .form import AddGzhForm, AccountForm
from gzh import tasks
from utils import format_date

logger = logging.getLogger('gzh')


def _is_ajax_request(handler):
    def wraper(*args, **kwargs):
        if not args[0].is_ajax():
            return HttpResponse(
                json.dumps({"status": 403, "msg": "ajax required"}))
        else:
            return handler(*args, **kwargs)
    return wraper


def _ajax_login_required(handler):
    def wraper(*args, **kwargs):
        if args[0] and args[0].user.is_authenticated():
            return handler(*args, **kwargs)
        else:
            return HttpResponse(
                json.dumps({"status": 401, "msg": "login required"})
            )
    return wraper


def weibo_login(request):
    url = ('https://api.weibo.com/oauth2/authorize?client_id=%s'
           '&redirect_uri=%s') % (settings.CLIENT_ID, settings.REDIRECT_URI)
    return HttpResponseRedirect(url)


def weibo_auth(request):
    code = request.GET.get('code')
    token_url = 'https://api.weibo.com/oauth2/access_token'
    post_data = {
        'client_id': settings.CLIENT_ID,
        'client_secret': settings.CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.REDIRECT_URI
    }
    try:
        r_data = requests.post(token_url, data=post_data).json()
        access_token = r_data['access_token']
        uid = r_data['uid']
        weibo_info_url = ('https://api.weibo.com/2/users/show.json?'
                          'access_token=%s&uid=%s') % (access_token, uid)
        weibo_info = requests.get(weibo_info_url).json()
        if weibo_info.get('error_code') is not None:
            raise Exception(weibo_info)
    except Exception as ex:
        logger.warning(ex)
        return HttpResponse('weibo login failed')

    if WeiBoProfile.objects.filter(uid=uid).count() > 0:
        userprofile = UserProfile.objects.select_related('weiboprofile', 'user')\
            .get(weiboprofile=WeiBoProfile.objects.filter(uid=uid))
        weiboprofile = userprofile.weiboprofile
        weiboprofile.access_token = access_token
        weiboprofile.screen_name = weibo_info['screen_name']
        weiboprofile.avatar = weibo_info['profile_image_url']
        weiboprofile.save()

        #
        user = userprofile.user
        user.username = weibo_info['screen_name']
        user.save(update_fields=['username'])
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        auth.login(request, user)
        return HttpResponseRedirect(reverse('welcome'))
    else:
        new_weibo_user = WeiBoProfile.objects.create(
            uid=uid,
            access_token=access_token,
            screen_name=weibo_info['screen_name'],
            avatar=weibo_info['profile_image_url']
        )
        if request.user.is_authenticated():
            user = request.user
            userprofile = user.userprofile
        else:
            new_user = User.objects.create(username=weibo_info['screen_name'])
            userprofile = UserProfile()
            userprofile.user = new_user
            new_user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth.login(request, new_user)
        userprofile.weiboprofile = new_weibo_user
        userprofile.save()
        return HttpResponseRedirect(reverse('welcome'))
    return HttpResponseRedirect('/')


def welcome(request):
    return render(request, 'welcome.html')


class AddGzhView(View):

    def post(self, request, *args, **kwargs):
        form = AddGzhForm(request.POST)
        if form.is_valid():
            wx_id = form.cleaned_data['wx_id']
            wx_name = form.cleaned_data['wx_name']
            category = form.cleaned_data['category']
            tasks.add_gzh.delay(wx_id, wx_name, category)
            return HttpResponse(json.dumps({"status": 0, "msg": "SUCCESS"}))
        else:
            return HttpResponse(json.dumps({"status": 1, "msg": u"提交错误"}))


def index(request, category_id=1):
    if not cache.get('categories'):
        categories = Category.objects.all()
        cache.set('categories', categories, 24 * 60 * 60)
    else:
        categories = cache.get('categories')

    gzhs = GongZhongHao.objects.filter(
        category=Category.objects. filter(
            pk=int(category_id))).order_by('-last_updated')
    paginator = Paginator(gzhs, 10)
    page = request.GET.get("page", 1)
    try:
        gzh_list = paginator.page(page)
    except PageNotAnInteger:
        gzh_list = paginator.page(1)
    except EmptyPage:
        gzh_list = paginator.page(paginator.num_pages)
    return render(request, "gzh/index.html",
                  {"categories": categories,
                   "gzhs": gzh_list,
                   "add_gzh_form": AddGzhForm(),
                   "current_id": int(category_id)})


def gzh_info(request, wx_id):
    gzh = GongZhongHao.objects.get(wx_id=wx_id)
    if gzh:
        post_list = gzh.post_set.all()
        paginator = Paginator(post_list, 12)

        page = request.GET.get("page")
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)
        return render(request, "post/list_post.html",
                      {"posts": posts, "gzh": gzh})


def show_post(request, id):
    post = get_object_or_404(Post, id=int(id))
    soup = BeautifulSoup(post.content)
    # for img in soup.find_all('img'):
    ##img['src'] = settings.STATIC_URL + 'images/loader.gif'
    # img['src'] = '#'
    post.content = unicode(soup)
    return render(request, "post/show.html", {"post": post})

# class Signup(View):
    # def post(self, request, *args, **kwargs):
    #user_form = UserForm(request.POST)
    #user_profile_form = UserProfileForm(request.POST)

    # if user_form.is_valid() and user_profile_form.is_valid():
    #user = user_form.save()
    # user.save()

    #profile = user_profile_form.save(commit=False)
    #profile.user = user

    # profile.save()
    # user = auth.authenticate(username=user_form.cleaned_data['username'],
    # password=user_form.cleaned_data['password'])
    # if user is not None:
    #auth.login(request, user)
    # return HttpResponseRedirect("/gzh/")
    # else:
    #error_message = user_form.errors.get('__all__')
    ## user_profile_form = UserProfileForm()
    # return render(request, "regiseter.html",
    #{"user_form": user_form, "user_profile_form": user_profile_form,
    #"error_message": error_message })

    # def get(self, request, *args, **kwargs):
    #user_form = UserForm()
    #user_profile_form = UserProfileForm()
    # return render(request, "regiseter.html",
    #{"user_form": user_form, "user_profile_form": user_profile_form})


def signin(request):
    return render(request, 'signin.html')


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/")


@_ajax_login_required
@_is_ajax_request
def subscribe(request):
    '''
    '''
    result = {"status": 200, "msg": "SUCCESS"}
    if request.GET.get("id") and request.user.is_authenticated():
        id = int(request.GET.get("id"))
        user_profile = request.user.userprofile
        if user_profile.subscribes.filter(pk=id).count() > 0:
            gzh = GongZhongHao.objects.get(pk=id)
            user_profile.subscribes.remove(gzh)
            gzh.hot_plus(-1)
            result["data"] = '0'
            return HttpResponse(json.dumps(result))
        else:
            try:
                gzh = GongZhongHao.objects.get(pk=id)
            except:
                return HttpResponse(status=400)
            user_profile.subscribes.add(gzh)
            gzh.hot_plus(1)
            result["data"] = '1'
            return HttpResponse(json.dumps(result))


def update_post(request):
    # tasks.MakeMobiTask.delay()
    tasks.UpdatePost.delay()
    # tasks.MakeLocalImage.delay()
    return HttpResponse('ok')


def set_account(request):
    if request.method == "GET":
        kindle_email = request.user.userprofile.kindle_email
        delivery_switch = request.user.userprofile.delivery
        initial_form = AccountForm({"kindle_email": kindle_email,
                                    "delivery_switch": delivery_switch})
        return render(request, "setting_account.html",
                      {"account_form": initial_form})

    elif request.method == "POST":
        success_message = ''
        error_message = ''
        account_form = AccountForm(request.POST)
        if account_form.is_valid():
            account_form.save(request.user)
            success_message = u'保存成功'
        else:
            error_message = u'更新失败'

        return render(request,
                      "setting_account.html",
                      {"account_form": account_form,
                       "error_message": error_message,
                       "success_message": success_message})


class SetPassword(View):
    pass


@login_required
def home(request):
    subscribes = request.user.userprofile.subscribes.\
        order_by('-last_updated').all()
    # if subscribes.count() > 0:
    # entries = _entries(subscribes[0].id)
    # if len(entries) > 0:
    # entry = _entry(entries[0]['id'])
    return render(request, "home.html", {"feeds": subscribes})


@_is_ajax_request
@login_required
def entries_api(request, id):
    userprofile = request.user.userprofile
    result = {"entries": []}
    gzh = GongZhongHao.objects.filter(pk=int(id))
    posts_qs = Post.objects.values("title", "id", "last_modified", "cover").\
        filter(gongzhonghao=gzh).all()
    paginator = Paginator(posts_qs, 10)
    page = request.GET.get('page', 1)
    try:
        entries = paginator.page(page).object_list
        result['next_page'] = int(page) + 1
    except:
        entries = []
        result['next_page'] = 0
    for entry in entries:
        entry['last_modified'] = format_date(entry['last_modified'])
        if userprofile.readed_posts.filter(pk=entry['id']).count() > 0:
            entry['readed'] = 0
        else:
            entry['readed'] = 1
        result['entries'].append(entry)
    return HttpResponse(json.dumps(result), content_type="application/json")


@_ajax_login_required
@_is_ajax_request
def entry_api(request, id):
    post = get_object_or_404(Post, pk=int(id))
    soup = BeautifulSoup(post.content)
    remove_attributes = ['class', 'id', 'title', 'style', 'width', 'height',
                         'onclick']
    for attr in remove_attributes:
        for x in soup.find_all(attrs={attr: True}):
            del x[attr]
    for img in soup.find_all('img'):
        if not img.has_attr('data-src'):
            img.extract()
        # else:
            ##img['src'] = settings.STATIC_URL + 'images/loader.gif'
            # img['src'] = '#'
    return HttpResponse(unicode(soup))

# //entry_up?id=1


@_ajax_login_required
@_is_ajax_request
def entry_up(request):
    userprofile = request.user.userprofile
    try:
        id = int(request.GET['id'])
        if userprofile.liked_posts.filter(post_id=id).count() == 0:
            post = Post.objects.get(pk=id)
            post.up_plus()
            userprofile.liked_posts.add(post)
        return HttpResponse(0)
    except:
        return HttpResponse(1)

# mark_as_readed?id=1


@_ajax_login_required
@_is_ajax_request
def mark_as_readed(request):
    userprofile = request.user.userprofile
    try:
        id = int(request.GET['id'])
        post = Post.objects.get(pk=id)
        userprofile.readed_posts.add(post)
        return HttpResponse(0)
    except:
        return HttpResponse(1)


def show(request, id):
    gzh = get_object_or_404(GongZhongHao, id=int(id))
    posts_qs = Post.objects.values(
        'id', 'title', 'summary', 'cover', 'last_modified').\
        filter(gongzhonghao=GongZhongHao.objects.filter(pk=int(id)))
    posts_paginator = Paginator(posts_qs, 15)
    page = request.GET.get("page", 1)
    try:
        post_list = posts_paginator.page(page)
        for p in post_list.object_list:
            p['last_modified'] = format_date(p['last_modified'])
    except PageNotAnInteger:
        post_list = posts_paginator.page(1)
    except EmptyPage:
        post_list = posts_paginator.page(posts_paginator.num_pages)
    return render(request, 'gzh/show.html',
                  {"posts": post_list, "gzh": gzh})


@_is_ajax_request
def search_gzh(request):
    query = request.GET.get('query', None)
    if query is None:
        gzh = []
    else:
        gzh = GongZhongHao.objects.values('wx_name', 'logo', 'id').\
            filter(wx_name__icontains=query)[:10]
    for g in gzh:
        g['logo'] = settings.STATIC_URL + g['logo']
    return HttpResponse(json.dumps(list(gzh)), content_type="application/json")
