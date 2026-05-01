"""
URL configuration for chaineHistoire project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import path

from backend import views


def home(request):
    return render(request, "library.html")

def about(request):
    return render(request, "about.html")


urlpatterns = [
    path("", views.get_story_library, name="home"),
    path("admin/", admin.site.urls),
    path("create/", views.create_story, name="create"),
    path("library/", views.get_story_library, name="library"),
    path("add/<int:pk>/", views.add_to_story, name="add"),
    path("read/<int:pk>/", views.read_story, name="read"),
    path("about/", about, name="about"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
