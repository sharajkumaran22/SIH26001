import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from .models import (
    RiskInput, RiskResult, LocationModel, AlertModel,
    AcknowledgeRequest, FieldObservationModel, ScenarioModel
)
from .risk_engine import assess_landslide_risk, get_ml_pipeline_info, GEO_ZONES
from .database import (
    init_db, get_all_locations, get_location_by_id, update_location_risk,
    get_alerts, add_alert, acknowledge_alert, log_prediction,
    get_location_history, add_field_observation, get_field_observations
)

# Initialize Database tables and demonstration seed records
init_db()

app = FastAPI(
    title="LAND-SAFE AI API",
    description="AI-Based Early Warning & Landslide Risk Monitoring System for the North Eastern Region (NER)",
    version="1.1.0"
)

# CORS configuration for development and hackathon presentation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))


# ---------------------------------------------------------
# REST API Endpoints
# ---------------------------------------------------------

@app.get("/api/health")
def get_system_health():
    """System health check and operational mode indicators."""
    ml_info = get_ml_pipeline_info()
    return {
        "status": "OPERATIONAL",
        "system": "LAND-SAFE AI Decision-Support System",
        "region": "North Eastern Region (NER) - 8 Monitored Zones",
        "mode": "DEMO / SIMULATION MODE",
        "data_honesty": "Using seeded demonstration and simulated in-situ sensor readings. Ready for IMD/IoT/GIS integration.",
        "risk_engines": {
            "transparent_weighted": "35% Rainfall, 25% Soil Moisture, 20% Slope, 20% Ground Movement",
            "machine_learning": f"Calibrated Random Forest Pipeline (Status: {ml_info['status']})"
        },
        "ml_accuracy": f"{ml_info.get('accuracy', 0.0) * 100:.1f}%",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/scenarios", response_model=List[ScenarioModel])
def get_demo_scenarios():
    """Pre-configured demo scenarios for SIH live evaluation."""
    return [
        ScenarioModel(
            id="normal",
            title="Normal Conditions",
            description="Clear weather, stable hill slopes, typical pre-monsoon baseline.",
            rainfall=30.0,
            soil_moisture=35.0,
            slope=12.0,
            ground_movement=0.5,
            expected_level="LOW"
        ),
        ScenarioModel(
            id="high_rainfall",
            title="High Rainfall Advisory",
            description="Moderate to heavy rainband over gentle to moderate slope.",
            rainfall=140.0,
            soil_moisture=52.0,
            slope=18.0,
            ground_movement=1.2,
            expected_level="MODERATE"
        ),
        ScenarioModel(
            id="high_risk",
            title="High Landslide Risk",
            description="Sustained monsoon downpour with elevated pore pressure and noticeable slope creep.",
            rainfall=150.0,
            soil_moisture=75.0,
            slope=32.0,
            ground_movement=5.5,
            expected_level="HIGH"
        ),
        ScenarioModel(
            id="critical",
            title="Critical Conditions",
            description="Torrential rainfall, highly saturated soil, steep cutting, accelerated shear displacement.",
            rainfall=190.0,
            soil_moisture=88.0,
            slope=40.0,
            ground_movement=8.5,
            expected_level="CRITICAL"
        ),
    ]


@app.get("/api/locations", response_model=List[LocationModel])
def list_monitored_locations():
    """Retrieve all monitored NER locations with current readings and risk status."""
    return get_all_locations()


@app.get("/api/location/{location_id}")
def get_location_details(location_id: str):
    """Retrieve detailed location profile and 7-day time-series readings."""
    loc = get_location_by_id(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail=f"Monitored location '{location_id}' not found.")
    
    history = get_location_history(location_id)
    return {
        "location": loc,
        "history": history
    }


@app.post("/api/predict", response_model=RiskResult)
def predict_landslide_risk(input_data: RiskInput):
    """
    Execute AI/ML Risk Engine on provided environmental and geospatial inputs.
    Supports both:
    - 'weighted': Transparent normalized heuristic model (35/25/20/20)
    - 'ml_rf': Calibrated Random Forest Ensemble Classifier with Geospatial Feature Engineering
    """
    try:
        # Run selected risk engine
        result = assess_landslide_risk(input_data)

        # Log prediction to SQLite
        log_prediction(
            loc_id=input_data.location_id,
            rain=input_data.rainfall,
            soil=input_data.soil_moisture,
            slope=input_data.slope,
            ground=input_data.ground_movement,
            score=result.risk_score,
            level=result.risk_level,
            factors=result.factors
        )

        # If analyzing a registered location, dynamically sync location status & trigger alert
        if input_data.location_id:
            loc = get_location_by_id(input_data.location_id)
            if loc:
                update_location_risk(
                    loc_id=input_data.location_id,
                    score=result.risk_score,
                    level=result.risk_level,
                    rain=input_data.rainfall,
                    soil=input_data.soil_moisture,
                    ground=input_data.ground_movement
                )

                # If risk is HIGH or CRITICAL, ensure an active early warning alert exists
                if result.early_warning:
                    alert_id = f"ALT-{input_data.location_id}-{datetime.now().strftime('%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
                    add_alert({
                        "id": alert_id,
                        "location_id": loc["id"],
                        "location_name": loc["name"],
                        "state": loc["state"],
                        "risk_score": result.risk_score,
                        "risk_level": result.risk_level,
                        "main_factors": result.factors[:4],
                        "recommended_action": result.recommended_action,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk Engine computation error: {str(e)}"
        )


@app.get("/api/alerts", response_model=List[AlertModel])
def list_alerts():
    """Retrieve all active and acknowledged early warnings."""
    return get_alerts()


@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_warning(alert_id: str, req: AcknowledgeRequest):
    """Officer acknowledgment of an early warning alert."""
    success = acknowledge_alert(alert_id, req.officer_name, req.notes)
    if not success:
        raise HTTPException(status_code=404, detail=f"Alert with ID '{alert_id}' not found.")
    return {
        "status": "success",
        "message": f"Alert '{alert_id}' marked as ACKNOWLEDGED by {req.officer_name}.",
        "acknowledged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


@app.post("/api/observations")
def record_observation(obs: FieldObservationModel):
    """Save field officer site observation with photo and verification notes."""
    obs_id = add_field_observation(
        loc_id=obs.location_id,
        loc_name=obs.location_name,
        officer=obs.officer_name,
        notes=obs.notes,
        photo=obs.photo_data
    )
    return {
        "status": "success",
        "observation_id": obs_id,
        "message": "Field observation and photo recorded in local database."
    }


@app.get("/api/observations")
def list_observations():
    """Retrieve all recorded field observations."""
    return get_field_observations()


@app.get("/api/ml-status")
def get_ml_architecture_status():
    """Metadata regarding prototype risk engine vs trained ML models and regional calibration."""
    ml_info = get_ml_pipeline_info()
    model_path = ml_info["model_path"]
    trained_model_exists = ml_info["model_file_exists"]

    return {
        "active_engines": [
            "Transparent Weighted Engine (35% Rain, 25% Soil, 20% Slope, 20% Displacement)",
            "Calibrated Random Forest Ensemble Classifier (Scikit-Learn 1.8+)"
        ],
        "ml_pipeline_status": ml_info["status"],
        "accuracy": ml_info.get("accuracy", 1.0),
        "feature_importances": ml_info.get("feature_importances", {}),
        "geo_zones": GEO_ZONES,
        "future_ml_pipeline": {
            "model_architecture": "Random Forest / XGBoost Classifier & Regressor",
            "prototype_trained_model_ready": trained_model_exists,
            "training_script": "ml/train_prototype_ml.py",
            "input_features": [
                "rainfall", "soil_moisture", "slope", "ground_movement", "elevation",
                "ari (Antecedent Rainfall Index)", "twi (Topographic Wetness Index)",
                "pore_water_pressure (kPa)", "displacement_rate (mm/day)", "zone_code"
            ],
            "target": "landslide_risk_classification (LOW, MODERATE, HIGH, CRITICAL)",
            "data_requirement": "Validated regional historical landslide inventory (GSI / NDMA)"
        }
    }


@app.get("/api/ml/zones")
def list_geo_zones():
    """List regional geo-climatic calibration zones for Northeast India."""
    return GEO_ZONES


# ---------------------------------------------------------
# Frontend Static Files Mount
# ---------------------------------------------------------
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
