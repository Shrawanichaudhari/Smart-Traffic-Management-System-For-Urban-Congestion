import asyncio
import json
import random
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# -----------------------------
# City configuration (demo)
# -----------------------------
CITY_ID = "CITY_DEMO"
CITY_CENTER = {"lat": 28.6139, "lng": 77.2090}  # editable later

# Small 2x2 grid of intersections around a center.
CITY_NODES = [
    {
        "intersection_id": "INT_A",
        "name": "Node A",
        "lat": CITY_CENTER["lat"] + 0.0030,
        "lng": CITY_CENTER["lng"] + 0.0030,
        "neighbors": ["INT_B", "INT_C"],
    },
    {
        "intersection_id": "INT_B",
        "name": "Node B",
        "lat": CITY_CENTER["lat"] + 0.0030,
        "lng": CITY_CENTER["lng"] - 0.0030,
        "neighbors": ["INT_A", "INT_D"],
    },
    {
        "intersection_id": "INT_C",
        "name": "Node C",
        "lat": CITY_CENTER["lat"] - 0.0030,
        "lng": CITY_CENTER["lng"] + 0.0030,
        "neighbors": ["INT_A", "INT_D"],
    },
    {
        "intersection_id": "INT_D",
        "name": "Node D",
        "lat": CITY_CENTER["lat"] - 0.0030,
        "lng": CITY_CENTER["lng"] - 0.0030,
        "neighbors": ["INT_B", "INT_C"],
    },
]

DIRECTIONS = ["north", "south", "east", "west"]


# -----------------------------
# State models
# -----------------------------
@dataclass
class Incident:
    incident_id: str
    intersection_id: str
    direction: str
    incident_type: str  # accident / event / roadblock
    severity: int
    created_at: str
    status: str  # active/cleared


@dataclass
class AmbulanceRoute:
    route_id: str
    from_intersection: str
    to_intersection: str
    created_at: str
    eta_seconds: int
    status: str  # enroute / arrived / cleared


@dataclass
class Explainability:
    policy: str
    reason: str
    phase_scores: Dict[str, float]
    chosen_phase: str
    emergency_preemption: bool
    notes: str


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        payload = json.dumps(message)
        disconnected: List[WebSocket] = []
        for ws in self.active_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)


# -----------------------------
# App
# -----------------------------
app = FastAPI(title="City Traffic WebSocket API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()

# City state (in-memory demo)
incidents: Dict[str, Incident] = {}
routes: Dict[str, AmbulanceRoute] = {}

# Keep a short event log for UI timeline/replay.
event_log: Deque[Dict[str, Any]] = deque(maxlen=500)

# Per-node traffic state
node_metrics: Dict[str, Dict[str, Any]] = {}


def log_event(event_type: str, data: Dict[str, Any]):
    evt = {"type": event_type, "timestamp": utc_now_iso(), "data": data}
    event_log.append(evt)


def ensure_node_state():
    for n in CITY_NODES:
        nid = n["intersection_id"]
        if nid not in node_metrics:
            node_metrics[nid] = {
                "direction_metrics": {
                    d: {
                        "vehicle_counts": {"car": 0, "bus": 0, "truck": 0, "bike": 0},
                        "queue_length": 0,
                        "vehicles_crossed": 0,
                        "avg_wait_time": 0.0,
                        "emergency_vehicle_present": False,
                    }
                    for d in DIRECTIONS
                },
                "current_phase": {
                    "phase_id": 0,
                    "active_directions": ["east", "west"],
                    "status": "GREEN",
                    "remaining_time": 20,
                },
                "overall_metrics": {
                    "total_vehicles_passed": 0,
                    "avg_wait_time_all_sides": 0.0,
                    "throughput": 0.0,
                    "avg_speed": 0.0,
                    "cycle_time": 60,
                },
                "explainability": None,
            }


def simulate_node_tick(intersection_id: str):
    """A lightweight simulator for demo UI. Replace later with real ML/pygame ingestion."""
    st = node_metrics[intersection_id]

    # Update queues randomly
    total_q = 0
    total_wait = 0.0
    total_crossed = 0

    # Ambulance inbound -> mark emergency present for target node (preemption)
    inbound = any(r.to_intersection == intersection_id and r.status == "enroute" for r in routes.values())

    for d in DIRECTIONS:
        m = st["direction_metrics"][d]
        q = max(0, m["queue_length"] + random.randint(-1, 3))
        m["queue_length"] = q
        total_q += q

        # Vehicle type split
        car = max(0, int(q * 0.65))
        bike = max(0, int(q * 0.15))
        bus = max(0, int(q * 0.10))
        truck = max(0, q - car - bike - bus)
        m["vehicle_counts"] = {"car": car, "bus": bus, "truck": truck, "bike": bike}

        # Wait time approximation
        m["avg_wait_time"] = round(min(90.0, 5.0 + q * 2.0 + random.uniform(-2, 2)), 1)
        total_wait += m["avg_wait_time"]

        # Emergency present if inbound and direction is the assumed arrival corridor.
        m["emergency_vehicle_present"] = bool(inbound and d in ("east", "west"))

        # Crossed (only when green)
        total_crossed += random.randint(0, 3)

    # Simple max-pressure-ish phase choice
    ew = st["direction_metrics"]["east"]["queue_length"] + st["direction_metrics"]["west"]["queue_length"]
    ns = st["direction_metrics"]["north"]["queue_length"] + st["direction_metrics"]["south"]["queue_length"]

    emergency_preempt = inbound
    chosen = "EW" if ew >= ns else "NS"
    if emergency_preempt:
        chosen = "EW"  # pretend corridor arrives from E/W in this demo

    active = ["east", "west"] if chosen == "EW" else ["north", "south"]

    st["current_phase"] = {
        "phase_id": 0 if chosen == "EW" else 1,
        "active_directions": active,
        "status": "GREEN",
        "remaining_time": random.randint(10, 30),
    }

    st["overall_metrics"] = {
        "total_vehicles_passed": st["overall_metrics"]["total_vehicles_passed"] + total_crossed,
        "avg_wait_time_all_sides": round(total_wait / 4.0, 1),
        "throughput": round(total_crossed / 2.0, 2),
        "avg_speed": round(random.uniform(12, 35), 1),
        "cycle_time": 60,
    }

    st["explainability"] = asdict(
        Explainability(
            policy="max_pressure",
            reason="emergency_preemption" if emergency_preempt else "max_pressure_selection",
            phase_scores={"EW": float(ew), "NS": float(ns)},
            chosen_phase=chosen,
            emergency_preemption=emergency_preempt,
            notes=(
                "Inbound ambulance detected → preempted corridor" if emergency_preempt else "Selected busiest phase"
            ),
        )
    )


def build_city_update() -> Dict[str, Any]:
    nodes_payload = []
    for n in CITY_NODES:
        nid = n["intersection_id"]
        st = node_metrics[nid]
        nodes_payload.append(
            {
                "intersection_id": nid,
                "name": n["name"],
                "lat": n["lat"],
                "lng": n["lng"],
                "neighbors": n["neighbors"],
                "current_phase": st["current_phase"],
                "overall_metrics": st["overall_metrics"],
                "direction_metrics": st["direction_metrics"],
                "explainability": st.get("explainability"),
            }
        )

    return {
        "type": "city_update",
        "timestamp": utc_now_iso(),
        "city": {"city_id": CITY_ID, "center": CITY_CENTER, "nodes": nodes_payload},
        "incidents": [asdict(i) for i in incidents.values() if i.status == "active"],
        "ambulance_routes": [asdict(r) for r in routes.values()],
        "event_log_tail": list(event_log)[-25:],
    }


def make_id(prefix: str) -> str:
    return f"{prefix}_{int(datetime.now(timezone.utc).timestamp())}_{random.randint(1000, 9999)}"


async def tick_routes():
    # Decrement ETA and update status
    for r in routes.values():
        if r.status != "enroute":
            continue
        r.eta_seconds = max(0, r.eta_seconds - 2)
        if r.eta_seconds == 0:
            r.status = "arrived"
            log_event(
                "ambulance_arrived",
                {
                    "route_id": r.route_id,
                    "to_intersection": r.to_intersection,
                },
            )


# -----------------------------
# HTTP endpoints
# -----------------------------
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "timestamp": utc_now_iso(),
    }


@app.get("/city/config")
def city_config():
    return {"city_id": CITY_ID, "center": CITY_CENTER, "nodes": CITY_NODES}


@app.get("/city/events")
def city_events():
    return {"events": list(event_log)}


# -----------------------------
# WebSocket
# -----------------------------
@app.websocket("/ws/city")
async def ws_city(websocket: WebSocket):
    await manager.connect(websocket)

    # Send initial snapshot
    ensure_node_state()
    await websocket.send_text(json.dumps(build_city_update()))

    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=0.25)
            except asyncio.TimeoutError:
                continue

            try:
                msg = json.loads(raw)
            except Exception:
                continue

            mtype = msg.get("type")

            if mtype == "incident_create":
                inc = Incident(
                    incident_id=make_id("INC"),
                    intersection_id=msg.get("intersection_id", "INT_A"),
                    direction=msg.get("direction", "east"),
                    incident_type=msg.get("incident_type", "accident"),
                    severity=int(msg.get("severity", 2)),
                    created_at=utc_now_iso(),
                    status="active",
                )
                incidents[inc.incident_id] = inc
                log_event("incident_created", asdict(inc))
                await manager.broadcast({"type": "incident_update", "timestamp": utc_now_iso(), "incident": asdict(inc)})

            elif mtype == "incident_clear":
                incident_id = msg.get("incident_id")
                if incident_id and incident_id in incidents:
                    incidents[incident_id].status = "cleared"
                    log_event("incident_cleared", {"incident_id": incident_id})
                    await manager.broadcast(
                        {
                            "type": "incident_update",
                            "timestamp": utc_now_iso(),
                            "incident": asdict(incidents[incident_id]),
                        }
                    )

            elif mtype == "dispatch_ambulance":
                route = AmbulanceRoute(
                    route_id=make_id("AMB"),
                    from_intersection=msg.get("from_intersection", "INT_A"),
                    to_intersection=msg.get("to_intersection", "INT_B"),
                    created_at=utc_now_iso(),
                    eta_seconds=int(msg.get("eta_seconds", 30)),
                    status="enroute",
                )
                routes[route.route_id] = route
                log_event("ambulance_dispatched", asdict(route))
                await manager.broadcast(
                    {
                        "type": "ambulance_route_update",
                        "timestamp": utc_now_iso(),
                        "route": asdict(route),
                    }
                )

            elif mtype == "clear_ambulance_route":
                route_id = msg.get("route_id")
                if route_id and route_id in routes:
                    routes[route_id].status = "cleared"
                    log_event("ambulance_route_cleared", {"route_id": route_id})

            elif mtype == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": utc_now_iso()}))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# -----------------------------
# Broadcaster loop
# -----------------------------
async def broadcast_loop():
    ensure_node_state()
    while True:
        # update nodes
        for n in CITY_NODES:
            simulate_node_tick(n["intersection_id"])

        await tick_routes()

        msg = build_city_update()
        log_event("city_update", {"summary": {"nodes": len(CITY_NODES)}})

        if manager.active_connections:
            await manager.broadcast(msg)

        await asyncio.sleep(2)


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(broadcast_loop())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
