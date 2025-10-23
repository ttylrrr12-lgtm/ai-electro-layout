# Обучение детектора символов (YOLOv8/YOLOv10)

## Шаги
1. Соберите датасет (Roboflow/Label Studio) с классами: `panel, socket, switch, light, junction` (расширяйте по нужде).
2. Экспортируйте в формát COCO или YOLO.
3. Заполните `dataset.yaml`.
4. Запустите:
```bash
python train.py --model yolo11n.pt --epochs 50 --img 1024
```
5. Экспортируйте ONNX и подключите к backend.

## Пример `dataset.yaml`
```yaml
path: ./data
train: images/train
val: images/val
names: [panel, socket, switch, light, junction]
```

## Инференс сервер
После обучения экспортируйте:
```bash
yolo export model=runs/detect/train/weights/best.pt format=onnx opset=12
```
И загрузите ONNX в backend (см. TODO в `backend/app.py`: эндпоинт `/detect`).
