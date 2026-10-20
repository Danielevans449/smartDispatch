import base64
import io
from pathlib import Path

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageDraw, ImageOps
from ultralytics import YOLO

ML_DIR = Path(__file__).resolve().parent / "ml"

# satu model, dua class (Hollow dan Pipe)
model = YOLO(str(ML_DIR / "pipe_hollow.pt"))
print("CLASS MODEL:", model.names)

CONF = 0.5
WARNA = {"pipe": (0, 200, 0), "hollow": (255, 140, 0)}


def index(request):
    return render(request, "detection/index.html")


def ambil_foto(request):
    return render(request, "detection/ambil_foto.html")


@csrf_exempt  # sementara buat testing
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