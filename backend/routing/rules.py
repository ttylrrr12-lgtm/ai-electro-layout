from typing import Dict, Any, List
import math

# Упрощённые нормы/оценки. На проде — профиль правил NEC/ПУЭ в JSON.

CABLE_PRICE_PER_M = {
    "socket": 0.7,   # условная цена/м (материал)
    "light": 0.6,
    "switch": 0.6,
    "junction": 0.5
}
LABOR_PRICE_PER_M = 1.1

def _polyline_length(points: list) -> float:
    total = 0.0
    for i in range(len(points)-1):
        x1,y1 = points[i]; x2,y2 = points[i+1]
        total += math.dist((x1,y1),(x2,y2))
    return total

def estimate_bill(routes: Dict[str, list]) -> Dict[str, Any]:
    items = []
    total = 0.0
    for kind, polylines in routes.items():
        length = sum(_polyline_length(p.points) for p in polylines) / 1000.0  # мм→м
        mat = length * CABLE_PRICE_PER_M.get(kind, 0.6)
        labor = length * LABOR_PRICE_PER_M
        cost = mat + labor
        items.append({"kind": kind, "length_m": round(length,2), "materials": round(mat,2), "labor": round(labor,2), "cost": round(cost,2)})
        total += cost
    return {"items": items, "total": round(total,2)}

def validate_routes(routes: Dict[str, list], ruleset: str = "NEC2023") -> List[str]:
    warnings = []
    # Здесь можно проверять заполнение каналов, радиусы изгиба, запреты через двери и мокрые зоны и др.
    # Для MVP просто возвращаем пусто.
    return warnings
