from django.contrib import admin
from django.views.static import serve
from django.urls import path, include
from django.urls.conf import re_path
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
    re_path(r'^static/(?P<path>.*)$', serve,
            {'document_root': settings.STATIC_ROOT}),
]
