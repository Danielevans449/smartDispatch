from django.contrib import admin
from django.urls import path
from detection.views import detect, index, ambil_foto

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index),
    path("ambil-foto/", ambil_foto),
    path("api/detect/", detect),
]