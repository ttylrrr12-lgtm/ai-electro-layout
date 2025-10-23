from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
import io, json
from routing.graph import build_graph_from_walls, route_wires_a_star, unify_bundles
from routing.rules import estimate_bill, validate_routes

from fastapi import Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Project

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# создать таблицы, если их нет
Base.metadata.create_all(bind=engine)

class ProjectIn(BaseModel):
    title: str
    plan: Plan
    detection: DetectionResult
    routes: Dict[str, list] = Field(default_factory=dict)
    estimate: Dict[str, Any] = Field(default_factory=dict)

class ProjectOut(BaseModel):
    id: int
    title: str

app = FastAPI(default_response_class=ORJSONResponse, title="AI Electro Layout API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Schemas ----
class Wall(BaseModel):
    x1: float; y1: float; x2: float; y2: float

class Door(BaseModel):
    x: float; y: float; w: float

SymbolType = Literal["socket","switch","light","panel","junction"]

class Symbol(BaseModel):
    type: SymbolType
    x: float; y: float
    rotation: float = 0.0
    meta: Optional[Dict[str, Any]] = None

class Plan(BaseModel):
    walls: List[Wall] = Field(default_factory=list)
    doors: List[Door] = Field(default_factory=list)
    scale_mm_per_px: Optional[float] = None

class DetectionResult(BaseModel):
    symbols: List[Symbol] = Field(default_factory=list)

class RouteRequest(BaseModel):
    plan: Plan
    detection: DetectionResult
    ruleset: Literal["NEC2023","PUE","Custom"] = "NEC2023"

class Polyline(BaseModel):
    points: List[List[float]]

class RouteResponse(BaseModel):
    routes: Dict[str, List[Polyline]]
    warnings: List[str] = Field(default_factory=list)
    estimate: Dict[str, Any] = Field(default_factory=dict)

# ---- Endpoints (mock parsers/detectors) ----

@app.post("/parse", response_model=Plan)
async def parse_plan(file: UploadFile = File(...)):
    # Заглушка: клиент уже присылает план как JSON; 
    # если PNG/PDF — на проде подключите CV/ML-пайплайн.
    if file.content_type in ["application/json","text/json"]:
        data = json.load(io.TextIOWrapper(file.file, encoding="utf-8"))
        return Plan(**data)
    raise HTTPException(415, "Заглушка: поддержан только JSON (walls/doors).")

@app.post("/detect", response_model=DetectionResult)
async def detect_symbols(file: UploadFile = File(...)):
    # Заглушка: клиент может прислать detection JSON
    if file.content_type in ["application/json","text/json"]:
        data = json.load(io.TextIOWrapper(file.file, encoding="utf-8"))
        return DetectionResult(**data)
    # Иначе — вернуть пустой результат
    return DetectionResult()

@app.post("/route", response_model=RouteResponse)
async def route(req: RouteRequest):
    G = build_graph_from_walls(req.plan.walls, req.plan.doors)
    # Источник питания — панель (panel). Узлы‑назначения — sockets/lights/switches/junction.
    panels = [s for s in req.detection.symbols if s.type == "panel"]
    if not panels:
        return RouteResponse(routes={}, warnings=["Не найден электрощит (panel)."])
    panel = panels[0]

    by_type = {}
    for t in ["socket","light","switch","junction"]:
        by_type[t] = [s for s in req.detection.symbols if s.type == t]

    routes: Dict[str, list] = {t: [] for t in by_type}
    warnings: List[str] = []

    for t, targets in by_type.items():
        for sym in targets:
            path = route_wires_a_star(G, (panel.x, panel.y), (sym.x, sym.y))
            if path is None:
                warnings.append(f"Нет пути по стенам: {t} @ ({sym.x:.0f},{sym.y:.0f})")
                continue
            routes[t].append({"points": path})

    # Бандлинг/заполнение и валидация по простым правилам
    routes = {k: [Polyline(points=p['points']) for p in v] for k,v in routes.items()}
    bundled = unify_bundles(routes)
    warn_rules = validate_routes(bundled, ruleset=req.ruleset)
    warnings.extend(warn_rules)

    estimate = estimate_bill(bundled)
    return RouteResponse(routes=bundled, warnings=warnings, estimate=estimate)

@app.post("/estimate")
async def estimate_only(body: RouteResponse):
    return estimate_bill(body.routes)


@app.post("/projects", response_model=ProjectOut)
async def create_project(p: ProjectIn, db: Session = Depends(get_db)):
    pr = Project(
        title=p.title,
        plan_json=ORJSONResponse.render(p.plan.model_dump()).decode(),
        detection_json=ORJSONResponse.render(p.detection.model_dump()).decode(),
        routes_json=ORJSONResponse.render(p.routes).decode(),
        estimate_json=ORJSONResponse.render(p.estimate).decode()
    )
    db.add(pr); db.commit(); db.refresh(pr)
    return ProjectOut(id=pr.id, title=pr.title)

@app.get("/projects/{pid}")
async def get_project(pid: int, db: Session = Depends(get_db)):
    pr = db.get(Project, pid)
    if not pr: raise HTTPException(404, "Not found")
    return {
        "id": pr.id,
        "title": pr.title,
        "plan": json.loads(pr.plan_json),
        "detection": json.loads(pr.detection_json),
        "routes": json.loads(pr.routes_json),
        "estimate": json.loads(pr.estimate_json),
    }

@app.get("/projects")
async def list_projects(db: Session = Depends(get_db)):
    return [{"id": p.id, "title": p.title} for p in db.query(Project).order_by(Project.id.desc()).all()]

