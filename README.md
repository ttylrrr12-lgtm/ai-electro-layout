# AI Electro Layout — Starter Repo

Полноценный старт для веб‑сервиса: загрузка плана → распознавание символов (заглушка) → AI‑разводка по стенам → смета → экспорт SVG/PDF.

## Состав
- **frontend/** — React + Vite. Холст, загрузка плана (PNG/PDF/SVG), визуализация трасс, смета.
- **backend/** — FastAPI. Эндпоинты: `/parse`, `/detect`, `/route`, `/estimate` (пока с упрощённой логикой). CORS включён.
- **ml/** — каркас для обучения детектора символов (YOLO). Конфиги и скрипт запуска.

> MVP без настоящих моделей — заглушки и простой роутинг по сегментам стен. Подмените моки на реальные чекпоинты и правила.

## Быстрый запуск (Dev)

### 1) Backend
```bash
cd backend
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

### 2) Frontend
```bash
cd frontend
npm i
npm run dev
# открывайте http://localhost:5173
```

## Формат данных (сжатая схема)
- **План** нормализуется в координаты миллиметров и стены — это массив сегментов:
```json
{
  "walls": [ {"x1":0,"y1":0,"x2":4000,"y2":0}, ... ],
  "doors": [ {"x":1000,"y":0,"w":900} ],
  "scale_mm_per_px": 5.0
}
```
- **Символы** (розетки/выключатели/свет/щит):
```json
{ "symbols":[ {"type":"socket","x":1200,"y":300,"rotation":0}, ... ] }
```
- **Роутинг** — массив полилиний (SVG‑path или список точек).
- **Смета** — JSON позиций и итогов.

## Обучение детектора символов (YOLO)
Смотрите `ml/yolo/README.md`. Нужны свои разметки (Roboflow/Label Studio). После обучения — экспорт в ONNX и использование в backend.

## Экспорт
- SVG в `frontend/src/lib/export.ts`.
- PDF (временно) собирается на фронтенде из SVG (через `window.print`); прод: вынесите в backend (WeasyPrint/ReportLab).

## Лицензия
MIT
