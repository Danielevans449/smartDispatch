from django.contrib import admin
from .models import Verifikasi, Profile, Distribusi, AnggotaDistribusi, DeliveryOrder


class AnggotaInline(admin.TabularInline):
    model = AnggotaDistribusi
    extra = 0


@admin.register(Distribusi)
class DistribusiAdmin(admin.ModelAdmin):
    list_display = ("kapal", "tujuan", "shipper", "konsignee")
    inlines = [AnggotaInline]


@admin.register(DeliveryOrder)
class DOAdmin(admin.ModelAdmin):
    list_display = ("no_urut", "distribusi", "nomor_trip", "pengirim", "penerima", "status")


admin.site.register(Verifikasi)
admin.site.register(Profile)