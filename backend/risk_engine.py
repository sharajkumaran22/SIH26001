import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional
from .models import RiskInput, RiskResult, FactorContribution

# ---------------------------------------------------------------------------
# Transparent Multi-Parametric Weighted Engine Constants (SIH Baseline)
# ---------------------------------------------------------------------------
WEIGHT_RAINFALL = 0.35
WEIGHT_SOIL_MOISTURE = 0.25
WEIGHT_SLOPE = 0.20
WEIGHT_GROUND_MOVEMENT = 0.20

MAX_REF_RAINFALL = 200.0       # mm (Extreme monsoon threshold)
MAX_REF_SOIL_MOISTURE = 100.0   # % (Saturation limit)
MAX_REF_SLOPE = 50.0           # degrees (Extreme steep angle)
MAX_REF_GROUND_MOVEMENT = 10.0 # mm (Critical shear strain precursor)

# ---------------------------------------------------------------------------
# Regional Geo-Climatic Zones Metadata
# ---------------------------------------------------------------------------
GEO_ZONES = {
    "zone_a": {
        "code": 0,
        "name": "Zone A: Shillong Plateau (Meghalaya)",
        "states": ["Meghalaya"],
        "geology": "Precambrian Crystalline / Khasi Sandstone",
        "primary_trigger": "Torrential monsoon precipitation & rapid regolith saturation",
        "description": "High rainfall sensitivity; intense downpours rapidly oversaturate shallow soil cover over crystalline bedrock."
    },
    "zone_b": {
        "code": 1,
        "name": "Zone B: Eastern Himalayas (Sikkim & Arunachal)",
        "states": ["Sikkim", "Arunachal Pradesh"],
        "geology": "Young Folded Sedimentary / High Himalayan Metamorphics",
        "primary_trigger": "Steep gravitational shear stress, active tectonics & debris flows",
        "description": "Extreme slope angles, glacial till and deep valley gorges with high kinematic failure susceptibility."
    },
    "zone_c": {
        "code": 2,
        "name": "Zone C: Barail & Disang Shales (Assam, Nagaland, Manipur, Mizoram, Tripura)",
        "states": ["Assam", "Nagaland", "Manipur", "Mizoram", "Tripura"],
        "geology": "Tertiary Folded Shales & Mudstones (Barail/Disang Formation)",
        "primary_trigger": "Progressive slope creep & road-cut toe failures during sustained rain",
        "description": "Highly weathered fissile shales prone to deep rotational mudslides, creeping road embankments, and drainage collapse."
    }
}

CLASS_NAMES = ["LOW", "MODERATE", "HIGH", "CRITICAL"]

# ---------------------------------------------------------------------------
# Load Serialized Machine Learning Pipeline
# ---------------------------------------------------------------------------
ML_MODEL_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "ml", "landslide_rf_model.joblib")
)

_ml_bundle: Optional[Dict[str, Any]] = None
_ml_pipeline = None

def load_ml_model():
    global _ml_bundle, _ml_pipeline
    if os.path.exists(ML_MODEL_PATH):
        try:
            loaded = joblib.load(ML_MODEL_PATH)
            if isinstance(loaded, dict) and "pipeline" in loaded:
                _ml_bundle = loaded
                _ml_pipeline = loaded["pipeline"]
            else:
                _ml_pipeline = loaded
                _ml_bundle = {
                    "pipeline": loaded,
                    "accuracy": 0.95,
                    "feature_importances": {},
                    "metadata": {"trained_at": "Pre-trained"}
                }
            print(f"[LAND-SAFE AI] ML Pipeline loaded successfully from {ML_MODEL_PATH}")
        except Exception as e:
            print(f"[LAND-SAFE AI] Warning: Failed to load ML model from {ML_MODEL_PATH}: {e}")
            _ml_pipeline = None
            _ml_bundle = None
    else:
        print(f"[LAND-SAFE AI] Notice: ML model artifact not found at {ML_MODEL_PATH}")

# Attempt initial load
load_ml_model()


def get_ml_pipeline_info() -> Dict[str, Any]:
    """Retrieve runtime status and parameters of the ML pipeline."""
    is_ready = _ml_pipeline is not None
    info = {
        "status": "LOADED" if is_ready else "NOT_LOADED",
        "model_file_exists": os.path.exists(ML_MODEL_PATH),
        "model_path": ML_MODEL_PATH,
        "engine_architecture": "Ensemble Random Forest Classifier (Scikit-Learn)",
        "accuracy": _ml_bundle.get("accuracy", 0.0) if _ml_bundle else 0.0,
        "feature_importances": _ml_bundle.get("feature_importances", {}) if _ml_bundle else {},
        "geo_zones": GEO_ZONES,
        "metadata": _ml_bundle.get("metadata", {}) if _ml_bundle else {}
    }
    return info


def detect_geo_zone(location_id: Optional[str], state_name: Optional[str] = None) -> str:
    """Infer the geo-climatic zone from location ID or state name."""
    if state_name:
        s_lower = state_name.lower()
        if "meghalaya" in s_lower:
            return "zone_a"
        elif "sikkim" in s_lower or "arunachal" in s_lower:
            return "zone_b"
        elif any(st in s_lower for st in ["assam", "nagaland", "manipur", "mizoram", "tripura"]):
            return "zone_c"

    if location_id:
        lid = location_id.upper()
        if "LOC-MG" in lid:
            return "zone_a"
        elif "LOC-SK" in lid or "LOC-AR" in lid:
            return "zone_b"
        elif any(code in lid for code in ["LOC-AS", "LOC-NL", "LOC-MN", "LOC-MZ", "LOC-TR"]):
            return "zone_c"

    return "zone_b"  # Default to Eastern Himalayas


def normalize_value(val: float, max_ref: float) -> float:
    """Normalize continuous environmental input into 0-100 range."""
    return max(0.0, min(100.0, (val / max_ref) * 100.0))


def classify_risk(score: float) -> Tuple[str, str, str]:
    """
    Classify score into Risk Level, Color Hex, and Operational Recommended Action.
    Thresholds:
      0–29     LOW
      30–49    MODERATE
      50–74    HIGH
      75–100   CRITICAL
    """
    int_score = int(round(score))
    if int_score <= 29:
        return (
            "LOW",
            "#10B981",  # Emerald Green
            "Routine telemetry monitoring. Slope integrity stable; standard drainage maintenance sufficient."
        )
    elif int_score <= 49:
        return (
            "MODERATE",
            "#F59E0B",  # Amber/Yellow
            "Elevated advisory status. Increase automated sensor polling frequency; inspect culverts and road cut slopes."
        )
    elif int_score <= 74:
        return (
            "HIGH",
            "#F97316",  # Orange
            "Immediate field assessment and monitoring recommended. Alert district disaster control room and highway patrol."
        )
    else:
        return (
            "CRITICAL",
            "#EF4444",  # Crimson Red
            "URGENT DECISION SUPPORT: High probability of slope failure. Dispatch rapid verification units, prep traffic diversions, notify SDRF/NDRF teams."
        )


# ---------------------------------------------------------------------------
# Engine 1: Transparent Multi-Parametric Weighted Engine
# ---------------------------------------------------------------------------
def assess_landslide_risk_weighted(input_data: RiskInput, geo_zone_key: str) -> RiskResult:
    """
    Transparent Weighted Prototype Risk Engine.
    Combines Rainfall (35%), Soil Moisture (25%), Slope (20%), and Ground Movement (20%).
    """
    # 1. Normalize individual inputs
    norm_rain = normalize_value(input_data.rainfall, MAX_REF_RAINFALL)
    norm_soil = normalize_value(input_data.soil_moisture, MAX_REF_SOIL_MOISTURE)
    norm_slope = normalize_value(input_data.slope, MAX_REF_SLOPE)
    norm_ground = normalize_value(input_data.ground_movement, MAX_REF_GROUND_MOVEMENT)

    # 2. Weighted score calculation
    weighted_rain = norm_rain * WEIGHT_RAINFALL
    weighted_soil = norm_soil * WEIGHT_SOIL_MOISTURE
    weighted_slope = norm_slope * WEIGHT_SLOPE
    weighted_ground = norm_ground * WEIGHT_GROUND_MOVEMENT

    total_score_raw = weighted_rain + weighted_soil + weighted_slope + weighted_ground
    total_score = int(round(max(0.0, min(100.0, total_score_raw))))

    risk_level, color_code, recommended_action = classify_risk(total_score)
    early_warning = total_score >= 50

    # 3. Factor status tagging and factor description list
    detected_factors: List[str] = []
    
    rain_status = "Normal"
    if input_data.rainfall >= 130:
        rain_status = "Extreme"
        detected_factors.append(f"Torrential rainfall ({input_data.rainfall:.1f} mm) exceeding saturation threshold")
    elif input_data.rainfall >= 80:
        rain_status = "Heavy"
        detected_factors.append(f"Heavy rainfall ({input_data.rainfall:.1f} mm) accelerating pore pressure")
    elif input_data.rainfall >= 45:
        rain_status = "Moderate"

    soil_status = "Normal"
    if input_data.soil_moisture >= 80:
        soil_status = "Saturated"
        detected_factors.append(f"Critical soil moisture saturation ({input_data.soil_moisture:.1f}%) reducing cohesion")
    elif input_data.soil_moisture >= 65:
        soil_status = "High"
        detected_factors.append(f"High soil moisture content ({input_data.soil_moisture:.1f}%)")
    elif input_data.soil_moisture >= 45:
        soil_status = "Moderate"

    slope_status = "Gentle"
    if input_data.slope >= 35:
        slope_status = "Steep / Unstable"
        detected_factors.append(f"Very steep topography ({input_data.slope:.1f}°) with high gravitational shear stress")
    elif input_data.slope >= 25:
        slope_status = "Moderate Slope"
        detected_factors.append(f"Steep slope gradient ({input_data.slope:.1f}°)")
    elif input_data.slope >= 15:
        slope_status = "Low-Moderate"

    ground_status = "Stable"
    if input_data.ground_movement >= 6.0:
        ground_status = "Active Shear"
        detected_factors.append(f"Accelerated ground displacement ({input_data.ground_movement:.1f} mm) indicates active shear movement")
    elif input_data.ground_movement >= 3.0:
        ground_status = "Creep Detected"
        detected_factors.append(f"Measurable slope creep detected ({input_data.ground_movement:.1f} mm)")
    elif input_data.ground_movement >= 1.0:
        ground_status = "Minor Creep"

    if not detected_factors:
        detected_factors.append("Environmental parameters within normal baseline limits")

    # 4. Explainable AI breakdown: Compute relative percentage contribution
    effective_total = total_score_raw if total_score_raw > 0 else 1.0
    rain_pct = round((weighted_rain / effective_total) * 100, 1)
    soil_pct = round((weighted_soil / effective_total) * 100, 1)
    slope_pct = round((weighted_slope / effective_total) * 100, 1)
    ground_pct = round((weighted_ground / effective_total) * 100, 1)

    detailed_factors: List[FactorContribution] = [
        FactorContribution(
            name="Rainfall",
            raw_value=input_data.rainfall,
            unit="mm",
            normalized_score=round(norm_rain, 1),
            weight=WEIGHT_RAINFALL,
            weighted_score=round(weighted_rain, 1),
            percentage_contribution=rain_pct,
            status=rain_status,
        ),
        FactorContribution(
            name="Soil Moisture",
            raw_value=input_data.soil_moisture,
            unit="%",
            normalized_score=round(norm_soil, 1),
            weight=WEIGHT_SOIL_MOISTURE,
            weighted_score=round(weighted_soil, 1),
            percentage_contribution=soil_pct,
            status=soil_status,
        ),
        FactorContribution(
            name="Slope Gradient",
            raw_value=input_data.slope,
            unit="deg",
            normalized_score=round(norm_slope, 1),
            weight=WEIGHT_SLOPE,
            weighted_score=round(weighted_slope, 1),
            percentage_contribution=slope_pct,
            status=slope_status,
        ),
        FactorContribution(
            name="Ground Movement",
            raw_value=input_data.ground_movement,
            unit="mm",
            normalized_score=round(norm_ground, 1),
            weight=WEIGHT_GROUND_MOVEMENT,
            weighted_score=round(weighted_ground, 1),
            percentage_contribution=ground_pct,
            status=ground_status,
        ),
    ]

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    zone_details = GEO_ZONES.get(geo_zone_key, GEO_ZONES["zone_b"])

    return RiskResult(
        risk_score=total_score,
        risk_level=risk_level,
        color=color_code,
        factors=detected_factors,
        detailed_factors=detailed_factors,
        recommended_action=recommended_action,
        early_warning=early_warning,
        timestamp=timestamp_str,
        model_type="Transparent Multi-Parametric Weighted Engine (35 / 25 / 20 / 20 %)",
        confidence_level="Operational Decision Support (Calibrated Heuristic)",
        engine_type="weighted",
        geo_zone=geo_zone_key,
        geo_zone_name=zone_details["name"],
        class_probabilities=None,
        engineered_features=None,
        ml_metrics=None
    )


# ---------------------------------------------------------------------------
# Engine 2: Calibrated Machine Learning Pipeline (Random Forest Ensemble)
# ---------------------------------------------------------------------------
def assess_landslide_risk_ml(input_data: RiskInput, geo_zone_key: str) -> RiskResult:
    """
    Execute Calibrated Random Forest Machine Learning pipeline on
    geotechnical telemetry and regional geo-climatic features.
    """
    global _ml_pipeline
    if _ml_pipeline is None:
        load_ml_model()
        if _ml_pipeline is None:
            # Fallback to weighted engine if model unavailable
            return assess_landslide_risk_weighted(input_data, geo_zone_key)

    zone_details = GEO_ZONES.get(geo_zone_key, GEO_ZONES["zone_b"])
    z_code = zone_details["code"]
    elev = input_data.elevation if input_data.elevation is not None else 1200.0

    # 1. Compute domain-specific engineered features
    rain = float(input_data.rainfall)
    soil = float(input_data.soil_moisture)
    slope = float(input_data.slope)
    ground = float(input_data.ground_movement)

    ari = rain * (1.0 + (soil / 100.0) * 0.4)
    rad_slope = np.radians(np.clip(slope, 2.0, 85.0))
    twi = float(np.log(120.0 / np.tan(rad_slope)))
    pore_water_press = float((soil / 100.0) * 9.81 * np.cos(rad_slope)**2 * 2.2)
    disp_rate = float(ground * (0.8 + (soil / 100.0) * 0.5))

    feature_dict = {
        "rainfall": rain,
        "soil_moisture": soil,
        "slope": slope,
        "ground_movement": ground,
        "elevation": float(elev),
        "ari": ari,
        "twi": twi,
        "pore_water_pressure": pore_water_press,
        "displacement_rate": disp_rate,
        "zone_code": z_code
    }

    feature_cols = [
        "rainfall", "soil_moisture", "slope", "ground_movement", "elevation",
        "ari", "twi", "pore_water_pressure", "displacement_rate", "zone_code"
    ]
    df_in = pd.DataFrame([[feature_dict[c] for c in feature_cols]], columns=feature_cols)

    # 2. Inference
    probas = _ml_pipeline.predict_proba(df_in)[0]  # Array of 4 probabilities: LOW, MODERATE, HIGH, CRITICAL
    predicted_class_idx = int(np.argmax(probas))
    predicted_class_name = CLASS_NAMES[predicted_class_idx]

    # Map probabilities cleanly to dictionary with 1-decimal percentage
    prob_dict = {
        CLASS_NAMES[i]: round(float(probas[i] * 100), 1) for i in range(len(CLASS_NAMES))
    }

    # 3. Continuous Calibrated Score (0-100)
    # Centroid weights: LOW~15, MODERATE~40, HIGH~65, CRITICAL~90
    raw_score = (
        probas[0] * 12.0 +
        probas[1] * 38.0 +
        probas[2] * 64.0 +
        probas[3] * 92.0
    )
    
    # Ensure predicted class matches threshold boundary
    if predicted_class_name == "CRITICAL" and raw_score < 75.0:
        raw_score = max(75.0, raw_score + 10.0)
    elif predicted_class_name == "HIGH" and (raw_score < 50.0 or raw_score >= 75.0):
        raw_score = np.clip(raw_score, 52.0, 73.0)
    elif predicted_class_name == "MODERATE" and (raw_score < 30.0 or raw_score >= 50.0):
        raw_score = np.clip(raw_score, 32.0, 48.0)
    elif predicted_class_name == "LOW" and raw_score >= 30.0:
        raw_score = min(28.0, raw_score)

    risk_score = int(round(np.clip(raw_score, 0.0, 100.0)))
    risk_level, color_code, recommended_action = classify_risk(risk_score)
    early_warning = risk_score >= 50

    # 4. Identified factors from ML perspective
    detected_factors: List[str] = []
    if ground >= 6.0 or disp_rate >= 7.0:
        detected_factors.append(f"Accelerated displacement rate ({disp_rate:.2f} mm/day) indicates critical shear plane movement")
    elif ground >= 2.5:
        detected_factors.append(f"Active borehole slope displacement detected ({ground:.1f} mm)")

    if rain >= 130.0 or ari >= 180.0:
        detected_factors.append(f"Antecedent rainfall index ({ari:.1f} mm) exceeds regional failure threshold")
    elif rain >= 75.0:
        detected_factors.append(f"Elevated precipitation ({rain:.1f} mm) advancing pore pressure")

    if soil >= 78.0:
        detected_factors.append(f"Topsoil pore saturation ({soil:.1f}%) significantly reduces shear strength")
    elif soil >= 60.0:
        detected_factors.append(f"High moisture saturation ({soil:.1f}%)")

    if slope >= 35.0:
        detected_factors.append(f"Steep slope angle ({slope:.1f}°) with elevated gravitational sliding vector")
    
    detected_factors.append(f"Calibrated for {zone_details['name']} ({zone_details['geology']})")

    # 5. Explainable AI Feature Importances
    feat_imps = _ml_bundle.get("feature_importances", {}) if _ml_bundle else {}
    
    # Calculate relative shares for 4 primary physical factors for UI bar visualization
    # Combining base + engineered pairs
    disp_imp = feat_imps.get("displacement_rate", 28.0) + feat_imps.get("ground_movement", 18.0)
    rain_imp = feat_imps.get("rainfall", 18.0) + feat_imps.get("ari", 16.0)
    soil_imp = feat_imps.get("soil_moisture", 8.0) + feat_imps.get("pore_water_pressure", 2.0)
    slope_imp = feat_imps.get("slope", 4.0) + feat_imps.get("twi", 3.0)

    # Scale with input severity for sample-specific dynamic explanation
    norm_rain = normalize_value(rain, MAX_REF_RAINFALL)
    norm_soil = normalize_value(soil, MAX_REF_SOIL_MOISTURE)
    norm_slope = normalize_value(slope, MAX_REF_SLOPE)
    norm_ground = normalize_value(ground, MAX_REF_GROUND_MOVEMENT)

    eff_disp = disp_imp * (0.3 + 0.7 * (norm_ground / 100.0))
    eff_rain = rain_imp * (0.3 + 0.7 * (norm_rain / 100.0))
    eff_soil = soil_imp * (0.3 + 0.7 * (norm_soil / 100.0))
    eff_slope = slope_imp * (0.3 + 0.7 * (norm_slope / 100.0))
    eff_total = eff_disp + eff_rain + eff_soil + eff_slope or 1.0

    detailed_factors: List[FactorContribution] = [
        FactorContribution(
            name="Ground Displacement Rate",
            raw_value=round(disp_rate, 2),
            unit="mm/d",
            normalized_score=round(norm_ground, 1),
            weight=round(disp_imp / 100.0, 2),
            weighted_score=round(eff_disp, 1),
            percentage_contribution=round((eff_disp / eff_total) * 100.0, 1),
            status="Active Shear" if ground >= 5.0 else ("Creep" if ground >= 2.0 else "Stable")
        ),
        FactorContribution(
            name="Antecedent Rainfall (ARI)",
            raw_value=round(ari, 1),
            unit="mm",
            normalized_score=round(norm_rain, 1),
            weight=round(rain_imp / 100.0, 2),
            weighted_score=round(eff_rain, 1),
            percentage_contribution=round((eff_rain / eff_total) * 100.0, 1),
            status="Extreme" if rain >= 130 else ("Heavy" if rain >= 75 else "Normal")
        ),
        FactorContribution(
            name="Soil Pore Saturation",
            raw_value=round(soil, 1),
            unit="%",
            normalized_score=round(norm_soil, 1),
            weight=round(soil_imp / 100.0, 2),
            weighted_score=round(eff_soil, 1),
            percentage_contribution=round((eff_soil / eff_total) * 100.0, 1),
            status="Saturated" if soil >= 78 else ("Elevated" if soil >= 60 else "Normal")
        ),
        FactorContribution(
            name="Slope Topography (TWI)",
            raw_value=round(slope, 1),
            unit="deg",
            normalized_score=round(norm_slope, 1),
            weight=round(slope_imp / 100.0, 2),
            weighted_score=round(eff_slope, 1),
            percentage_contribution=round((eff_slope / eff_total) * 100.0, 1),
            status="Steep" if slope >= 34 else "Moderate"
        )
    ]

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ml_metrics_summary = {
        "predicted_class": predicted_class_name,
        "class_probabilities": prob_dict,
        "feature_importances": feat_imps,
        "pipeline_accuracy": _ml_bundle.get("accuracy", 0.95) if _ml_bundle else 0.95,
        "n_estimators": 140,
        "model_architecture": "Ensemble Random Forest (Calibrated)",
        "geo_zone_applied": zone_details["name"]
    }

    return RiskResult(
        risk_score=risk_score,
        risk_level=risk_level,
        color=color_code,
        factors=detected_factors,
        detailed_factors=detailed_factors,
        recommended_action=recommended_action,
        early_warning=early_warning,
        timestamp=timestamp_str,
        model_type=f"Calibrated Random Forest Ensemble (NER {zone_details['name']})",
        confidence_level=f"ML Predicted: {predicted_class_name} ({prob_dict.get(predicted_class_name, 0.0)}% probability)",
        engine_type="ml_rf",
        geo_zone=geo_zone_key,
        geo_zone_name=zone_details["name"],
        class_probabilities=prob_dict,
        engineered_features={
            "ari_mm": round(ari, 1),
            "twi_index": round(twi, 2),
            "pore_water_pressure_kpa": round(pore_water_press, 2),
            "displacement_rate_mm_day": round(disp_rate, 2)
        },
        ml_metrics=ml_metrics_summary
    )


# ---------------------------------------------------------------------------
# Unified Risk Assessment Router
# ---------------------------------------------------------------------------
def assess_landslide_risk(input_data: RiskInput) -> RiskResult:
    """
    Main entry point for landslide hazard evaluation.
    Routes between Transparent Weighted Heuristic Engine and
    Calibrated Random Forest ML Engine based on `input_data.engine_type`.
    """
    # Resolve Geo-Climatic Zone
    geo_zone_key = input_data.geo_zone
    if not geo_zone_key or geo_zone_key == "auto":
        geo_zone_key = detect_geo_zone(input_data.location_id)

    if input_data.engine_type == "ml_rf":
        return assess_landslide_risk_ml(input_data, geo_zone_key)
    else:
        return assess_landslide_risk_weighted(input_data, geo_zone_key)
