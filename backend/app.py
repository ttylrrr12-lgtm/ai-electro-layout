# ---------- импорты ----------
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import time
from PIL import Image
import io

from database import SessionLocal, engine, Base
from models import Project, Plan


# ---------- создаём FastAPI ----------
app = FastAPI(title="AI Electro Backend", version="0.1.0")

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- функции ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- стартовое событие ----------
@app.on_event("startup")
def startup_event():
    attempts, delay = 10, 3
    for i in range(attempts):
        try:
            Base.metadata.create_all(bind=engine)
            print("[startup] DB ready")
            break
        except Exception as e:
            print(f"[startup] DB init failed: {e}. Retry {i+1}/{attempts} in {delay}s")
            time.sleep(delay)


# ---------- эндпоинты ----------
@app.post("/upload_plan")
async def upload_plan(file: UploadFile = File(...), db: Session = Depends(get_db)):
    allowed = {"image/png", "image/jpeg", "image/svg+xml"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=415, detail="Поддерживаются PNG/JPG/SVG")

    content = await file.read()
    width = height = None
    if file.content_type in {"image/png", "image/jpeg"}:
        try:
            im = Image.open(io.BytesIO(content))
            width, height = im.size
        except Exception:
            pass

    plan = Plan(
        filename=file.filename or "plan",
        mimetype=file.content_type,
        width=width,
        height=height,
        data=content,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return {"plan_id": plan.id, "width": width, "height": height, "mimetype": plan.mimetype}


@app.get("/plan/{plan_id}/image")
def get_plan_image(plan_id: int, db: Session = Depends(get_db)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="План не найден")
    return Response(content=plan.data, media_type=plan.mimetype)
