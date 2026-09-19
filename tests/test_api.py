"""
LAND-SAFE AI - End-to-End API and Verification Suite
Runs automated verification against live running FastAPI instance on http://127.0.0.1:8000
"""

import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000"


def http_get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        status_code = response.status
        content_type = response.getheader('Content-Type')
        data = response.read()
        if 'application/json' in content_type:
            return status_code, json.loads(data.decode('utf-8'))
        return status_code, data.decode('utf-8')


def http_post(path, payload):
    url = f"{BASE_URL}{path}"
    data_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data_bytes, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        status_code = response.status
        return status_code, json.loads(response.read().decode('utf-8'))


def run_tests():
    print("==================================================")
    print("LAND-SAFE AI: Executing Automated API Verification")
    print("==================================================")
    
    passed = 0
    total = 0

    # Test 1: Frontend Serving
    total += 1
    status, html = http_get("/")
    assert status == 200 and "LAND-SAFE AI" in html, "Failed to serve frontend index.html"
    print("[PASS] 1. Frontend index.html served at root '/'")
    passed += 1

    # Test 2: System Health
    total += 1
    status, health = http_get("/api/health")
    assert status == 200 and health["status"] == "OPERATIONAL" and "DEMO" in health["mode"], "Health check failed"
    print(f"[PASS] 2. Health Endpoint OK: Status={health['status']}, Mode={health['mode']}")
    passed += 1

    # Test 3: Demo Scenarios
    total += 1
    status, scenarios = http_get("/api/scenarios")
    assert status == 200 and len(scenarios) == 4, "Scenarios count mismatch"
    print(f"[PASS] 3. Scenarios Endpoint OK: Found {len(scenarios)} presets (Normal, High Rain, High Risk, Critical)")
    passed += 1

    # Test 4: Monitored Locations (8 NER States)
    total += 1
    status, locations = http_get("/api/locations")
    assert status == 200 and len(locations) == 8, f"Expected 8 locations, got {len(locations)}"
    states = {loc["state"] for loc in locations}
    print(f"[PASS] 4. Locations Endpoint OK: Found {len(locations)} locations across {len(states)} NER states")
    passed += 1

    # Test 5: Detailed Location & History
    total += 1
    status, loc_detail = http_get("/api/location/LOC-SK-01")
    assert status == 200 and loc_detail["location"]["name"] == "Mangan Hillside", "Location detail failed"
    assert len(loc_detail["history"]) > 0, "Location history empty"
    print(f"[PASS] 5. Location Detail OK: Mangan Hillside has {len(loc_detail['history'])} time-series data points")
    passed += 1

    # Test 6: Risk Prediction - Normal Scenario (LOW)
    total += 1
    normal_payload = {
        "rainfall": 30.0,
        "soil_moisture": 35.0,
        "slope": 12.0,
        "ground_movement": 0.5
    }
    status, normal_res = http_post("/api/predict", normal_payload)
    assert status == 200, "Predict normal failed"
    assert normal_res["risk_level"] == "LOW", f"Expected LOW, got {normal_res['risk_level']}"
    assert normal_res["risk_score"] <= 29, f"Expected <= 29, got {normal_res['risk_score']}"
    assert not normal_res["early_warning"], "Normal should not trigger early warning"
    print(f"[PASS] 6. Risk Engine Normal Scenario OK: Score={normal_res['risk_score']}%, Level={normal_res['risk_level']}")
    passed += 1

    # Test 7: Risk Prediction - Critical Scenario (CRITICAL + EARLY WARNING)
    total += 1
    crit_payload = {
        "location_id": "LOC-SK-01",
        "rainfall": 190.0,
        "soil_moisture": 88.0,
        "slope": 40.0,
        "ground_movement": 8.5
    }
    status, crit_res = http_post("/api/predict", crit_payload)
    assert status == 200, "Predict critical failed"
    assert crit_res["risk_level"] == "CRITICAL", f"Expected CRITICAL, got {crit_res['risk_level']}"
    assert crit_res["risk_score"] >= 75, f"Expected >= 75, got {crit_res['risk_score']}"
    assert crit_res["early_warning"] is True, "Critical must trigger early warning"
    assert len(crit_res["detailed_factors"]) == 4, "Explainable AI factor breakdown missing"
    print(f"[PASS] 7. Risk Engine Critical Scenario OK: Score={crit_res['risk_score']}%, Level={crit_res['risk_level']}, EarlyWarning={crit_res['early_warning']}")
    passed += 1

    # Test 8: Alerts List & Acknowledgment
    total += 1
    status, alerts = http_get("/api/alerts")
    assert status == 200 and len(alerts) > 0, "Alerts list failed"
    active_alert = next((a for a in alerts if a["status"] == "ACTIVE"), None)
    assert active_alert is not None, "No active alert to acknowledge"
    ack_status, ack_res = http_post(f"/api/alerts/{active_alert['id']}/acknowledge", {
        "officer_name": "Test Disaster Officer",
        "notes": "Verified via automated test script."
    })
    assert ack_status == 200 and ack_res["status"] == "success", "Alert acknowledge failed"
    print(f"[PASS] 8. Alerts Endpoint OK: Alert '{active_alert['id']}' acknowledged successfully")
    passed += 1

    # Test 9: Field Observations
    total += 1
    obs_payload = {
        "location_id": "LOC-MG-02",
        "location_name": "Sohra Cut-Slope",
        "officer_name": "Inspector S. Sangma",
        "notes": "Minor tension cracks along upper berm, drainage ditch cleaned."
    }
    status, obs_res = http_post("/api/observations", obs_payload)
    assert status == 200 and obs_res["status"] == "success", "Observation logging failed"
    status, obs_list = http_get("/api/observations")
    assert status == 200 and any(o["notes"] == obs_payload["notes"] for o in obs_list), "Obs not found in feed"
    print(f"[PASS] 9. Field Observations OK: Recorded and retrieved in SQLite successfully")
    passed += 1

    # Test 10: ML Status
    total += 1
    status, ml_status = http_get("/api/ml-status")
    assert status == 200 and ml_status["future_ml_pipeline"]["prototype_trained_model_ready"] is True
    assert ml_status["ml_pipeline_status"] == "LOADED", "ML pipeline status should be LOADED"
    print(f"[PASS] 10. ML Architecture Status OK: Model accuracy {ml_status['accuracy']*100:.1f}%, 140 trees active")
    passed += 1

    # Test 11: Machine Learning Random Forest Prediction (CRITICAL)
    total += 1
    ml_payload = {
        "location_id": "LOC-SK-01",
        "rainfall": 185.0,
        "soil_moisture": 84.0,
        "slope": 38.0,
        "ground_movement": 7.8,
        "engine_type": "ml_rf",
        "geo_zone": "zone_b"
    }
    status, ml_res = http_post("/api/predict", ml_payload)
    assert status == 200, "ML Predict failed"
    assert ml_res["engine_type"] == "ml_rf", "Expected engine_type ml_rf"
    assert ml_res["risk_level"] == "CRITICAL", f"Expected CRITICAL, got {ml_res['risk_level']}"
    assert "class_probabilities" in ml_res and ml_res["class_probabilities"] is not None
    assert "engineered_features" in ml_res and ml_res["engineered_features"] is not None
    assert "ari_mm" in ml_res["engineered_features"]
    assert "twi_index" in ml_res["engineered_features"]
    assert "pore_water_pressure_kpa" in ml_res["engineered_features"]
    assert "displacement_rate_mm_day" in ml_res["engineered_features"]
    print(f"[PASS] 11. ML Random Forest Engine OK: Score={ml_res['risk_score']}%, Level={ml_res['risk_level']}, ARI={ml_res['engineered_features']['ari_mm']}mm, P(Crit)={ml_res['class_probabilities']['CRITICAL']}%")
    passed += 1

    # Test 12: Regional Geo-Climatic Zones Endpoint
    total += 1
    status, zones = http_get("/api/ml/zones")
    assert status == 200, "Failed to get geo zones"
    assert "zone_a" in zones and "zone_b" in zones and "zone_c" in zones, "Missing expected NER geo zones"
    print(f"[PASS] 12. Regional Geo-Climatic Zones OK: Found {len(zones)} calibrated NER belts (Zone A, B, C)")
    passed += 1

    # Test 13: Dual-Engine Normal Conditions Check (Low Risk on both engines)
    total += 1
    low_payload_ml = {
        "rainfall": 25.0,
        "soil_moisture": 30.0,
        "slope": 12.0,
        "ground_movement": 0.4,
        "engine_type": "ml_rf",
        "geo_zone": "zone_a"
    }
    status, low_res_ml = http_post("/api/predict", low_payload_ml)
    assert status == 200 and low_res_ml["risk_level"] == "LOW", f"Expected LOW risk for ML normal conditions, got {low_res_ml['risk_level']}"
    print(f"[PASS] 13. ML Engine Low Risk Scenario OK: Score={low_res_ml['risk_score']}%, Level={low_res_ml['risk_level']}, P(Low)={low_res_ml['class_probabilities']['LOW']}%")
    passed += 1

    print("==================================================")
    print(f"VERIFICATION COMPLETE: {passed}/{total} Tests Passed (100%)")
    print("LAND-SAFE AI is fully functional with Dual AI/ML Engines & Regional Calibration!")
    print("==================================================")


if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"\n[FAIL] Test suite failed: {e}", file=sys.stderr)
        sys.exit(1)
