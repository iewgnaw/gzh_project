# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re

from django import forms
from django.contrib.auth.models import User
from gzh.models import UserProfile, Category

class AddGzhForm(forms.Form):
	def __init__(self, *args, **kwargs):
		super(AddGzhForm, self).__init__(*args, **kwargs)
		self.fields['category'].choices = \
			[(category.id, category.value) for category in Category.objects.all()]

	wx_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',
		                                                    'placeholder': u'公众号名称'}),
							  required=True,
							  label=u'',
							  error_messages={'required': u'请输入公众号名称'})
	wx_id	= forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',
							  								'placeholder': u'公众号ID'}),
	 						  required=True,
	 						  label=u'',
	 						  error_messages={'required': u'请输入公众号ID'})
	category = forms.ChoiceField(label=u'分类',
                                widget=forms.Select(attrs={'class': 'form-control'}),
								required=True,
								choices=())

	def clean_wx_name(self):
		return self.cleaned_data['wx_name'].strip()

	def clean_wx_id(self):
		return self.cleaned_data['wx_id'].strip()

	def clean_category(self):
		category_id = int(self.cleaned_data.get('category'))
		if Category.objects.filter(pk=category_id).count() == 0:
			forms.ValidationError(u'未选择分类')
		return Category.objects.get(pk=category_id)

class UserForm(forms.Form):
	username = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}),
							   max_length=30,
							   label=u'用户名',
							   required=True,
							   error_messages={'required': u'请输入有效的用户名'})
	email	 = forms.EmailField(widget=forms.TextInput(attrs={'class':'form-control'}),
								label=u'邮件地址',
								required=True,
								error_messages={'required': u'必须输入邮件地址',
										        'invalid': u'请输入有效的邮件地址'})
	password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}),
								label=u'密码',
								required=False,
								error_messages={'required': u'请输入密码'})

	password_c = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}),
								label=u'确认密码',
								required=False)

	def clean_username(self):
		username = self.cleaned_data['username'].strip()
		if User.objects.filter(username=username).count():
			raise forms.ValidationError(u'用户名已经已经被占用')
		patterns = re.compile(r'^[\w\_\-]+$')
		if not patterns.match(username):
			raise forms.ValidationError(u'用户名只能包含字母 数字 - _')
		return username

	def clean_email(self):
		email = self.cleaned_data['email'].strip()
		if User.objects.filter(email=email).count():
				raise forms.ValidationError(u'邮箱已经被注册')
		return email

	def clean(self):
		password 	= self.cleaned_data.get('password')
		password_c 	= self.cleaned_data.get('password_c')
		if password == password_c:
			return self.cleaned_data
		else:
			raise forms.ValidationError(u'两次密码不相同')


	def save(self):
		username = self.cleaned_data['username']
		email = self.cleaned_data['email']
		password = self.cleaned_data['password']

		new_user = User(username=username)
		new_user.set_password(password)
		new_user.email =  email
		new_user.save()

		return new_user

class UserProfileForm(forms.ModelForm):
	class Meta:
		model = UserProfile
		fields = []


class LoginForm(forms.Form):
	name_or_email = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}),
									label=u'用户名或邮件地址',
									required=True,
									error_messages={'required': u'请输入用户名！'})
	password 	  = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}),
									label=u'密码',
									required=True,
									error_messages={'required': u'请输入密码！'})

class AccountForm(forms.Form):
    kindle_email = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control', 'id': 'kindle-email'}),
									label=u'kindle邮箱',
									required=False,
							 		error_messages={'required': u'邮箱不能为空',
								             	    'invalid': u'邮箱格式错误'},
									help_text=u'kindle@weiread.pw必须在您的已认可发件人电子邮箱列表内')
    delivery_switch = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'form-control delivery'}),
                                  label=u'开启投递',
                                  required=False)

    def clean_kindle_email(self):
		kindle_email = self.cleaned_data.get('kindle_email')
		if kindle_email and not re.search(r"\w+@kindle\.c", kindle_email):
			raise forms.ValidationError(u'kindle邮箱格式不对')
		return kindle_email

    def clean_delivery_switch(self):
        if (not self.clean_kindle_email()) and self.cleaned_data.get('delivery_switch'):
            raise forms.ValidationError(u'必须设置正确的kindle邮箱才能开启投递')
        return self.cleaned_data.get('delivery_switch')

    def clean(self):
        return self.cleaned_data

    def save(self,user):
        userprofile = user.userprofile
        userprofile.kindle_email = self.cleaned_data['kindle_email']
        userprofile.delivery = self.cleaned_data['delivery_switch']
        userprofile.save(update_fields=['kindle_email', 'delivery'])
