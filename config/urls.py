
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views

from detection.views import (
    detect,
    index,
    ambil_foto,
    simpan,
    distribusi_baru,
    buat_do,
    detail_do,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", index, name="beranda"),

    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="detection/login.html"
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    path(
        "distribusi-baru/",
        distribusi_baru,
        name="distribusi_baru",
    ),
    path(
        "buat-do/",
        buat_do,
        name="buat_do",
    ),
    path("detail-do/<int:id>/", detail_do, name="detail_do"),
    path("do/<int:id>/", detail_do, name="do_digital"),

    path("ambil-foto/", ambil_foto, name="ambil_foto"),
    path("api/detect/", detect, name="detect"),
    path("api/simpan/", simpan, name="simpan"),
] + static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT,
)
