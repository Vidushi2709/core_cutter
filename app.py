from fastapi import FastAPI, HTTPException  # BackgroundTasks, asyncio not needed anymore
from pydantic import BaseModel
import uvicorn
# import asyncio  # Not needed - commented out auto-balance endpoints
from main import PhaseBalancingController
from utility import DataStorage  # HouseRegistry, PhaseRegistry not directly used
# from configerations import AUTO_BALANCE_INTERVAL  # Not needed - commented out auto-balance

# Pydantic models
class TelemetryData(BaseModel):
    """
    Incoming telemetry from IoT sensor.

    - house_id: unique house identifier
    - voltage: instantaneous voltage
    - power_kw: signed power (positive = import / consumption, negative = export / generation)
    - phase: physical phase reported by the sensor (used on first sight of a house)
    """
    house_id: str
    voltage: float
    power_kw: float
    phase: str


class HouseRegistration(BaseModel):
    house_id: str
    initial_phase: str


# class ManualSwitchRequest(BaseModel):  # Not needed - commented out manual switch endpoint
#     house_id: str
#     to_phase: str

app = FastAPI(title="Phase Balancing Controller", version="1.0")
controller = PhaseBalancingController(DataStorage())  
# auto_balance_running = False  # Not needed - commented out auto-balance endpoints


# async def _auto_balance_loop(interval: int):
#     """DEPRECATED: Not needed"""
#     global auto_balance_running
#     while auto_balance_running:
#         try:
#             controller.run_cycle()
#         except Exception:
#             pass
#         await asyncio.sleep(interval)

# @app.post("/house/register_house")
# def register_house(house: HouseRegistration):
#     """DEPRECATED: Not needed"""
#     # register a new house
#     try:
#         controller.registry.add_house(house.house_id, house.initial_phase)
#         return {"status": "success", "message": f"House {house.house_id} registered on phase {house.initial_phase}"}
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))

@app.post("/telemetry")
def telemetry(data: TelemetryData):
    """
    Single telemetry endpoint:
    1. Accepts telemetry from the IoT sensor (house_id, voltage, power_kw, phase).
    2. Ensures the house exists in the registry (auto-registers on first sight using `phase`).
    3. Runs the full balancing logic.
    4. Returns ONLY the switching recommendation (where to switch), if any.
    """
    try:
        house_id = data.house_id

        # 1) Ensure house exists. If not, auto-register it with the reported phase.
        if house_id not in controller.registry.houses:
            controller.registry.add_house(house_id, data.phase)

        # 2) Update latest reading for this house
        controller.registry.update_reading(house_id, data.voltage, data.power_kw)

        # 3) Run one balancing cycle (this will also apply a switch if recommended)
        status = controller.run_cycle()

        # 4) Return just the recommendation ("where do we switch")
        recommendation = status.get("recommendation")

        # Caller only cares about phase outcome, so return a compact payload.
        if recommendation:
            return {
                "status": "success",
                "new_phase": recommendation["to_phase"],
            }

        # No switch -> keep the current phase of the reporting house.
        return {
            "status": "success",
            "new_phase": controller.registry.houses[house_id].phase,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# @app.post("/house/telemetry")
# def get_telemetry(data: TelemetryData):
#     """DEPRECATED: Use /telemetry instead"""
#     try:
#         controller.registry.update_reading(data.house_id, data.voltage, data.power_kw)
#         return {"status": "success", "message": f"Telemetry updated for house {data.house_id}"}
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))

# @app.post("/status")
# def get_status():
#     """DEPRECATED: Use /telemetry instead"""
#     phase_stats = controller.analyzer.get_phase_stats()
#     mode = controller.analyzer.detect_mode(phase_stats) 
#     imbalance = controller.analyzer.get_imbalance(phase_stats)
#     phase_issues = controller.analyzer.detect_voltage_issues(phase_stats)
#     power_issues = controller.analyzer.detect_power_issues(phase_stats)

#     return{
#         "mode": mode,
#         "imbalance_kw": round(imbalance, 2),
#         "phase_stats": [
#             {
#                 "phase": ps.phase,
#                 "power_kw": round(ps.total_power_kw, 2),
#                 "voltage": round(ps.avg_voltage, 1) if ps.avg_voltage else None,
#                 "house_count": ps.house_count
#             }
#             for ps in phase_stats
#         ],
#         "phase_issues": phase_issues,
#         "power_issues": power_issues,
#         "houses": {
#             hid:{
#                 "phase": h.phase,
#                 "last_changed": h.last_changed.isoformat(),
#                 "last_reading": {
#                     "voltage": h.last_reading.voltage,
#                     "power_kw": h.last_reading.power_kw,
#                     "timestamp": h.last_reading.timestamp.isoformat(),
#                 } if h.last_reading else None 
#             }
#             for hid, h in controller.registry.houses.items()
#         }
#     }

# @app.post("/balance/run")
# def run_balance_cycle():
#     """DEPRECATED: Not needed - use /telemetry endpoint"""
#     try:
#         status = controller.run_cycle()
#         return status
#     except Exception as e:
#         import traceback
#         return {"error": str(e), "trace": traceback.format_exc()}

# @app.post("/balance/auto/start")
# async def start_auto_balance(background_tasks: BackgroundTasks):
#     """DEPRECATED: Not needed"""
#     """Start automatic balancing"""
#     global auto_balance_running
#     if auto_balance_running:
#         return {"status": "info", "message": "Auto-balance already running"}

#     auto_balance_running = True
#     # start background loop (non-blocking)
#     asyncio.create_task(_auto_balance_loop(AUTO_BALANCE_INTERVAL))
#     return {"status": "success", "message": f"Auto-balance started (interval: {AUTO_BALANCE_INTERVAL}s)"}


# @app.post("/balance/auto/stop")
# def stop_auto_balance():
#     """DEPRECATED: Not needed"""
#     """Stop automatic balancing"""
#     global auto_balance_running
#     auto_balance_running = False
#     return {"status": "success", "message": "Auto-balance stopped"}

# @app.post("/switch/manual")
# def manual_switch(req: ManualSwitchRequest):
#     """DEPRECATED: Not needed"""
#     """Manually switch a house to a different phase"""
#     try:
#         controller.registry.apply_switch(req.house_id, req.to_phase)
#         return {"status": "success", "message": f"House {req.house_id} switched to {req.to_phase}"}
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @app.get("/history/switches")
# def get_switch_history(limit: int = 50):
#     """DEPRECATED: Not needed"""
#     """Get recent switch history"""
#     history = controller.storage.get_switch_history(limit)
#     return {"switches": history}

# @app.get("/history/telemetry")
# def get_telemetry_history(house_id: str, hours: int = 24):
#     """DEPRECATED: Not needed"""
#     telemetry = controller.storage.get_recent_telemetry(house_id, hours)
#     return {
#         "house_id": house_id,
#         "telemetry": [t.to_dict() for t in telemetry],
#         "count": len(telemetry)
#     }

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Phase Balancing Controller is running"}

@app.get("/")
def root():
    return {
        "name": "Phase Balancing Controller",
        "version": "1.0",
        "endpoints": [
            "/telemetry",  # Single endpoint for telemetry + status (includes phase info)
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)