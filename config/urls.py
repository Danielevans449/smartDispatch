from django.contrib import admin
from django.urls import path
from detection.views import detect, index

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index),
    path("api/detect/", detect),
]