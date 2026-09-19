"""
LAND-SAFE AI — Calibrated Machine Learning Pipeline & Training Module
This module implements the end-to-end Machine Learning pipeline for landslide risk
classification across the North Eastern Region (NER) of India, incorporating:

1. Geospatial Feature Engineering:
   - Antecedent Rainfall Index (ARI)
   - Topographic Wetness Index proxy (TWI)
   - Subsurface Pore Water Pressure proxy (kPa)
   - Inclinometer Displacement Rate (mm/day)
2. Regional Geo-Climatic Calibration:
   - Zone A: Precambrian Crystalline / Shillong Plateau (Meghalaya)
   - Zone B: Young Folded Sedimentary / Eastern Himalayas (Sikkim & Arunachal)
   - Zone C: Barail & Disang Shales (Assam, Nagaland, Manipur, Mizoram, Tripura)
3. Multi-Class Random Forest Ensemble Classifier (0=LOW, 1=MODERATE, 2=HIGH, 3=CRITICAL)
4. Model Packaging with full metadata, feature importances, and regional parameters for live inference.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

# Feature column definitions
FEATURE_COLUMNS = [
    "rainfall",
    "soil_moisture",
    "slope",
    "ground_movement",
    "elevation",
    "ari",
    "twi",
    "pore_water_pressure",
    "displacement_rate",
    "zone_code"
]

CLASS_NAMES = ["LOW", "MODERATE", "HIGH", "CRITICAL"]

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


def compute_engineered_features_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute domain-specific geotechnical and hydrological indices:
    - ARI (Antecedent Rainfall Index proxy in mm)
    - TWI (Topographic Wetness Index proxy)
    - Pore Water Pressure proxy (kPa)
    - Inclinometer Displacement Rate proxy (mm/day)
    """
    df = df.copy()
    # 1. Antecedent Rainfall Index: factors in saturation amplification
    df["ari"] = df["rainfall"] * (1.0 + (df["soil_moisture"] / 100.0) * 0.4)
    
    # 2. Topographic Wetness Index proxy: ln(area / tan(slope))
    rad_slope = np.radians(np.clip(df["slope"], 2.0, 85.0))
    df["twi"] = np.log(120.0 / np.tan(rad_slope))
    
    # 3. Subsurface Pore Water Pressure proxy (kPa): u = gamma_w * h * cos^2(theta)
    df["pore_water_pressure"] = (df["soil_moisture"] / 100.0) * 9.81 * np.cos(rad_slope)**2 * 2.2
    
    # 4. Inclinometer Displacement Rate (mm/day): velocity proxy based on shear strain
    df["displacement_rate"] = df["ground_movement"] * (0.8 + (df["soil_moisture"] / 100.0) * 0.5)
    
    return df


def generate_regional_synthetic_dataset(n_samples: int = 3600, random_seed: int = 42) -> pd.DataFrame:
    """
    Generate balanced geomorphological records across all 3 NER geo-climatic zones
    and 4 landslide hazard regimes.
    """
    np.random.seed(random_seed)
    records = []
    
    samples_per_regime = n_samples // 4  # 900 per risk regime
    samples_per_zone = samples_per_regime // 3  # 300 per zone per regime
    
    for regime_idx in range(4):
        for zone_key, zone_info in GEO_ZONES.items():
            z_code = zone_info["code"]
            
            # Regime 0: Low Risk Baseline
            if regime_idx == 0:
                rain = np.random.uniform(5.0, 50.0, samples_per_zone)
                soil = np.random.uniform(15.0, 42.0, samples_per_zone)
                slope = np.random.uniform(8.0, 22.0, samples_per_zone)
                ground = np.random.uniform(0.1, 1.0, samples_per_zone)
                elev = np.random.uniform(400.0, 2800.0, samples_per_zone)
            
            # Regime 1: Moderate Advisory
            elif regime_idx == 1:
                rain = np.random.uniform(55.0, 105.0, samples_per_zone)
                soil = np.random.uniform(40.0, 62.0, samples_per_zone)
                slope = np.random.uniform(18.0, 30.0, samples_per_zone)
                ground = np.random.uniform(1.0, 2.5, samples_per_zone)
                elev = np.random.uniform(400.0, 3100.0, samples_per_zone)
            
            # Regime 2: High Early Warning
            elif regime_idx == 2:
                # Zone-specific sensitivity adjustment
                if z_code == 0:  # Zone A: rainfall dominates
                    rain = np.random.uniform(130.0, 190.0, samples_per_zone)
                    soil = np.random.uniform(70.0, 88.0, samples_per_zone)
                    slope = np.random.uniform(25.0, 38.0, samples_per_zone)
                    ground = np.random.uniform(2.5, 5.0, samples_per_zone)
                elif z_code == 1:  # Zone B: slope & displacement dominate
                    rain = np.random.uniform(100.0, 160.0, samples_per_zone)
                    soil = np.random.uniform(60.0, 78.0, samples_per_zone)
                    slope = np.random.uniform(34.0, 48.0, samples_per_zone)
                    ground = np.random.uniform(3.5, 7.0, samples_per_zone)
                else:  # Zone C: shale creep & moisture dominate
                    rain = np.random.uniform(110.0, 165.0, samples_per_zone)
                    soil = np.random.uniform(68.0, 84.0, samples_per_zone)
                    slope = np.random.uniform(26.0, 36.0, samples_per_zone)
                    ground = np.random.uniform(3.2, 6.5, samples_per_zone)
                elev = np.random.uniform(500.0, 3200.0, samples_per_zone)
            
            # Regime 3: Critical Slope Failure Imminent
            else:
                if z_code == 0:  # Zone A: extreme precipitation
                    rain = np.random.uniform(170.0, 280.0, samples_per_zone)
                    soil = np.random.uniform(82.0, 98.0, samples_per_zone)
                    slope = np.random.uniform(30.0, 46.0, samples_per_zone)
                    ground = np.random.uniform(5.5, 12.0, samples_per_zone)
                elif z_code == 1:  # Zone B: extreme slope & severe displacement
                    rain = np.random.uniform(150.0, 240.0, samples_per_zone)
                    soil = np.random.uniform(75.0, 95.0, samples_per_zone)
                    slope = np.random.uniform(38.0, 56.0, samples_per_zone)
                    ground = np.random.uniform(7.0, 16.0, samples_per_zone)
                else:  # Zone C: complete shear boundary failure
                    rain = np.random.uniform(155.0, 250.0, samples_per_zone)
                    soil = np.random.uniform(80.0, 96.0, samples_per_zone)
                    slope = np.random.uniform(32.0, 45.0, samples_per_zone)
                    ground = np.random.uniform(6.5, 14.0, samples_per_zone)
                elev = np.random.uniform(500.0, 3400.0, samples_per_zone)

            for i in range(samples_per_zone):
                records.append({
                    "rainfall": round(float(rain[i]), 1),
                    "soil_moisture": round(float(soil[i]), 1),
                    "slope": round(float(slope[i]), 1),
                    "ground_movement": round(float(ground[i]), 2),
                    "elevation": round(float(elev[i]), 0),
                    "zone_code": z_code,
                    "risk_class": regime_idx
                })

    raw_df = pd.DataFrame(records)
    # Compute engineered features
    df = compute_engineered_features_df(raw_df)
    # Shuffle dataset
    df = df.sample(frac=1.0, random_state=random_seed).reset_index(drop=True)
    return df


def train_and_export_model():
    """Train the full ensemble pipeline and serialize with inference metadata."""
    print("=================================================================")
    print("LAND-SAFE AI: Calibrated Machine Learning Pipeline Training")
    print("Regional Geo-Climatic Calibration (Zone A / Zone B / Zone C)")
    print("=================================================================")

    # Step 1: Generate dataset with engineered geotechnical features
    print("\n[1/5] Synthesizing regional NER geotechnical dataset...")
    df = generate_regional_synthetic_dataset(n_samples=3600, random_seed=42)
    print(f"      Total records: {len(df)} across 3 zones and 4 risk regimes.")
    
    X = df[FEATURE_COLUMNS]
    y = df["risk_class"]

    # Step 2: Stratified Train / Test Split
    print("\n[2/5] Creating 80/20 stratified train/test split...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"      Train set: {len(X_train)} samples | Test set: {len(X_test)} samples")

    # Step 3: Train Random Forest Pipeline
    print("\n[3/5] Fitting ensemble Random Forest Classifier (140 estimators)...")
    rf_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", RandomForestClassifier(
            n_estimators=140,
            max_depth=12,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ))
    ])

    rf_pipeline.fit(X_train, y_train)

    # Step 4: Model Evaluation
    print("\n[4/5] Evaluating model performance on out-of-sample test set...")
    y_pred = rf_pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report_dict = classification_report(y_test, y_pred, target_names=CLASS_NAMES, output_dict=True)
    report_text = classification_report(y_test, y_pred, target_names=CLASS_NAMES)
    
    print(f"\n      >>> Model Test Accuracy: {acc * 100:.2f}% <<<\n")
    print(report_text)

    # Extract feature importances
    rf_classifier = rf_pipeline.named_steps["classifier"]
    importances = rf_classifier.feature_importances_
    feature_importance_map = {
        col: round(float(imp * 100), 2) for col, imp in zip(FEATURE_COLUMNS, importances)
    }
    # Sort descending
    sorted_importances = dict(sorted(feature_importance_map.items(), key=lambda x: x[1], reverse=True))

    print("      Feature Importances (Tree MDI):")
    for feat, val in sorted_importances.items():
        print(f"        - {feat:<22}: {val:>5.2f}%")

    # Step 5: Serialize Model with Complete Operational Metadata
    print("\n[5/5] Packaging model pipeline with operational metadata...")
    model_payload = {
        "pipeline": rf_pipeline,
        "feature_columns": FEATURE_COLUMNS,
        "class_names": CLASS_NAMES,
        "accuracy": round(float(acc), 4),
        "feature_importances": sorted_importances,
        "geo_zones": GEO_ZONES,
        "classification_report": report_dict,
        "metadata": {
            "model_family": "RandomForestClassifier",
            "n_estimators": 140,
            "max_depth": 12,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "engineered_features": ["ari", "twi", "pore_water_pressure", "displacement_rate"],
            "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "region": "North Eastern Region (NER), India",
            "framework_version": "Scikit-Learn 1.8+ / Joblib"
        }
    }

    output_path = os.path.join(os.path.dirname(__file__), "landslide_rf_model.joblib")
    joblib.dump(model_payload, output_path)
    print(f"      Successfully serialized model bundle to:\n      -> {output_path}")
    print("=================================================================")
    print("Pipeline Ready for Production & SIH Live Demonstration!")
    print("=================================================================")
    return model_payload


if __name__ == "__main__":
    train_and_export_model()
