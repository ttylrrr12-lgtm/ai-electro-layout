# backend/app.py
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import time
from PIL import Image
import io

# ВАЖНО: используем существующие объекты из database.py
from database import SessionLocal, engine, Base
from models import Project, Plan

# ----------------- СОЗДАЁМ ПРИЛОЖЕНИЕ РАНЬШЕ ВСЕГО -----------------
app = FastAPI(title="AI Electro Backend", version="0.1.0")

# CORS (позже можно сузить на домен Beget)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- DEPENDENCY -----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------- STARTUP: создаём таблицы с ретраями -----------------
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

# ----------------- HEALTH -----------------
@app.get("/health")
def health():
    return {"ok": True}

# ----------------- UPLOAD PLAN -----------------
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

# ----------------- PROJECTS SCHEMAS -----------------
class ProjectIn(BaseModel):
    title: str
    plan: Dict[str, Any] = Field(default_factory=dict)
    detection: Dict[str, Any] = Field(default_factory=dict)
    routes: Dict[str, Any] = Field(default_factory=dict)
    estimate: Dict[str, Any] = Field(default_factory=dict)
    plan_id: Optional[int] = None

class ProjectOut(ProjectIn):
    id: int
    class Config:
        from_attributes = True  # pydantic v2

def project_to_dict(p: Project) -> Dict[str, Any]:
    return {
        "id": p.id,
        "title": p.title,
        "plan": p.plan or {},
        "detection": p.detection or {},
        "routes": p.routes or {},
        "estimate": p.estimate or {},
        "plan_id": p.plan_id,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }

# ----------------- PROJECTS CRUD -----------------
@app.post("/projects", response_model=ProjectOut)
def create_project(payload: ProjectIn, db: Session = Depends(get_db)):
    obj = Project(
        title=payload.title,
        plan=payload.plan,
        detection=payload.detection,
        routes=payload.routes,
        estimate=payload.estimate,
        plan_id=payload.plan_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return project_to_dict(obj)

@app.get("/projects", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    rows = db.query(Project).order_by(Project.id.asc()).all()
    return [project_to_dict(r) for r in rows]

@app.get("/projects/{pid}", response_model=ProjectOut)
def get_project(pid: int, db: Session = Depends(get_db)):
    p = db.get(Project, pid)
    if not p:
        raise HTTPException(404, "Проект не найден")
    return project_to_dict(p)

@app.put("/projects/{pid}", response_model=ProjectOut)
def update_project(pid: int, payload: ProjectIn, db: Session = Depends(get_db)):
    p = db.get(Project, pid)
    if not p:
        raise HTTPException(404, "Проект не найден")
    p.title = payload.title
    p.plan = payload.plan
    p.detection = payload.detection
    p.routes = payload.routes
    p.estimate = payload.estimate
    p.plan_id = payload.plan_id
    db.commit()
    db.refresh(p)
    return project_to_dict(p)

# ----------------- AI ROUTE (заглушка) -----------------
class RouteIn(BaseModel):
    plan: Dict[str, Any] = Field(default_factory=dict)
    detection: Dict[str, Any] = Field(default_factory=dict)

@app.post("/route")
def make_route(body: RouteIn):
    # позже подставим реальную логику прокладки по правилам
    return {"ok": True, "routes": body.plan.get("routes", {}), "detection": body.detection}
