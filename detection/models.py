from django.db import models
from django.contrib.auth.models import User

class Verifikasi(models.Model):
    batch = models.CharField(max_length=100, default="Batch 1")
    pipe_ai = models.PositiveIntegerField(default=0)
    hollow_ai = models.PositiveIntegerField(default=0)
    pipe_final = models.PositiveIntegerField(default=0)
    hollow_final = models.PositiveIntegerField(default=0)
    foto = models.ImageField(upload_to="verifikasi/")
    foto_hasil = models.ImageField(
        upload_to="verifikasi/hasil/",
        null=True,
        blank=True,
    )
    dibuat = models.DateTimeField(auto_now_add=True)
    do = models.ForeignKey("DeliveryOrder", null=True, blank=True,
                       on_delete=models.SET_NULL, related_name="verifikasi")

    @property
    def total_final(self):
        return self.pipe_final + self.hollow_final

    def __str__(self):
        return f"{self.batch} - {self.total_final} barang"
    
class Profile(models.Model):
    ROLE = [("admin", "Admin"), ("petugas", "Petugas"), ("driver", "Driver")]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE, default="petugas")
    no_hp = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

NOMOR_DO_AWAL = 1  # ganti 4805 kalau mau nyambung ke DO fisik


class Distribusi(models.Model):
    kapal = models.CharField(max_length=100)
    shipper = models.CharField(max_length=150)
    konsignee = models.CharField(max_length=150)
    tujuan = models.CharField(max_length=150)
    dibuat_oleh = models.ForeignKey(User, on_delete=models.PROTECT, related_name="distribusi_dibuat")
    dibuat = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.kapal} → {self.tujuan}"


class AnggotaDistribusi(models.Model):  # association class
    PERAN = [("pengirim", "Pengirim"), ("penerima", "Penerima")]
    distribusi = models.ForeignKey(Distribusi, on_delete=models.CASCADE, related_name="anggota")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    peran = models.CharField(max_length=10, choices=PERAN)

    class Meta:
        unique_together = ("distribusi", "user", "peran")


class DeliveryOrder(models.Model):
    STATUS = [("menunggu", "Menunggu"), ("dikirim", "Dikirim"), ("selesai", "Selesai")]
    distribusi = models.ForeignKey(
    Distribusi,
    null=True,
    blank=True,
    on_delete=models.CASCADE,
        related_name="do_set",
    )

    no_urut = models.PositiveIntegerField(
        unique=True,
        null=True,
        blank=True,
    )

    nomor_trip = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    pengirim = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="do_pengirim",
    )
    palka = models.CharField(max_length=20, blank=True)
    no_truk = models.CharField(max_length=20, blank=True)
    driver = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="do_driver")
    penerima = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="do_penerima")
    status = models.CharField(max_length=10, choices=STATUS, default="menunggu")
    dibuat = models.DateTimeField(auto_now_add=True)
    

    @property
    def no_do(self):
        return f"{self.no_urut:04d}"

    @property
    def jumlah_pipe(self):
        return self.verifikasi.aggregate(t=models.Sum("pipe_final"))["t"] or 0

    @property
    def jumlah_hollow(self):
        return self.verifikasi.aggregate(t=models.Sum("hollow_final"))["t"] or 0