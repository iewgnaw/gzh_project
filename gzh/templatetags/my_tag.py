# -*- coding: utf-8 -*-
from django import template

register = template.Library()


import time

@register.filter
def time_format(timestamp):
	return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


@register.filter
def relative_time(timestamp):
	post_time = time.localtime(timestamp)
	now = time.localtime()

	'''北京时间timestamp比UTC timestamp少28800=8*60*60'''
	relative_days = int((time.time()) + 28800)/(60*60*24) - (timestamp + 28800)/(60*60*24)
	if relative_days == 0:
		return "今天%s" %time.strftime("%H:%M", time.localtime(timestamp))
	elif relative_days == 1:
		return "昨天"
	elif now.tm_year == post_time.tm_year:
		return time.strftime("%m月%d日", time.localtime(timestamp))
	else:
		return time.strftime("%y年%m月%d日", time.localtime(timestamp))

@register.filter
def desc(text):
	return text[:30]

@register.filter
def has_subscribe(user, id):
	if not user.is_authenticated():
		return False
	if user.userprofile.subscribes.filter(pk=id).count() > 0:
		return True
	else:
		return False
