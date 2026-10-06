from ultralytics import YOLO

for nama in ["pipe", "hollow"]:
    m = YOLO(f"detection/ml/{nama}.pt")
    r = m.predict("tes.jpeg", conf=0.25, verbose=False)[0]
    print(nama, [round(float(c), 2) for c in r.boxes.conf])
    r.save(f"hasil_{nama}.jpg")