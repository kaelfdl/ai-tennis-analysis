from ultralytics import YOLO

model = YOLO('yolov8x')

result = model.predict('tennis_sample.MOV', conf=0.2, save=True)
print(result)
print("boxes:")
for box in result[0].boxes:
    print(box)
