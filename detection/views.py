import base64
import io
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Max
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageDraw, ImageOps
from ultralytics import YOLO

from .models import (AnggotaDistribusi, DeliveryOrder, Distribusi,
                     NOMOR_DO_AWAL, Verifikasi)

ML_DIR = Path(__file__).resolve().parent / "ml"

# satu model, dua class (Hollow dan Pipe)
model = YOLO(str(ML_DIR / "pipe_hollow.pt"))
print("CLASS MODEL:", model.names)

CONF = 0.5
WARNA = {"pipe": (0, 200, 0), "hollow": (255, 140, 0)}


def role_user(user):
    try:
        return user.profile.role
    except Exception:
        return "admin" if user.is_superuser else "petugas"


def no_urut_berikut():
    m = DeliveryOrder.objects.aggregate(m=Max("no_urut"))["m"]
    return NOMOR_DO_AWAL if m is None else m + 1


@login_required
def index(request):
    role = role_user(request.user)
    if role == "petugas":
        return redirect("distribusi_baru")  # sementara, nanti Beranda Petugas
    return HttpResponse(f"Beranda {role} (belum dibuat)")


@login_required
def distribusi_baru(request):
    petugas = User.objects.filter(profile__role="petugas").exclude(id=request.user.id)
    if request.method == "POST":
        p = request.POST
        d = Distribusi.objects.create(
            kapal=p.get("kapal", "").strip(),
            shipper=p.get("shipper", "").strip(),
            konsignee=p.get("konsignee", "").strip(),
            tujuan=p.get("tujuan", "").strip(),
            dibuat_oleh=request.user,
        )
        AnggotaDistribusi.objects.create(distribusi=d, user=request.user, peran="pengirim")
        for peran in ("pengirim", "penerima"):
            for uid in p.getlist(peran):
                AnggotaDistribusi.objects.get_or_create(distribusi=d, user_id=uid, peran=peran)
        return redirect(f"/buat-do/?distribusi={d.id}")
    return render(request, "detection/distribusi_baru.html", {"petugas": petugas})


@login_required
def buat_do(request):
    if not (request.GET.get("distribusi") or "").isdigit():
        return redirect("distribusi_baru")
    d = get_object_or_404(Distribusi, id=request.GET["distribusi"],
                          anggota__user=request.user, anggota__peran="pengirim")
    if request.method == "POST":
        p = request.POST
        do = DeliveryOrder.objects.create(
            distribusi=d, pengirim=request.user,
            no_urut=no_urut_berikut(),
            nomor_trip=d.do_set.count() + 1,
            palka=p.get("palka", "").strip(),
            no_truk=p.get("no_truk", "").strip().upper(),
            driver_id=p.get("driver") or None,
        )
        return redirect(f"/ambil-foto/?do={do.id}")
    return render(request, "detection/buat_do.html", {
        "d": d, "trip": d.do_set.count() + 1,
        "no_do": f"{no_urut_berikut():04d}",
        "drivers": User.objects.filter(profile__role="driver"),
    })


@login_required
def ambil_foto(request):
    if not (request.GET.get("do") or "").isdigit():
        return redirect("beranda")
    do = get_object_or_404(DeliveryOrder, id=request.GET["do"], pengirim=request.user)
    return render(request, "detection/ambil_foto.html", {"do": do})


@csrf_exempt  # sementara buat testing
@login_required
def simpan(request):
    if request.method != "POST" or "foto" not in request.FILES:
        return JsonResponse({"error": "Kirim foto lewat key 'foto' via POST"}, status=400)
    do = get_object_or_404(DeliveryOrder, id=request.POST.get("batch"), pengirim=request.user)
    v = Verifikasi.objects.create(
        batch=do.no_do, do=do,
        pipe_ai=int(request.POST.get("pipe_ai", 0)),
        hollow_ai=int(request.POST.get("hollow_ai", 0)),
        pipe_final=int(request.POST.get("pipe_final", 0)),
        hollow_final=int(request.POST.get("hollow_final", 0)),
        foto=request.FILES["foto"],
        foto_hasil=request.FILES.get("foto_hasil"),
    )
    return JsonResponse({"id": v.id, "total": v.total_final})


@login_required
def detail_do(request, id):
    do = get_object_or_404(DeliveryOrder, id=id)
    boleh = (role_user(request.user) == "admin"
             or do.distribusi.anggota.filter(user=request.user).exists())
    if not boleh:
        return HttpResponse("Tidak punya akses", status=403)
    return render(request, "detection/do_digital.html", {"do": do})


@csrf_exempt  # sementara buat testing
@login_required
def detect(request):
    if request.method != "POST" or "image" not in request.FILES:
        return JsonResponse({"error": "Kirim file dengan key 'image' via POST"}, status=400)

    # exif_transpose biar foto dari HP nggak miring/kebalik
    img = ImageOps.exif_transpose(Image.open(request.FILES["image"])).convert("RGB")

    r = model.predict(img, conf=CONF, verbose=False)[0]

    draw = ImageDraw.Draw(img)
    tebal = max(3, img.width // 250)
    jumlah = {"pipe": 0, "hollow": 0}

    for box, cls in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist()):
        nama = r.names[int(cls)].lower()  # "Hollow" -> "hollow"
        if nama not in jumlah:
            continue
        jumlah[nama] += 1
        draw.rectangle(box, outline=WARNA[nama], width=tebal)

    # kecilkan biar ringan dikirim balik
    img.thumbnail((1280, 1280))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    data_url = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

    return JsonResponse({
        "total": jumlah["pipe"] + jumlah["hollow"],
        "per_jenis": {"steel_pipe": jumlah["pipe"], "steel_hollow": jumlah["hollow"]},
        "image": data_url,
    })