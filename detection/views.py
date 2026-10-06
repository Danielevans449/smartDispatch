import base64
import io
from pathlib import Path

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageDraw
from torchvision.ops import box_iou
from ultralytics import YOLO

ML_DIR = Path(__file__).resolve().parent / "ml"

models = {
    "pipe": YOLO(str(ML_DIR / "pipe.pt")),
    "hollow": YOLO(str(ML_DIR / "hollow.pt")),
}

CONF = 0.7


def index(request):
    return render(request, "detection/index.html")


@csrf_exempt  # sementara buat testing
def detect(request):
    if request.method != "POST" or "image" not in request.FILES:
        return JsonResponse({"error": "Kirim file dengan key 'image' via POST"}, status=400)

    img = Image.open(request.FILES["image"]).convert("RGB")

    r_pipe = models["pipe"].predict(img, conf=CONF, verbose=False)[0]
    r_hollow = models["hollow"].predict(img, conf=CONF, verbose=False)[0]

    pipe_boxes = r_pipe.boxes.xyxy
    hollow_boxes = r_hollow.boxes.xyxy

    # buang kotak hollow yang numpuk dengan kotak pipe
    if len(pipe_boxes) and len(hollow_boxes):
        iou = box_iou(hollow_boxes, pipe_boxes)
        hollow_boxes = hollow_boxes[iou.max(dim=1).values < 0.5]

    # gambar kotak di foto
    draw = ImageDraw.Draw(img)
    tebal = max(3, img.width // 250)
    for b in pipe_boxes.tolist():
        draw.rectangle(b, outline=(0, 200, 0), width=tebal)
    for b in hollow_boxes.tolist():
        draw.rectangle(b, outline=(255, 140, 0), width=tebal)

    # kecilkan biar ringan dikirim balik
    img.thumbnail((1280, 1280))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    data_url = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

    jml_pipe = len(pipe_boxes)
    jml_hollow = len(hollow_boxes)
    return JsonResponse({
        "total": jml_pipe + jml_hollow,
        "per_jenis": {"steel_pipe": jml_pipe, "steel_hollow": jml_hollow},
        "image": data_url,
    })