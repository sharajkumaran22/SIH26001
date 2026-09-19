# LAND-SAFE AI — Machine Learning Architecture & Methodology

## 1. Overview & Dual-Engine Architecture

**LAND-SAFE AI** features a production-ready **Dual-Engine Architecture** for Northeast India landslide risk assessment:

1. **Engine 1: Transparent Weighted Multi-Parametric Engine (Deterministic Heuristic)**
   - **Rainfall (24-72h aggregate)**: 35%
   - **Soil Moisture Saturation**: 25%
   - **Slope Gradient (Degrees)**: 20%
   - **Ground Movement (Inclinometer / Displacement)**: 20%
   - Designed for total baseline transparency, field inspector audits, and instant explainability.

2. **Engine 2: Calibrated Random Forest Machine Learning Pipeline**
   - Ensemble of 140 decision trees (`RandomForestClassifier` with `StandardScaler`).
   - Integrates domain-specific geotechnical and hydrological feature engineering.
   - Evaluates multi-class risk probabilities across `LOW`, `MODERATE`, `HIGH`, and `CRITICAL`.
   - Regional Geo-Climatic Calibration across all 8 NER states.

---

## 2. Geospatial Feature Engineering

The operational pipeline computes domain features from raw in-situ and remote sensing inputs:

| Feature Name | Symbol / Unit | Geotechnical Role & Physical Formula |
|---|---|---|
| **Antecedent Rainfall Index** | `ari` (mm) | Infiltration proxy factoring cumulative downpour and antecedent saturation: $ARI = Rain \times (1.0 + 0.4 \times \frac{SoilMoisture}{100})$ |
| **Topographic Wetness Index** | `twi` (index) | Local catchment accumulation and drainage capacity: $TWI = \ln(\frac{120}{\tan(\theta_{slope})})$ |
| **Subsurface Pore Water Pressure** | `pore_water_pressure` (kPa) | Buoyant pore pressure reducing effective normal stress: $u = \frac{SoilMoisture}{100} \times \gamma_w \times \cos^2(\theta) \times 2.2$ |
| **Inclinometer Displacement Rate** | `displacement_rate` (mm/day) | Shear strain velocity precursor: $v = GroundMovement \times (0.8 + 0.5 \times \frac{SoilMoisture}{100})$ |
| **Regional Zone Encoding** | `zone_code` (0, 1, 2) | Geotectonic regime indicator (Zone A, Zone B, Zone C) |

---

## 3. Regional Geo-Climatic Calibration Belts

Northeast India is subdivided into 3 distinct geological zones with localized failure mechanisms:

### Zone A: Precambrian Crystalline / Shillong Plateau (Meghalaya)
- **Monitored Locations**: Sohra Cut-Slope (East Khasi Hills, Meghalaya)
- **Lithology**: Khasi Sandstone & Precambrian crystalline basement
- **Failure Mode**: High rainfall sensitivity; torrential downpours rapidly oversaturate shallow regolith overlying bedrock, triggering translational debris slides.
- **Dominant Trigger**: Antecedent Rainfall Index ($ARI > 130$ mm).

### Zone B: Young Folded Sedimentary / Eastern Himalayas (Sikkim & Arunachal)
- **Monitored Locations**: Mangan Hillside (North Sikkim), Tawang Pass Sector (Arunachal Pradesh)
- **Lithology**: Tectonic thrust belts, schists, gneisses, and glacial till
- **Failure Mode**: Extreme slope angles ($> 34^\circ$), high gravitational shear strain, rockfalls, and rapid debris flows.
- **Dominant Trigger**: Slope Gradient & Inclinometer Displacement Rate.

### Zone C: Barail & Disang Shales (Assam, Nagaland, Manipur, Mizoram, Tripura)
- **Monitored Locations**: Haflong Valley Bypass (Assam), Kohima Ridge North (Nagaland), Churachandpur Highway (Manipur), Aizawl North (Mizoram), Jampui Hills (Tripura)
- **Lithology**: Tertiary folded fissile shales, siltstones, and claystones
- **Failure Mode**: Sustained monsoon infiltration causing deep rotational slumps, road embankment subsidence, and creeping slope failures.
- **Dominant Trigger**: Sustained Soil Pore Saturation & Continuous Slope Creep.

---

## 4. Pipeline Execution & Training

To re-train or calibrate the ensemble pipeline:

```bash
python ml/train_prototype_ml.py
```

This script:
1. Synthesizes 3,600 balanced regional geotechnical records across all 3 NER zones and 4 risk regimes.
2. Computes the engineered indices ($ARI$, $TWI$, pore pressure, displacement rate).
3. Performs a stratified 80/20 train/test split.
4. Trains an ensemble `RandomForestClassifier` with 140 estimators and standard scaling.
5. Computes Tree Mean Decrease in Impurity (MDI) feature importances.
6. Serializes the pipeline bundle and metadata to `ml/landslide_rf_model.joblib`.

---

## 5. Live REST API Integration

| Endpoint | Method | Description |
|---|---|---|
| `/api/predict` | `POST` | Accepts `engine_type` (`"weighted"` or `"ml_rf"`) and `geo_zone` (`"auto"`, `"zone_a"`, `"zone_b"`, `"zone_c"`). Returns score, class probabilities, and XAI contributions. |
| `/api/ml-status` | `GET` | Returns live model status, pipeline accuracy, tree count, feature importance rankings, and regional zones. |
| `/api/ml/zones` | `GET` | Retrieves full geotechnical metadata for Zone A, Zone B, and Zone C. |
