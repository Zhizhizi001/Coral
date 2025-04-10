"""
URL configuration for CDVS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin #管理后台模块
from django.urls import path, include #定义 URL 路径和包含其他 URL 配置的函数


urlpatterns = [
    path('admin/', admin.site.urls),
    # 将 /admin/ 的请求路由到 Django 的管理后台。
    path('', include(('user.urls', 'user'), namespace='user')),
    #将根 URL (/) 路由到 user 应用的 URL 配置。include 函数会加载 user.urls 模块中的所有 URL 路由，并为它们定义命名空间 user。

   # path('system/', include(('system.urls', 'system'), namespace='system')),
    # path('system/', include(('system.urls', 'system'), namespace='system')),
    path('coral_app/', include('coral_app.urls', namespace='coral_app')),
]
