from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from main import PhaseBalancingController
from utility import DataStorage

# Pydantic models
class TelemetryData(BaseModel):
    """
    Incoming telemetry from IoT sensor.

    - house_id: unique house identifier
    - voltage: instantaneous voltage
    - current: instantaneous current (negative = export, positive = import)
    - power_kw: signed power (positive = import / consumption, negative = export / generation)
    - phase: physical phase reported by the sensor (used on first sight of a house)
    """
    house_id: str
    voltage: float
    current: float
    power_kw: float
    phase: str


# Response models for real-time analytics website
class HouseReading(BaseModel):
    """Current reading for a single house."""
    house_id: str
    phase: str
    voltage: float
    current: float
    power_kw: float
    timestamp: str
    mode_reading: str  # EXPORT or CONSUME


class PhaseAnalytics(BaseModel):
    """Analytics data for a single phase."""
    phase: str
    total_power_kw: float
    avg_voltage: float
    house_count: int
    houses: list[HouseReading]


class SystemStatus(BaseModel):
    """Overall system status for real-time dashboard."""
    timestamp: str
    mode: str  # EXPORT or CONSUME
    imbalance_kw: float
    phases: list[PhaseAnalytics]
    phase_issues: dict
    power_issues: dict


class SwitchEvent(BaseModel):
    """Switch event for timeline/history view."""
    timestamp: str
    house_id: str
    from_phase: str
    to_phase: str
    reason: str

app = FastAPI(title="Phase Balancing Controller - Real-time Analytics", version="2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "null"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
controller = PhaseBalancingController(DataStorage())

@app.post("/telemetry")
def telemetry(data: TelemetryData):
    try:
        house_id = data.house_id

        if house_id not in controller.registry.houses:
            controller.registry.add_house(house_id, data.phase)

        controller.registry.update_reading(house_id, data.voltage, data.current, data.power_kw)

        controller.run_cycle()

        current_assigned_phase = controller.registry.houses[house_id].phase

        return {
            "status": "success",
            "house_id": house_id,
            "new_phase": current_assigned_phase
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/analytics/status")
def get_system_status() -> SystemStatus:
    try:
        from datetime import datetime, timezone
        
        phase_stats = controller.analyzer.get_phase_stats()
        r_mode = controller.analyzer.detect_mode(phase_stats)
        mode = controller._stable_mode(r_mode)
        imbalance = controller.analyzer.get_imbalance(phase_stats)
        phase_issues = controller.analyzer.detect_voltage_issues(phase_stats)
        power_issues = controller.analyzer.detect_power_issues(phase_stats)
        
        phases_data = []
        for ps in phase_stats:
            houses_on_phase = []
            for house_id, house in controller.registry.houses.items():
                if house.phase == ps.phase and house.last_reading:
                    reading = house.last_reading
                    houses_on_phase.append(HouseReading(
                        house_id=house_id,
                        phase=house.phase,
                        voltage=round(reading.voltage, 2),
                        current=round(reading.current, 2),
                        power_kw=round(reading.power_kw, 3),
                        timestamp=reading.timestamp.isoformat(),
                        mode_reading="EXPORT" if reading.current < 0 else "CONSUME"
                    ))
            
            phases_data.append(PhaseAnalytics(
                phase=ps.phase,
                total_power_kw=round(ps.total_power_kw, 2),
                avg_voltage=round(ps.avg_voltage, 1) if ps.avg_voltage else 0.0,
                house_count=ps.house_count,
                houses=houses_on_phase
            ))
        
        return SystemStatus(
            timestamp=datetime.now(timezone.utc).isoformat(),
            mode=mode,
            imbalance_kw=round(imbalance, 2),
            phases=phases_data,
            phase_issues=phase_issues,
            power_issues=power_issues
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching status: {str(e)}")


@app.get("/analytics/houses")
def get_all_houses() -> list[HouseReading]:
    try:
        houses_list = []
        for house_id, house in controller.registry.houses.items():
            if house.last_reading:
                reading = house.last_reading
                houses_list.append(HouseReading(
                    house_id=house_id,
                    phase=house.phase,
                    voltage=round(reading.voltage, 2),
                    current=round(reading.current, 2),
                    power_kw=round(reading.power_kw, 3),
                    timestamp=reading.timestamp.isoformat(),
                    mode_reading="EXPORT" if reading.current < 0 else "CONSUME"
                ))
        
        houses_list.sort(key=lambda h: h.house_id)
        return houses_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching houses: {str(e)}")


@app.get("/analytics/house/{house_id}")
def get_house_details(house_id: str) -> HouseReading:
    try:
        if house_id not in controller.registry.houses:
            raise HTTPException(status_code=404, detail=f"House {house_id} not found")
        
        house = controller.registry.houses[house_id]
        if not house.last_reading:
            raise HTTPException(status_code=404, detail=f"No reading available for house {house_id}")
        
        reading = house.last_reading
        return HouseReading(
            house_id=house_id,
            phase=house.phase,
            voltage=round(reading.voltage, 2),
            current=round(reading.current, 2),
            power_kw=round(reading.power_kw, 3),
            timestamp=reading.timestamp.isoformat(),
            mode_reading="EXPORT" if reading.current < 0 else "CONSUME"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching house details: {str(e)}")


@app.get("/analytics/switches")
def get_switch_history(limit: int = 50) -> dict:
    try:
        history = controller.storage.get_switch_history(limit)
        switches = [
            SwitchEvent(
                timestamp=event.get("timestamp", ""),
                house_id=event.get("house_id", ""),
                from_phase=event.get("from_phase", ""),
                to_phase=event.get("to_phase", ""),
                reason=event.get("reason", "")
            )
            for event in history
        ]
        return {
            "count": len(switches),
            "switches": switches
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching switch history: {str(e)}")


@app.get("/analytics/phase/{phase}")
def get_phase_details(phase: str) -> PhaseAnalytics:
    try:
        phase_stats = controller.analyzer.get_phase_stats()
        phase_data = next((ps for ps in phase_stats if ps.phase == phase), None)
        
        if not phase_data:
            raise HTTPException(status_code=404, detail=f"Phase {phase} not found")
        
        houses_on_phase = []
        for house_id, house in controller.registry.houses.items():
            if house.phase == phase and house.last_reading:
                reading = house.last_reading
                houses_on_phase.append(HouseReading(
                    house_id=house_id,
                    phase=house.phase,
                    voltage=round(reading.voltage, 2),
                    current=round(reading.current, 2),
                    power_kw=round(reading.power_kw, 3),
                    timestamp=reading.timestamp.isoformat(),
                    mode_reading="EXPORT" if reading.current < 0 else "CONSUME"
                ))
        
        return PhaseAnalytics(
            phase=phase,
            total_power_kw=round(phase_data.total_power_kw, 2),
            avg_voltage=round(phase_data.avg_voltage, 1) if phase_data.avg_voltage else 0.0,
            house_count=phase_data.house_count,
            houses=houses_on_phase
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching phase details: {str(e)}")

@app.get("/health")
def health_check():
    try:
        from datetime import datetime, timezone
        _ = controller.registry.houses
        return {
            "status": "ok",
            "message": "Phase Balancing Controller is running",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "houses_registered": len(controller.registry.houses)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Controller unhealthy: {str(e)}")


@app.get("/")
def root():
    return {
        "name": "Phase Balancing Controller - Real-time Analytics API",
        "version": "2.0",
        "endpoints": {
            "telemetry": "POST /telemetry - Send house reading (voltage, current, power) from IoT device",
            "analytics": {
                "status": "GET /analytics/status - System-wide status (all phases, houses, mode, imbalance)",
                "houses": "GET /analytics/houses - All houses with current readings",
                "house": "GET /analytics/house/{house_id} - Single house details",
                "phase": "GET /analytics/phase/{phase} - Phase analytics with all houses on phase",
                "switches": "GET /analytics/switches - Switch history for timeline view"
            },
            "health": "GET /health - Health check"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)