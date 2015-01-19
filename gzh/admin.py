from django.contrib import admin

# Register your models here.

from .models import GongZhongHao, Post, Category

admin.site.register(GongZhongHao)
admin.site.register(Post)
admin.site.register(Category)
