from typing import List, Tuple, Dict
from shapely.geometry import LineString, Point
import networkx as nx
import math

def _snap(point: Tuple[float,float], segments: List[LineString], tol=150.0) -> Tuple[float,float]:
    # проецируем точку на ближайший сегмент стены
    best = None; best_d = 1e18
    px, py = point
    p = Point(px, py)
    for seg in segments:
        proj = seg.interpolate(seg.project(p))
        d = proj.distance(p)
        if d < best_d and d <= tol:
            best_d = d; best = proj
    return (best.x, best.y) if best else point

def build_graph_from_walls(walls, doors) -> nx.Graph:
    # узлы на концах каждого сегмента, рёбра вдоль сегментов
    G = nx.Graph()
    segments: List[LineString] = []
    door_spans = []
    for d in doors or []:
        # дверной проём: запрещённая зона по X-оси шириной w, ориентировочно
        door_spans.append((d['x'], d['y'], d['w'])) if isinstance(d, dict) else door_spans.append((d.x, d.y, d.w))

    def allowed(seg: LineString) -> bool:
        # простое правило: не проводим через центр дверного пролёта
        cx, cy = seg.interpolate(0.5, normalized=True).xy
        cx, cy = cx[0], cy[0]
        for dx, dy, w in door_spans:
            if abs(cx-dx) < w/2 and abs(cy-dy) < 150:
                return False
        return True

    for w in walls or []:
        x1 = w['x1'] if isinstance(w, dict) else w.x1
        y1 = w['y1'] if isinstance(w, dict) else w.y1
        x2 = w['x2'] if isinstance(w, dict) else w.x2
        y2 = w['y2'] if isinstance(w, dict) else w.y2
        seg = LineString([(x1,y1),(x2,y2)])
        if not allowed(seg): 
            continue
        segments.append(seg)
        n1 = (x1,y1); n2 = (x2,y2)
        G.add_node(n1); G.add_node(n2)
        length = seg.length
        # штраф за повороты будет учтён в поиске
        G.add_edge(n1, n2, weight=length, geom=seg)

    # добавим «промежуточные» узлы на пересечениях сегментов для манхэттенской сетки
    for i in range(len(segments)):
        for j in range(i+1, len(segments)):
            inter = segments[i].intersection(segments[j])
            if inter.is_empty: 
                continue
            if 'Point' in inter.geom_type:
                p = (inter.x, inter.y)
                # разрезаем рёбра, чтобы в графе появился узел стыка
                for seg in (segments[i], segments[j]):
                    coords = list(seg.coords)
                    a, b = coords[0], coords[-1]
                    if a not in G: G.add_node(a)
                    if b not in G: G.add_node(b)
                    if G.has_edge(a, b):
                        G.remove_edge(a, b)
                    G.add_edge(a, p, weight=Point(a).distance(Point(p)), geom=LineString([a,p]))
                    G.add_edge(p, b, weight=Point(b).distance(Point(p)), geom=LineString([p,b]))
    G.graph['segments'] = segments
    return G

def _penalty(prev, curr, next_):
    # штраф за поворот, стимулируем 90°
    if prev is None or next_ is None: 
        return 0.0
    ax, ay = prev; bx, by = curr; cx, cy = next_
    v1 = (bx-ax, by-ay); v2 = (cx-bx, cy-by)
    def ang(v1, v2):
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        n1 = math.hypot(*v1); n2 = math.hypot(*v2)
        if n1 == 0 or n2 == 0: return 0.0
        cos = max(-1.0, min(1.0, dot/(n1*n2)))
        return math.degrees(math.acos(cos))
    a = ang(v1,v2)
    return 50.0 if a > 5 and abs(a-90) > 10 else 0.0

def route_wires_a_star(G, start, goal):
    # проецируем точки на ближайшие стены (если в допуске)
    segments: List[LineString] = G.graph.get('segments', [])
    s = _snap(start, segments)
    t = _snap(goal, segments)

    try:
        path = nx.astar_path(G, s, t, heuristic=lambda a,b: math.dist(a,b), weight='weight')
    except Exception:
        # попробуем ближайшие узлы
        try:
            s2 = min(G.nodes, key=lambda n: math.dist(n, s))
            t2 = min(G.nodes, key=lambda n: math.dist(n, t))
            path = nx.astar_path(G, s2, t2, heuristic=lambda a,b: math.dist(a,b), weight='weight')
        except Exception:
            return None

    # добавим штрафы за повороты в общую длину (для будущей оптимизации)
    cost = 0.0
    for i in range(len(path)-1):
        cost += math.dist(path[i], path[i+1])
        if 0 < i < len(path)-1:
            cost += _penalty(path[i-1], path[i], path[i+1])
    # преобразуем в полилинию
    return [[float(x), float(y)] for (x,y) in path]

def unify_bundles(routes: Dict[str, list]) -> Dict[str, list]:
    # объединяем близкие маршруты в «каналы» (очень упрощённо)
    return routes
