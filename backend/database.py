import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "land_safe.db")


def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Locations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        district TEXT NOT NULL,
        state TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        elevation REAL NOT NULL,
        slope REAL NOT NULL,
        last_rainfall REAL NOT NULL,
        last_soil_moisture REAL NOT NULL,
        last_ground_movement REAL NOT NULL,
        temperature REAL NOT NULL,
        humidity REAL NOT NULL,
        risk_score INTEGER NOT NULL,
        risk_level TEXT NOT NULL,
        data_source TEXT NOT NULL,
        last_updated TEXT NOT NULL
    )
    """)

    # 2. Environmental Readings (Time-series for Analytics)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS environmental_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        rainfall REAL NOT NULL,
        soil_moisture REAL NOT NULL,
        ground_movement REAL NOT NULL,
        risk_score INTEGER NOT NULL,
        FOREIGN KEY (location_id) REFERENCES locations(id)
    )
    """)

    # 3. Risk Predictions Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS risk_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id TEXT,
        rainfall REAL NOT NULL,
        soil_moisture REAL NOT NULL,
        slope REAL NOT NULL,
        ground_movement REAL NOT NULL,
        risk_score INTEGER NOT NULL,
        risk_level TEXT NOT NULL,
        factors_json TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)

    # 4. Alerts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id TEXT PRIMARY KEY,
        location_id TEXT NOT NULL,
        location_name TEXT NOT NULL,
        state TEXT NOT NULL,
        risk_score INTEGER NOT NULL,
        risk_level TEXT NOT NULL,
        main_factors_json TEXT NOT NULL,
        recommended_action TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        status TEXT NOT NULL,
        acknowledged_by TEXT,
        acknowledged_at TEXT
    )
    """)

    # 5. Field Observations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS field_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id TEXT NOT NULL,
        location_name TEXT NOT NULL,
        officer_name TEXT NOT NULL,
        notes TEXT NOT NULL,
        photo_data TEXT,
        timestamp TEXT NOT NULL,
        cv_status TEXT NOT NULL
    )
    """)

    conn.commit()

    # Seed data if locations are empty
    cursor.execute("SELECT COUNT(*) FROM locations")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_demonstration_data(conn)

    conn.close()


def seed_demonstration_data(conn):
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 8 Demonstration Locations covering all North Eastern states
    # Mapped with realistic geography and varied risk levels for SIH hackathon demonstration
    locations_data = [
        (
            "LOC-SK-01", "Mangan Hillside", "North Sikkim", "Sikkim",
            27.5097, 88.5287, 1310.0, 38.0, 185.0, 84.0, 7.8, 16.5, 94.0,
            83, "CRITICAL", "DEMO DATA (Simulated In-situ Sensor / GIS)", now_str
        ),
        (
            "LOC-MG-02", "Sohra Cut-Slope", "East Khasi Hills", "Meghalaya",
            25.2702, 91.7323, 1484.0, 34.0, 155.0, 78.0, 5.2, 19.0, 92.0,
            71, "HIGH", "DEMO DATA (Simulated In-situ Sensor / GIS)", now_str
        ),
        (
            "LOC-AS-03", "Haflong Valley Bypass", "Dima Hasao", "Assam",
            25.1764, 93.0238, 680.0, 31.0, 138.0, 72.0, 4.8, 24.0, 88.0,
            64, "HIGH", "DEMO DATA (Simulated In-situ Sensor / GIS)", now_str
        ),
        (
            "LOC-AR-04", "Tawang Pass Sector", "Tawang", "Arunachal Pradesh",
            27.5861, 91.8594, 3048.0, 24.0, 75.0, 52.0, 1.4, 11.0, 76.0,
            41, "MODERATE", "DEMO DATA (Simulated In-situ Sensor / GIS)", now_str
        ),
        (
            "LOC-NL-05", "Kohima Ridge North", "Kohima", "Nagaland",
            25.6751, 94.1086, 1444.0, 26.0, 82.0, 55.0, 1.8, 18.5, 78.0,
            44, "MODERATE", "DEMO DATA (Simulated In-situ Sensor / GIS)", now_str
        ),
        (
            "LOC-MN-06", "Churachandpur Highway", "Churachandpur", "Manipur",
            24.3333, 93.6667, 922.0, 28.0, 92.0, 61.0, 2.3, 22.0, 81.0,
            48, "MODERATE", "DEMO DATA (Simulated In-situ Sensor / GIS)", now_str
        ),
        (
            "LOC-MZ-07", "Aizawl North Escarpment", "Aizawl", "Mizoram",
            23.7271, 92.7176, 1132.0, 21.0, 42.0, 40.0, 0.6, 23.5, 68.0,
            26, "LOW", "DEMO DATA (Simulated In-situ Sensor / GIS)", now_str
        ),
        (
            "LOC-TR-08", "Jampui Hills Sector", "North Tripura", "Tripura",
            23.8500, 92.2667, 720.0, 16.0, 30.0, 36.0, 0.4, 26.0, 65.0,
            20, "LOW", "DEMO DATA (Simulated In-situ Sensor / GIS)", now_str
        ),
    ]

    cursor.executemany("""
    INSERT INTO locations (
        id, name, district, state, latitude, longitude, elevation, slope,
        last_rainfall, last_soil_moisture, last_ground_movement, temperature, humidity,
        risk_score, risk_level, data_source, last_updated
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, locations_data)

    # Seed Initial Alerts
    initial_alerts = [
        (
            "ALT-2026-001", "LOC-SK-01", "Mangan Hillside", "Sikkim", 83, "CRITICAL",
            json.dumps(["Torrential rainfall (185 mm)", "Saturated topsoil (84%)", "Steep 38° slope", "Active displacement (7.8 mm)"]),
            "URGENT: Deploy field assessment team to Mangan bypass. Coordinate temporary traffic restriction with Border Roads Organisation.",
            (datetime.now() - timedelta(minutes=42)).strftime("%Y-%m-%d %H:%M:%S"),
            "ACTIVE", None, None
        ),
        (
            "ALT-2026-002", "LOC-MG-02", "Sohra Cut-Slope", "Meghalaya", 71, "HIGH",
            json.dumps(["Heavy monsoon rainfall (155 mm)", "Elevated moisture (78%)", "34° road cut slope", "Measurable ground creep (5.2 mm)"]),
            "Immediate field monitoring recommended. Inspect slope toe retaining walls along Cherrapunji-Shella road corridor.",
            (datetime.now() - timedelta(hours=2, minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
            "ACTIVE", None, None
        ),
        (
            "ALT-2026-003", "LOC-AS-03", "Haflong Valley Bypass", "Assam", 64, "HIGH",
            json.dumps(["Sustained rainfall (138 mm)", "High soil moisture (72%)", "31° slope angle"]),
            "Issue advisory to Northeast Frontier Railway and district PWD. Maintain active telemetry polling.",
            (datetime.now() - timedelta(hours=4, minutes=50)).strftime("%Y-%m-%d %H:%M:%S"),
            "ACKNOWLEDGED", "District Disaster Mgmt Officer (Dima Hasao)",
            (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
        ),
    ]

    cursor.executemany("""
    INSERT INTO alerts (
        id, location_id, location_name, state, risk_score, risk_level,
        main_factors_json, recommended_action, timestamp, status, acknowledged_by, acknowledged_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, initial_alerts)

    # Seed 7-Day / 24-Hour Environmental Time-series for Analytics
    # Generate realistic trend data for each location
    now = datetime.now()
    readings = []
    
    # Base profiles for time series synthesis
    profiles = {
        "LOC-SK-01": {"rain_base": 120, "soil_base": 65, "ground_base": 4.5, "score_base": 65, "trend": 1.2},
        "LOC-MG-02": {"rain_base": 90, "soil_base": 60, "ground_base": 3.0, "score_base": 55, "trend": 1.1},
        "LOC-AS-03": {"rain_base": 80, "soil_base": 55, "ground_base": 2.5, "score_base": 50, "trend": 1.05},
        "LOC-AR-04": {"rain_base": 50, "soil_base": 45, "ground_base": 1.0, "score_base": 35, "trend": 0.95},
        "LOC-NL-05": {"rain_base": 55, "soil_base": 48, "ground_base": 1.2, "score_base": 38, "trend": 1.0},
        "LOC-MN-06": {"rain_base": 60, "soil_base": 50, "ground_base": 1.5, "score_base": 40, "trend": 1.02},
        "LOC-MZ-07": {"rain_base": 30, "soil_base": 35, "ground_base": 0.5, "score_base": 22, "trend": 0.9},
        "LOC-TR-08": {"rain_base": 25, "soil_base": 32, "ground_base": 0.3, "score_base": 18, "trend": 0.85},
    }

    # Generate 14 data points (last 7 days at 12-hour intervals)
    for loc_id, p in profiles.items():
        for i in range(14, -1, -1):
            t = now - timedelta(hours=i * 12)
            progress = (14 - i) / 14.0  # recent hours have more rain for high risk sites
            rain = max(5.0, round(p["rain_base"] * (0.4 + 0.6 * (progress ** p["trend"])), 1))
            soil = min(95.0, max(20.0, round(p["soil_base"] * (0.6 + 0.4 * progress), 1)))
            ground = max(0.1, round(p["ground_base"] * (0.3 + 0.7 * progress), 2))
            score = min(95, max(12, int(p["score_base"] * (0.5 + 0.5 * progress))))

            readings.append((
                loc_id,
                t.strftime("%Y-%m-%d %H:%M"),
                rain,
                soil,
                ground,
                score
            ))

    cursor.executemany("""
    INSERT INTO environmental_readings (
        location_id, timestamp, rainfall, soil_moisture, ground_movement, risk_score
    ) VALUES (?, ?, ?, ?, ?, ?)
    """, readings)

    # Seed Sample Field Observation
    cursor.execute("""
    INSERT INTO field_observations (
        location_id, location_name, officer_name, notes, photo_data, timestamp, cv_status
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "LOC-SK-01",
        "Mangan Hillside",
        "R. Lepcha (Sub-Divisional Disaster Officer)",
        "Inspected tension cracks on crown of slope along NH-10 bypass. Minor water seepage observed in road culvert. Retaining gabion wall showing slight outward tilt.",
        None,
        (datetime.now() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"),
        "Future AI Image Assessment Module (Simulated Observation)"
    ))

    conn.commit()


# Helper query methods
def get_all_locations() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM locations ORDER BY risk_score DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_location_by_id(loc_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM locations WHERE id = ?", (loc_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_location_risk(loc_id: str, score: int, level: str, rain: float, soil: float, ground: float):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    UPDATE locations
    SET risk_score = ?, risk_level = ?, last_rainfall = ?, last_soil_moisture = ?,
        last_ground_movement = ?, last_updated = ?
    WHERE id = ?
    """, (score, level, rain, soil, ground, now_str, loc_id))
    conn.commit()
    conn.close()


def get_alerts() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts ORDER BY CASE status WHEN 'ACTIVE' THEN 0 ELSE 1 END, timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    alerts = []
    for r in rows:
        d = dict(r)
        d["main_factors"] = json.loads(d["main_factors_json"])
        alerts.append(d)
    return alerts


def add_alert(alert_dict: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO alerts (
        id, location_id, location_name, state, risk_score, risk_level,
        main_factors_json, recommended_action, timestamp, status, acknowledged_by, acknowledged_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        alert_dict["id"],
        alert_dict["location_id"],
        alert_dict["location_name"],
        alert_dict["state"],
        alert_dict["risk_score"],
        alert_dict["risk_level"],
        json.dumps(alert_dict["main_factors"]),
        alert_dict["recommended_action"],
        alert_dict["timestamp"],
        "ACTIVE",
        None,
        None
    ))
    conn.commit()
    conn.close()


def acknowledge_alert(alert_id: str, officer_name: str, notes: Optional[str] = None) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    UPDATE alerts
    SET status = 'ACKNOWLEDGED', acknowledged_by = ?, acknowledged_at = ?
    WHERE id = ?
    """, (f"{officer_name} ({notes})" if notes else officer_name, now_str, alert_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def log_prediction(loc_id: Optional[str], rain: float, soil: float, slope: float, ground: float, score: int, level: str, factors: List[str]):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO risk_predictions (
        location_id, rainfall, soil_moisture, slope, ground_movement, risk_score, risk_level, factors_json, timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (loc_id, rain, soil, slope, ground, score, level, json.dumps(factors), now_str))
    conn.commit()
    conn.close()


def get_location_history(loc_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT timestamp, rainfall, soil_moisture, ground_movement, risk_score
    FROM environmental_readings
    WHERE location_id = ?
    ORDER BY timestamp ASC
    """, (loc_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_field_observation(loc_id: str, loc_name: str, officer: str, notes: str, photo: Optional[str]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO field_observations (
        location_id, location_name, officer_name, notes, photo_data, timestamp, cv_status
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        loc_id,
        loc_name,
        officer,
        notes,
        photo,
        now_str,
        "Future AI Image Assessment Module (Recorded for Field Log)"
    ))
    obs_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return obs_id


def get_field_observations() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM field_observations ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
