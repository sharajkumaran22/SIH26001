# LAND-SAFE AI
### AI-Based Early Warning & Landslide Risk Monitoring System for the North Eastern Region (NER)
**Smart India Hackathon (SIH) Round 2 Demonstration Prototype**

> *"Turning multi-source environmental signals into location-specific landslide risk intelligence."*

---

## 1. Problem Statement & Regional Context
The North Eastern Region (NER) of India—comprising Sikkim, Meghalaya, Assam, Arunachal Pradesh, Nagaland, Manipur, Mizoram, and Tripura—experiences frequent and devastating landslides triggered by intense monsoon precipitation, steep Himalayan slopes, active tectonic faulting, and soil saturation.

Traditional warning mechanisms rely almost entirely on broad, regional rainfall advisories that lack granular slope dynamics and geotechnical context. **LAND-SAFE AI** is a decision-support platform designed for state and district disaster management authorities that integrates multi-parametric environmental and geotechnical inputs:
1. **Antecedent & Ingestion Rainfall (mm)**
2. **Soil Moisture Saturation (%)**
3. **Terrain Slope Gradient (Degrees)**
4. **Borehole Ground Displacement / Shear Creep (mm)**
5. **Elevation, Temperature, and Humidity Context**

---

## 2. Technical Architecture

```
[ENVIRONMENTAL SOURCES]
Rainfall (IMD Radar) • Soil Moisture (IoT) • Slope (DEM) • Displacement (Inclinometer)
                           ↓
              [DATA COLLECTION & SANITIZATION]
         FastAPI + Pydantic v2 Type & Range Validation
                           ↓
                   [FEATURE ENGINEERING]
        Normalized Geomorphological Failure Indices
                           ↓
                [AI/ML RISK INFERENCE ENGINE]
      Prototype Transparent Model (35 / 25 / 20 / 20 %)
                 + Scikit-Learn RF Classifier
                           ↓
          ┌────────────────┴────────────────┐
          ↓                                 ↓
[EXPLAINABLE AI BREAKDOWN]         [GIS RISK MAP (LEAFLET)]
  - Parametric Contribution %       - Color-Coded Markers
  - Detected Trigger Factors        - Spatial Clusters
  - Recommended Actions             - Station Popups
          └────────────────┬────────────────┘
                           ↓
                 [EARLY WARNING ENGINE]
            Alert Center + Officer Acknowledgment
                           ↓
             [DISASTER COMMAND DASHBOARD]
```

### Technology Stack:
- **Frontend**: Vanilla ES6+ JavaScript, Semantic HTML5, CSS3 Custom Properties (zero compilation overhead, ultra-fast field loading).
- **Mapping (GIS)**: Leaflet.js with OpenStreetMap high-contrast dark tiles and custom SVG pulsing pins.
- **Charts / Analytics**: Chart.js for 24-hour and 7-day multi-series environmental trajectories.
- **Backend**: Python 3.14+ FastAPI + Uvicorn ASGI server.
- **Database**: SQLite prototype (`backend/land_safe.db`) with normalized tables (`locations`, `environmental_readings`, `risk_predictions`, `alerts`, `field_observations`).
- **AI/ML Pipeline**: Scikit-Learn Random Forest Classifier (`ml/train_prototype_ml.py`) with StandardScaler and Joblib serialization.

---

## 3. Data Honesty & Simulation Mode Disclosure
In strict adherence to engineering integrity:
- **DEMO DATA / SIMULATION MODE**: Real-time government weather APIs (IMD) and state-wide in-situ IoT inclinometers require restricted ministerial credentials. All values in this prototype are clearly labeled as **"DEMO DATA"** or **"SIMULATION MODE"**.
- **Transparent Risk Engine**: The system implements a normalized multi-parametric model where judges can verify the mathematical weights:
  - **Rainfall**: 35%
  - **Soil Moisture**: 25%
  - **Slope**: 20%
  - **Ground Movement**: 20%
- **Decision Support**: The application provides risk probabilities and situational decision intelligence; it does not claim to predict exact failure time.

---

## 4. Project Directory Structure

```
land-safe-ai/
│
├── frontend/
│   ├── index.html              # Command Center UI, GIS map, forms, alert modals, architecture tabs
│   ├── style.css               # Professional dark command-center theme, glowing badges, high contrast
│   └── script.js               # Leaflet map sync, Chart.js trends, scenario presets, REST client
│
├── backend/
│   ├── main.py                 # FastAPI application, static file serving, REST routes, CORS
│   ├── risk_engine.py          # Transparent weighted risk model & Explainable AI generator
│   ├── database.py             # SQLite schema, seed data for 8 NER states, query helpers
│   ├── models.py               # Pydantic schemas for inputs, outputs, alerts, and field logs
│   ├── requirements.txt        # Python package dependencies
│   └── land_safe.db            # SQLite database file (auto-generated on first launch)
│
├── data/
│   └── demo_data.csv           # Historical sample readings for all 8 NER monitoring locations
│
├── ml/
│   ├── train_prototype_ml.py   # Synthetic NER dataset generator & Random Forest training script
│   ├── landslide_rf_model.joblib # Serialized trained ML pipeline
│   └── README.md               # Detailed ML methodology and feature importance analysis
│
├── run.bat                     # Windows 1-click startup script
├── run.ps1                     # PowerShell 1-click startup script
└── README.md                   # Project documentation & presentation guide
```

---

## 5. Quick Start & Installation

### Option A: One-Click Startup (Recommended for Windows)
Double-click `run.bat` or in PowerShell execute:
```powershell
.\run.ps1
```
The script will check dependencies, launch the FastAPI server, and automatically open your default web browser to:
```
http://127.0.0.1:8000
```

### Option B: Manual Terminal Execution
1. Open terminal inside the `land-safe-ai` folder:
```bash
cd land-safe-ai
```
2. Install dependencies:
```bash
pip install -r backend/requirements.txt
```
3. (Optional) Run the ML training pipeline:
```bash
python ml/train_prototype_ml.py
```
4. Start the Unified Server:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
5. Open your browser to `http://127.0.0.1:8000`.

---

## 6. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the interactive frontend web dashboard |
| `GET` | `/api/health` | System health check and demo simulation status |
| `GET` | `/api/locations` | Retrieves all 8 monitored NER stations with current readings |
| `GET` | `/api/location/{id}` | Detailed location telemetry and 7-day historical time-series |
| `POST` | `/api/predict` | Executes the AI/ML risk calculation on environmental inputs |
| `GET` | `/api/scenarios` | Returns preset demo scenarios (Normal, High Rain, High Risk, Critical) |
| `GET` | `/api/alerts` | Lists all active and acknowledged early warnings |
| `POST` | `/api/alerts/{id}/acknowledge` | Records official officer acknowledgment of a warning |
| `POST` | `/api/observations` | Records field inspector photos and geotechnical notes |
| `GET` | `/api/observations` | Retrieves logged site observations |
| `GET` | `/api/ml-status` | Returns live model accuracy, tree count, feature rankings, and zone metadata |
| `GET` | `/api/ml/zones` | Retrieves regional geo-climatic calibration belts (Zone A, Zone B, Zone C) |

---

## 7. 3–5 Minute Live Hackathon Demonstration Flow

Here is the exact step-by-step walkthrough for your team to present before the SIH judges:

### Step 1: System Introduction (30 seconds)
1. Open `http://127.0.0.1:8000`.
2. Point out the top header:
   - System title: **LAND-SAFE AI**
   - Subtitle: **AI-Based Early Warning & Landslide Risk Monitoring System (NER)**
   - Status: **● System Operational**
   - Point to the **SIMULATION MODE** badge and explain: *"As an honest engineering prototype, we clearly identify simulated and demonstration data while building a production-ready decision-support architecture."*

### Step 2: Regional Sentinel Stations & GIS Map (45 seconds)
1. Show the **KPI Summary Cards**: 8 Areas Monitored across all 8 North Eastern states (Sikkim, Meghalaya, Assam, Arunachal Pradesh, Nagaland, Manipur, Mizoram, Tripura).
2. Point to the **GIS Risk Map** on the right:
   - Point out the color-coded markers: Green (Low), Yellow (Moderate), Orange (High), Red with pulse (Critical).
   - Click on the red marker (**Mangan Hillside, North Sikkim**). Notice the popup and how the left panel immediately loads Mangan's telemetry.

### Step 3: Risk Assessment & Dual-Engine Explainable AI (60 seconds)
1. In the left panel, point out the **Active AI/ML Risk Engine** switcher:
   - Switch between **Transparent Weighted** (35/25/20/20 physics model) and **Random Forest ML** (140-tree calibrated ensemble).
   - Point out the **Regional Geo-Climatic Calibration** selector: auto-calibrated per station (e.g. Mangan -> Zone B: Eastern Himalayas, Sohra -> Zone A: Shillong Plateau).
2. Point out the primary parameters:
   - Rainfall: 185 mm &bull; Soil Moisture: 84% &bull; Slope: 38° &bull; Ground Movement: 7.8 mm
3. Click the prominent **"ANALYZE RISK"** button:
   - Watch the backend compute the risk score (e.g. 92% - CRITICAL under ML mode).
   - Show the **ML Ensemble Class Probabilities**: LOW 0%, MODERATE 0%, HIGH 0%, CRITICAL 100%.
   - Show the engineered feature chips: ARI (247.2 mm), TWI (5.03), Pore Water Pressure (11.26 kPa), Displacement Rate (9.52 mm/d).
   - Show the **"WHY IS THIS AREA AT RISK?"** factor contribution bars with Tree Importance shares.
   - Show the detected factors checklist with physical interpretations and regional geology tag.
   - Show the **Operational Decision-Support Recommendation**: *"Dispatch rapid verification units, prep traffic diversions, notify SDRF/NDRF teams."*

### Step 4: Demo Scenario Simulator (45 seconds)
1. Click the **"NORMAL CONDITIONS"** scenario button:
   - The parameters instantly drop (Rain: 30mm, Soil: 35%, Slope: 12°, Ground: 0.5mm).
   - The risk engine recalculates: Risk drops to **LOW (20%)**, color changes to green, early warning banner automatically dismisses.
2. Click the **"HIGH LANDSLIDE RISK"** scenario:
   - Parameters update (Rain: 150mm, Soil: 75%, Slope: 32°, Ground: 5.5mm).
   - The score climbs to **HIGH (69%)**.
   - Notice the flashing red/amber **Early Warning Banner** slides down at the top: *"HIGH EARLY WARNING DISPATCHED"*.

### Step 5: Alert Center & Officer Workflow (30 seconds)
1. Switch to the **Alert Center** tab.
2. Show active alerts: notice the newly generated early warning for the monitored site.
3. Click **"Acknowledge Alert"**:
   - The alert changes status to **ACKNOWLEDGED** with the officer's title and timestamp recorded in the SQLite database.

### Step 6: Analytics & Field Photo Log (30 seconds)
1. Switch to the **Analytics & Trends** tab:
   - Show the 4 synchronized Chart.js graphs (Rainfall accumulation, Soil Moisture saturation, Ground displacement, and Composite Risk Trajectory). Toggle between 24 Hours and 7 Days.
2. Switch to **Field Observations**:
   - Upload a site image, show instant thumbnail preview, enter inspection notes, and submit.
   - Show the observation logged into the SQLite feed with the honest disclaimer: *"Future AI Image Assessment Module"*.

### Step 7: Architecture & Conclusion (30 seconds)
1. Switch to the **System Architecture** tab:
   - Walk through the 6-stage pipeline: Data Sources → Ingestion → AI Risk Engine → Explainable AI → GIS Map → Early Warning.
   - Show the Data Source Honesty Matrix (Rainfall: Demo, Ground Movement: Simulated IoT, Satellite: Future integration).
2. Conclude with:
   > *"LAND-SAFE AI turns multi-source environmental signals into location-specific, explainable landslide risk intelligence for disaster management officers across the North Eastern Region."*

---

## 8. SIH Hackathon Evaluation Highlights
- **Decision-Support Focus**: Specifically designed for district officers, avoiding unrealistic claims of exact failure timing.
- **Granular Geospatial Intelligence**: Goes beyond simple rain gauges by factoring in soil moisture, slope angle, and shear displacement.
- **Explainable AI (XAI)**: High-transparency factor contributions prevent black-box decision making.
- **Demonstration Reliability**: Includes 1-click scenario simulation presets and resilient client-side fallback to guarantee zero demo failures.
