from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FactorContribution(BaseModel):
    name: str
    raw_value: float
    unit: str
    normalized_score: float  # 0 to 100
    weight: float  # e.g. 0.35
    weighted_score: float
    percentage_contribution: float
    status: str  # Normal, Moderate, High, Severe


class RiskInput(BaseModel):
    location_id: Optional[str] = Field(None, description="Optional ID of monitored location")
    rainfall: float = Field(..., ge=0, le=500, description="Rainfall in mm (past 24-72h aggregate)")
    soil_moisture: float = Field(..., ge=0, le=100, description="Soil moisture percentage (%)")
    slope: float = Field(..., ge=0, le=90, description="Terrain slope angle in degrees")
    ground_movement: float = Field(..., ge=0, le=50, description="Surface ground movement / displacement in mm")
    elevation: Optional[float] = Field(None, description="Elevation in meters above sea level")
    temperature: Optional[float] = Field(None, description="Ambient temperature in Celsius")
    humidity: Optional[float] = Field(None, description="Relative humidity percentage")
    engine_type: Optional[str] = Field("weighted", description="'weighted' (Transparent Normalized) or 'ml_rf' (Calibrated Random Forest)")
    geo_zone: Optional[str] = Field(None, description="Regional Geo-Climatic Zone: 'zone_a', 'zone_b', 'zone_c', or 'auto'")


class RiskResult(BaseModel):
    risk_score: int  # 0 - 100
    risk_level: str  # LOW, MODERATE, HIGH, CRITICAL
    color: str  # hex color code
    factors: List[str]
    detailed_factors: List[FactorContribution]
    recommended_action: str
    early_warning: bool
    timestamp: str
    model_type: str = "Prototype Weighted Engine (Transparent Normalized)"
    confidence_level: str = "Operational Decision Support (Calibrated)"
    engine_type: str = "weighted"  # "weighted" or "ml_rf"
    geo_zone: Optional[str] = None
    geo_zone_name: Optional[str] = None
    class_probabilities: Optional[Dict[str, float]] = None  # e.g. {"LOW": 0.05, "MODERATE": 0.15, "HIGH": 0.60, "CRITICAL": 0.20}
    engineered_features: Optional[Dict[str, float]] = None
    ml_metrics: Optional[Dict[str, Any]] = None


class LocationModel(BaseModel):
    id: str
    name: str
    district: str
    state: str
    latitude: float
    longitude: float
    elevation: float
    slope: float
    last_rainfall: float
    last_soil_moisture: float
    last_ground_movement: float
    temperature: float
    humidity: float
    risk_score: int
    risk_level: str
    data_source: str = "DEMO DATA (Simulated In-situ Sensor / GIS)"
    last_updated: str
    geo_zone: Optional[str] = None


class AlertModel(BaseModel):
    id: str
    location_id: str
    location_name: str
    state: str
    risk_score: int
    risk_level: str
    main_factors: List[str]
    recommended_action: str
    timestamp: str
    status: str  # ACTIVE, ACKNOWLEDGED
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None


class AcknowledgeRequest(BaseModel):
    officer_name: str = "District Disaster Officer"
    notes: Optional[str] = "Dispatched field verification unit."


class FieldObservationModel(BaseModel):
    id: Optional[str] = None
    location_id: str
    location_name: str
    officer_name: str
    notes: str
    photo_data: Optional[str] = None  # Base64 string or image preview placeholder
    timestamp: Optional[str] = None
    cv_status: str = "Future AI Image Assessment Module (Placeholder)"


class ScenarioModel(BaseModel):
    id: str
    title: str
    description: str
    rainfall: float
    soil_moisture: float
    slope: float
    ground_movement: float
    expected_level: str
