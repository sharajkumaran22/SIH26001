/**
 * LAND-SAFE AI — Command Center Frontend Logic
 * SIH Prototype: AI-Based Early Warning & Landslide Risk Monitoring System
 * Handles Leaflet GIS, REST API integration, Explainable AI rendering,
 * Scenario simulations, Chart.js analytics, and early warning dispatch.
 */

// Global State
const state = {
  locations: [],
  selectedLocation: null,
  activeAlerts: [],
  observations: [],
  charts: {},
  analyticsTimeframe: '24h',
  gisMap: null,
  fullGisMap: null,
  mapMarkers: {},
  fullMapMarkers: {},
  engineType: 'weighted',
  geoZone: 'auto',
  mlStatus: null
};

// API Base URL
const API_BASE = '/api';

// ====================================================
// INITIALIZATION ON DOM LOAD
// ====================================================
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initClock();
  initNavigationTabs();
  initEngineControls();
  initTelemetryControls();
  initScenarioButtons();
  initGisMap();
  initFormSubmissions();
  initPhotoUpload();
  initAlertFilters();

  // Load backend data
  loadLocations();
  loadAlerts();
  loadObservations();
  loadMlArchitectureStatus();
});

// ====================================================
// 0. THEME SWITCHER (LIGHT / DARK)
// ====================================================
function initTheme() {
  const toggleBtn = document.getElementById('btnThemeToggle');
  const toggleIcon = document.getElementById('themeToggleIcon');
  const toggleText = document.getElementById('themeToggleText');

  // Default to light theme as requested
  const savedTheme = localStorage.getItem('landsafe_theme') || 'light';
  applyTheme(savedTheme);

  toggleBtn?.addEventListener('click', () => {
    const isLight = document.body.classList.contains('light-theme');
    const newTheme = isLight ? 'dark' : 'light';
    applyTheme(newTheme);
    localStorage.setItem('landsafe_theme', newTheme);
    showToast(`Switched to ${newTheme.toUpperCase()} Mode`, 'info');
  });

  function applyTheme(theme) {
    if (theme === 'dark') {
      document.body.classList.remove('light-theme');
      document.body.classList.add('dark-theme');
      if (toggleIcon) toggleIcon.innerHTML = '&#127769;';
      if (toggleText) toggleText.textContent = 'Dark';
    } else {
      document.body.classList.remove('dark-theme');
      document.body.classList.add('light-theme');
      if (toggleIcon) toggleIcon.innerHTML = '&#9728;&#65039;';
      if (toggleText) toggleText.textContent = 'Light';
    }

    // Refresh charts if rendered
    if (document.getElementById('tab-analytics')?.classList.contains('active')) {
      renderAnalyticsCharts();
    }
  }
}

// ====================================================
// 1. CLOCK & NAVIGATION
// ====================================================
function initClock() {
  const clockEl = document.getElementById('clockDisplay');
  const updateClock = () => {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString('en-IN', { hour12: false }) + ' IST';
  };
  updateClock();
  setInterval(updateClock, 1000);
}

function initNavigationTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const targetId = tab.getAttribute('data-tab');
      document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add('active');
        
        // Invalidate Leaflet map size on tab switch
        if (targetId === 'tab-dashboard' && state.gisMap) {
          setTimeout(() => state.gisMap.invalidateSize(), 200);
        } else if (targetId === 'tab-map') {
          if (!state.fullGisMap) {
            initFullGisMap();
          } else {
            setTimeout(() => state.fullGisMap.invalidateSize(), 200);
          }
        } else if (targetId === 'tab-analytics') {
          renderAnalyticsCharts();
        }
      }
    });
  });

  // Banner view alert shortcut
  document.getElementById('btnBannerViewAlert')?.addEventListener('click', () => {
    const alertTab = document.querySelector('[data-tab="tab-alerts"]');
    if (alertTab) alertTab.click();
  });

  document.getElementById('btnBannerDismiss')?.addEventListener('click', () => {
    document.getElementById('earlyWarningBanner').classList.add('hidden');
  });
}

// ====================================================
// 2. TELEMETRY CONTROLS SYNCHRONIZATION
// ====================================================
function initTelemetryControls() {
  syncSliderAndInput('sliderRain', 'inputRain', 'valDisplayRain', ' mm');
  syncSliderAndInput('sliderSoil', 'inputSoil', 'valDisplaySoil', ' %');
  syncSliderAndInput('sliderSlope', 'inputSlope', 'valDisplaySlope', ' °');
  syncSliderAndInput('sliderGround', 'inputGround', 'valDisplayGround', ' mm');

  // Location selector change
  const locSelect = document.getElementById('locationSelector');
  locSelect.addEventListener('change', (e) => {
    const locId = e.target.value;
    if (locId) {
      const loc = state.locations.find(l => l.id === locId);
      if (loc) {
        selectLocation(loc, false);
      }
    } else {
      state.selectedLocation = null;
      document.getElementById('activeDataSourceTag').textContent = 'CUSTOM / AD-HOC';
    }
  });

  // Analyze Risk Button
  document.getElementById('btnAnalyzeRisk').addEventListener('click', () => {
    executeRiskAnalysis();
  });
}

function syncSliderAndInput(sliderId, inputId, displayId, unit) {
  const slider = document.getElementById(sliderId);
  const input = document.getElementById(inputId);
  const display = document.getElementById(displayId);

  slider.addEventListener('input', () => {
    input.value = slider.value;
    display.textContent = parseFloat(slider.value).toFixed(slider.step.includes('.') ? 1 : 0);
  });

  input.addEventListener('input', () => {
    slider.value = input.value;
    display.textContent = parseFloat(input.value || 0).toFixed(slider.step.includes('.') ? 1 : 0);
  });
}

function setTelemetryValues(rain, soil, slope, ground) {
  document.getElementById('sliderRain').value = rain;
  document.getElementById('inputRain').value = rain;
  document.getElementById('valDisplayRain').textContent = rain.toFixed(1);

  document.getElementById('sliderSoil').value = soil;
  document.getElementById('inputSoil').value = soil;
  document.getElementById('valDisplaySoil').textContent = soil.toFixed(1);

  document.getElementById('sliderSlope').value = slope;
  document.getElementById('inputSlope').value = slope;
  document.getElementById('valDisplaySlope').textContent = slope.toFixed(1);

  document.getElementById('sliderGround').value = ground;
  document.getElementById('inputGround').value = ground;
  document.getElementById('valDisplayGround').textContent = ground.toFixed(1);
}

// ====================================================
// 3. DEMO SCENARIO SIMULATOR (P0 SIH REQUIREMENT)
// ====================================================
function initScenarioButtons() {
  document.getElementById('btnScenarioNormal').addEventListener('click', () => {
    setTelemetryValues(30.0, 35.0, 12.0, 0.5);
    showToast('Applied Scenario: NORMAL CONDITIONS (Low Baseline)', 'info');
    executeRiskAnalysis();
  });

  document.getElementById('btnScenarioHighRain').addEventListener('click', () => {
    setTelemetryValues(140.0, 52.0, 18.0, 1.2);
    showToast('Applied Scenario: HIGH RAINFALL (Advisory Level)', 'info');
    executeRiskAnalysis();
  });

  document.getElementById('btnScenarioHighRisk').addEventListener('click', () => {
    setTelemetryValues(150.0, 75.0, 32.0, 5.5);
    showToast('Applied Scenario: HIGH LANDSLIDE RISK (Early Warning Trigger)', 'info');
    executeRiskAnalysis();
  });

  document.getElementById('btnScenarioCritical').addEventListener('click', () => {
    setTelemetryValues(190.0, 88.0, 40.0, 8.5);
    showToast('Applied Scenario: CRITICAL CONDITIONS (Urgent Hazard)', 'info');
    executeRiskAnalysis();
  });
}

// ====================================================
// 4. REST API DATA FETCHING & LOCATIONS
// ====================================================
async function loadLocations() {
  try {
    const res = await fetch(`${API_BASE}/locations`);
    if (!res.ok) throw new Error('Failed to load locations');
    const data = await res.json();
    state.locations = data;

    populateLocationDropdowns(data);
    updateKpiStats(data);
    renderGisMarkers(data);

    // Select the first high-risk location by default (Mangan Hillside)
    if (data.length > 0) {
      selectLocation(data[0], true);
    }
  } catch (err) {
    console.error('Error fetching locations:', err);
    showToast('Using local offline backup data (Backend connecting...)', 'error');
  }
}

function populateLocationDropdowns(locations) {
  const mainSelect = document.getElementById('locationSelector');
  const analyticsSelect = document.getElementById('analyticsLocationSelect');
  const obsSelect = document.getElementById('obsLocationSelect');

  // Clear options except first
  mainSelect.innerHTML = '<option value="">-- Custom Field Coordinates / Ad-hoc Assessment --</option>';
  analyticsSelect.innerHTML = '';
  obsSelect.innerHTML = '';

  locations.forEach(loc => {
    const optMain = document.createElement('option');
    optMain.value = loc.id;
    optMain.textContent = `${loc.name} (${loc.state}) — [${loc.risk_level}]`;
    mainSelect.appendChild(optMain);

    const optAnalytics = document.createElement('option');
    optAnalytics.value = loc.id;
    optAnalytics.textContent = `${loc.name}, ${loc.state}`;
    analyticsSelect.appendChild(optAnalytics);

    const optObs = document.createElement('option');
    optObs.value = loc.id;
    optObs.textContent = `${loc.name} (${loc.state})`;
    obsSelect.appendChild(optObs);
  });

  analyticsSelect.addEventListener('change', () => {
    renderAnalyticsCharts();
  });
}

function selectLocation(loc, runPrediction = false) {
  state.selectedLocation = loc;
  document.getElementById('locationSelector').value = loc.id;
  document.getElementById('activeDataSourceTag').textContent = loc.data_source || 'DEMO DATA';

  // Set telemetry values
  setTelemetryValues(
    loc.last_rainfall,
    loc.last_soil_moisture,
    loc.slope,
    loc.last_ground_movement
  );

  // Aux readouts
  document.getElementById('valDisplayElev').textContent = `${loc.elevation.toLocaleString()} m`;
  document.getElementById('valDisplayTemp').textContent = `${loc.temperature} °C`;
  document.getElementById('valDisplayHum').textContent = `${loc.humidity} %`;

  // Auto-detect Geo-Climatic Zone
  autoDetectZoneForCurrentLocation();

  // Update map detail card
  updateMapDetailCard(loc);

  // Focus map on this location
  if (state.gisMap) {
    state.gisMap.setView([loc.latitude, loc.longitude], 9, { animate: true });
    if (state.mapMarkers[loc.id]) {
      state.mapMarkers[loc.id].openPopup();
    }
  }

  if (runPrediction) {
    executeRiskAnalysis();
  }
}

function updateMapDetailCard(loc) {
  document.getElementById('selectedLocName').textContent = loc.name;
  document.getElementById('selectedLocState').textContent = `${loc.district} • ${loc.state}`;
  
  const badge = document.getElementById('selectedLocBadge');
  badge.textContent = `${loc.risk_level} (${loc.risk_score}%)`;
  badge.className = `risk-badge ${getBadgeClass(loc.risk_level)}`;

  document.getElementById('mapMetricRain').textContent = `${loc.last_rainfall} mm`;
  document.getElementById('mapMetricSoil').textContent = `${loc.last_soil_moisture}%`;
  document.getElementById('mapMetricSlope').textContent = `${loc.slope}°`;
  document.getElementById('mapMetricGround').textContent = `${loc.last_ground_movement} mm`;
}

function updateKpiStats(locations) {
  document.getElementById('kpiMonitoredCount').textContent = locations.length;

  const critical = locations.filter(l => l.risk_level === 'CRITICAL').length;
  const high = locations.filter(l => l.risk_level === 'HIGH').length;

  document.getElementById('kpiCriticalCount').textContent = critical;
  document.getElementById('kpiHighCount').textContent = high;
}

// ====================================================
// 4B. DUAL ENGINE CONTROLS & GEO-ZONE CALIBRATION
// ====================================================
function initEngineControls() {
  const btnWeighted = document.getElementById('btnEngineWeighted');
  const btnMl = document.getElementById('btnEngineMl');
  const statusBadge = document.getElementById('engineStatusBadge');
  const zoneSelect = document.getElementById('geoZoneSelector');

  btnWeighted?.addEventListener('click', () => {
    btnWeighted.classList.add('active');
    btnMl?.classList.remove('active');
    state.engineType = 'weighted';
    if (statusBadge) {
      statusBadge.textContent = 'Heuristic Active';
      statusBadge.style.color = '#F59E0B';
    }
    showToast('Engine: Transparent Weighted Physics (35/25/20/20)', 'info');
    executeRiskAnalysis();
  });

  btnMl?.addEventListener('click', () => {
    btnMl.classList.add('active');
    btnWeighted?.classList.remove('active');
    state.engineType = 'ml_rf';
    if (statusBadge) {
      statusBadge.textContent = 'Random Forest Active';
      statusBadge.style.color = '#06B6D4';
    }
    showToast('Engine: Calibrated Random Forest ML Pipeline', 'success');
    executeRiskAnalysis();
  });

  zoneSelect?.addEventListener('change', (e) => {
    state.geoZone = e.target.value;
    updateZoneHint(state.geoZone);
    executeRiskAnalysis();
  });
}

function updateZoneHint(zoneKey) {
  const zoneHint = document.getElementById('zoneDescriptionHint');
  const autoBadge = document.getElementById('zoneAutoBadge');
  if (!zoneHint) return;

  if (zoneKey === 'zone_a') {
    zoneHint.textContent = 'Zone A: Shillong Plateau — High rainfall sensitivity, shallow regolith sliding over crystalline bedrock.';
    if (autoBadge) autoBadge.textContent = 'Manual: Zone A';
  } else if (zoneKey === 'zone_b') {
    zoneHint.textContent = 'Zone B: Eastern Himalayas — Extreme steep slope angles, kinematic shear strain, and debris flows.';
    if (autoBadge) autoBadge.textContent = 'Manual: Zone B';
  } else if (zoneKey === 'zone_c') {
    zoneHint.textContent = 'Zone C: Barail & Disang Shales — Highly weathered fissile shales prone to rotational mudslides and creep.';
    if (autoBadge) autoBadge.textContent = 'Manual: Zone C';
  } else {
    autoDetectZoneForCurrentLocation();
  }
}

function autoDetectZoneForCurrentLocation() {
  const autoBadge = document.getElementById('zoneAutoBadge');
  const zoneHint = document.getElementById('zoneDescriptionHint');
  if (!state.selectedLocation) {
    if (autoBadge && state.geoZone === 'auto') autoBadge.textContent = 'Auto: Zone B (Eastern Himalayas)';
    if (zoneHint && state.geoZone === 'auto') zoneHint.textContent = 'Calibrated for Eastern Himalayan steep terrain with high gravitational shear strain.';
    return 'zone_b';
  }

  const loc = state.selectedLocation;
  const stateStr = (loc.state || '').toLowerCase();
  let detected = 'zone_b';
  let label = 'Auto: Zone B (Eastern Himalayas)';
  let desc = 'Zone B: Eastern Himalayas — Extreme steep slope angles, kinematic shear strain, and debris flows.';

  if (stateStr.includes('meghalaya') || (loc.id && loc.id.includes('LOC-MG'))) {
    detected = 'zone_a';
    label = 'Auto: Zone A (Shillong Plateau)';
    desc = 'Zone A: Shillong Plateau — High rainfall sensitivity, shallow regolith sliding over crystalline bedrock.';
  } else if (stateStr.includes('sikkim') || stateStr.includes('arunachal') || (loc.id && (loc.id.includes('LOC-SK') || loc.id.includes('LOC-AR')))) {
    detected = 'zone_b';
    label = 'Auto: Zone B (Eastern Himalayas)';
    desc = 'Zone B: Eastern Himalayas — Extreme steep slope angles, kinematic shear strain, and debris flows.';
  } else {
    detected = 'zone_c';
    label = 'Auto: Zone C (Barail Shales)';
    desc = 'Zone C: Barail & Disang Shales — Highly weathered fissile shales prone to rotational mudslides and creep.';
  }

  if (autoBadge && state.geoZone === 'auto') autoBadge.textContent = label;
  if (zoneHint && state.geoZone === 'auto') zoneHint.textContent = desc;
  return detected;
}

// ====================================================
// 5. RISK ENGINE PREDICTION & EXPLAINABLE AI
// ====================================================
async function executeRiskAnalysis() {
  const rain = parseFloat(document.getElementById('inputRain').value);
  const soil = parseFloat(document.getElementById('inputSoil').value);
  const slope = parseFloat(document.getElementById('inputSlope').value);
  const ground = parseFloat(document.getElementById('inputGround').value);
  const locId = document.getElementById('locationSelector').value || null;

  const payload = {
    location_id: locId,
    rainfall: rain,
    soil_moisture: soil,
    slope: slope,
    ground_movement: ground,
    engine_type: state.engineType,
    geo_zone: state.geoZone
  };

  const btn = document.getElementById('btnAnalyzeRisk');
  btn.style.opacity = '0.7';

  try {
    const res = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`Risk Engine returned status: ${res.status}`);
    }

    const result = await res.json();
    displayRiskResult(result, locId);
    showToast(`Assessment Complete: ${result.risk_level} (${result.risk_score}%) [${result.engine_type === 'ml_rf' ? 'ML RF' : 'Weighted'}]`, 'success');

    // Reload alerts to reflect any new early warnings
    loadAlerts();
    
    // Update marker if attached to location
    if (locId && state.mapMarkers[locId]) {
      updateSingleMarker(locId, result.risk_score, result.risk_level);
    }
  } catch (err) {
    console.warn('Backend predict endpoint unavailable, utilizing client-side fallback calculation:', err);
    // Fallback formula ensuring zero downtime
    const fallback = calculateClientRisk(rain, soil, slope, ground);
    displayRiskResult(fallback, locId);
    showToast('Evaluated via Local Calibrated Engine', 'info');
  } finally {
    btn.style.opacity = '1';
  }
}

function displayRiskResult(result, locId) {
  // 1. Score and Badge
  const scoreVal = document.getElementById('resultScoreVal');
  const levelBadge = document.getElementById('resultLevelBadge');
  const levelText = document.getElementById('resultLevelText');
  const circle = document.getElementById('scoreCircle');

  scoreVal.textContent = result.risk_score;
  levelBadge.textContent = result.risk_level;
  levelBadge.className = `risk-badge ${getBadgeClass(result.risk_level)}`;
  levelText.textContent = `${result.risk_level} HAZARD`;
  levelText.style.color = result.color;
  circle.style.borderColor = result.color;

  // Metadata labels
  document.getElementById('resultModelTypeLabel').textContent = result.model_type || 'Decision Support Risk Engine';
  const modeEl = document.getElementById('resultAssessmentMode');
  if (modeEl) {
    modeEl.textContent = result.engine_type === 'ml_rf'
      ? 'Calibrated Random Forest Ensemble'
      : 'Multi-Factor Physics Normalization (35/25/20/20)';
  }
  const zoneLabelEl = document.getElementById('resultGeoZoneLabel');
  if (zoneLabelEl) {
    zoneLabelEl.textContent = result.geo_zone_name || 'Zone B: Eastern Himalayas';
  }
  document.getElementById('resultTimestamp').textContent = result.timestamp || new Date().toLocaleTimeString();

  // 1B. ML Probabilities & Geotechnical Features (When in ML Mode)
  const probContainer = document.getElementById('mlProbabilitiesContainer');
  if (result.engine_type === 'ml_rf' && result.class_probabilities) {
    probContainer?.classList.remove('hidden');
    const zoneTag = document.getElementById('mlZoneAppliedTag');
    if (zoneTag) zoneTag.textContent = result.geo_zone_name || 'Zone B (Eastern Himalayas)';

    const p = result.class_probabilities;
    const pLow = p.LOW || 0;
    const pMod = p.MODERATE || 0;
    const pHigh = p.HIGH || 0;
    const pCrit = p.CRITICAL || 0;

    document.getElementById('probValLow').textContent = `${pLow}%`;
    document.getElementById('probValMod').textContent = `${pMod}%`;
    document.getElementById('probValHigh').textContent = `${pHigh}%`;
    document.getElementById('probValCrit').textContent = `${pCrit}%`;

    setTimeout(() => {
      document.getElementById('probFillLow').style.height = `${Math.max(4, pLow)}%`;
      document.getElementById('probFillMod').style.height = `${Math.max(4, pMod)}%`;
      document.getElementById('probFillHigh').style.height = `${Math.max(4, pHigh)}%`;
      document.getElementById('probFillCrit').style.height = `${Math.max(4, pCrit)}%`;
    }, 50);

    if (result.engineered_features) {
      const ef = result.engineered_features;
      document.getElementById('chipAri').textContent = `ARI: ${ef.ari_mm} mm`;
      document.getElementById('chipTwi').textContent = `TWI: ${ef.twi_index}`;
      document.getElementById('chipPwp').textContent = `Pore Press.: ${ef.pore_water_pressure_kpa} kPa`;
      document.getElementById('chipDisp').textContent = `Disp. Rate: ${ef.displacement_rate_mm_day} mm/d`;
    }
  } else {
    probContainer?.classList.add('hidden');
  }

  // 2. Explainable AI: Contribution Bars
  const barsContainer = document.getElementById('xaiBarsContainer');
  barsContainer.innerHTML = '';

  result.detailed_factors.forEach(factor => {
    const item = document.createElement('div');
    item.className = 'xai-bar-item';
    item.innerHTML = `
      <div class="xai-bar-header">
        <div>
          <span class="xai-factor-name">${factor.name}</span>
          <span class="xai-factor-weight">(${result.engine_type === 'ml_rf' ? 'RF Importance' : 'Weight'}: ${(factor.weight * 100).toFixed(0)}% • Value: ${factor.raw_value} ${factor.unit} • ${factor.status})</span>
        </div>
        <span class="xai-factor-pct">${factor.percentage_contribution}% share</span>
      </div>
      <div class="xai-progress-track">
        <div class="xai-progress-fill" style="width: 0%; background: ${result.color};"></div>
      </div>
    `;
    barsContainer.appendChild(item);

    // Trigger animation
    setTimeout(() => {
      item.querySelector('.xai-progress-fill').style.width = `${factor.percentage_contribution}%`;
    }, 50);
  });

  // 3. Detected Risk Factors List
  const factorsList = document.getElementById('detectedFactorsList');
  factorsList.innerHTML = '';
  result.factors.forEach(f => {
    const li = document.createElement('li');
    li.className = 'factor-list-item';
    li.innerHTML = `<span class="factor-check" style="color: ${result.color};">&#10003;</span> <span>${f}</span>`;
    factorsList.appendChild(li);
  });

  // 4. Recommendation
  document.getElementById('recActionText').textContent = result.recommended_action;

  // 5. Early Warning Banner Control
  const banner = document.getElementById('earlyWarningBanner');
  if (result.early_warning) {
    banner.classList.remove('hidden');
    document.getElementById('bannerLevelTitle').textContent = `${result.risk_level} EARLY WARNING DISPATCHED`;
    const locName = state.selectedLocation ? `${state.selectedLocation.name}, ${state.selectedLocation.state}` : 'Field Assessment Zone';
    document.getElementById('bannerLocationTag').textContent = locName;
    document.getElementById('bannerScoreTag').textContent = `Risk Score: ${result.risk_score}%`;
    document.getElementById('bannerActionText').textContent = result.recommended_action;
  } else {
    banner.classList.add('hidden');
  }
}

// Client-side fallback computation
function calculateClientRisk(rain, soil, slope, ground) {
  const normRain = Math.min(100, (rain / 200) * 100);
  const normSoil = Math.min(100, (soil / 100) * 100);
  const normSlope = Math.min(100, (slope / 50) * 100);
  const normGround = Math.min(100, (ground / 10) * 100);

  const weightedRain = normRain * 0.35;
  const weightedSoil = normSoil * 0.25;
  const weightedSlope = normSlope * 0.20;
  const weightedGround = normGround * 0.20;

  const score = Math.round(Math.min(100, Math.max(0, weightedRain + weightedSoil + weightedSlope + weightedGround)));

  let level = 'LOW';
  let color = '#10B981';
  let action = 'Routine telemetry monitoring. Slope integrity stable; standard drainage maintenance sufficient.';

  if (score >= 75) {
    level = 'CRITICAL';
    color = '#EF4444';
    action = 'URGENT DECISION SUPPORT: High probability of slope failure. Dispatch rapid verification units, prep traffic diversions, notify SDRF/NDRF teams.';
  } else if (score >= 50) {
    level = 'HIGH';
    color = '#F97316';
    action = 'Immediate field assessment and monitoring recommended. Alert district disaster control room and highway patrol.';
  } else if (score >= 30) {
    level = 'MODERATE';
    color = '#F59E0B';
    action = 'Elevated advisory status. Increase automated sensor polling frequency; inspect culverts and road cut slopes.';
  }

  const factors = [];
  if (rain >= 130) factors.push(`Torrential rainfall (${rain.toFixed(1)} mm) exceeding saturation threshold`);
  else if (rain >= 80) factors.push(`Heavy rainfall (${rain.toFixed(1)} mm) accelerating pore pressure`);
  
  if (soil >= 80) factors.push(`Critical soil moisture saturation (${soil.toFixed(1)}%) reducing cohesion`);
  else if (soil >= 65) factors.push(`High soil moisture content (${soil.toFixed(1)}%)`);

  if (slope >= 35) factors.push(`Very steep topography (${slope.toFixed(1)}°) with high gravitational shear stress`);
  else if (slope >= 25) factors.push(`Steep slope gradient (${slope.toFixed(1)}°)`);

  if (ground >= 6) factors.push(`Accelerated ground displacement (${ground.toFixed(1)} mm) indicates active shear movement`);
  else if (ground >= 3) factors.push(`Measurable slope creep detected (${ground.toFixed(1)} mm)`);

  if (factors.length === 0) factors.push('Environmental parameters within normal baseline limits');

  const totalRaw = weightedRain + weightedSoil + weightedSlope + weightedGround || 1;

  return {
    risk_score: score,
    risk_level: level,
    color: color,
    factors: factors,
    detailed_factors: [
      { name: 'Rainfall', raw_value: rain, unit: 'mm', weight: 0.35, percentage_contribution: ((weightedRain / totalRaw) * 100).toFixed(1), status: rain >= 120 ? 'Extreme' : 'Normal' },
      { name: 'Soil Moisture', raw_value: soil, unit: '%', weight: 0.25, percentage_contribution: ((weightedSoil / totalRaw) * 100).toFixed(1), status: soil >= 75 ? 'Saturated' : 'Normal' },
      { name: 'Slope Gradient', raw_value: slope, unit: 'deg', weight: 0.20, percentage_contribution: ((weightedSlope / totalRaw) * 100).toFixed(1), status: slope >= 30 ? 'Steep' : 'Gentle' },
      { name: 'Ground Movement', raw_value: ground, unit: 'mm', weight: 0.20, percentage_contribution: ((weightedGround / totalRaw) * 100).toFixed(1), status: ground >= 5 ? 'Active Shear' : 'Stable' }
    ],
    recommended_action: action,
    early_warning: score >= 50,
    timestamp: new Date().toLocaleTimeString()
  };
}

// ====================================================
// 6. INTERACTIVE GIS LEAFLET MAP
// ====================================================
function initGisMap() {
  const mapEl = document.getElementById('gisMap');
  if (!mapEl) return;

  // Base Tile Layers (NO API KEY REQUIRED - Green Land, Blue Water Bodies)
  const osmStandard = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
    maxZoom: 19
  });

  const esriTopo = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; USGS, NOAA',
    maxZoom: 19
  });

  const esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Earthstar Geographics',
    maxZoom: 18
  });

  // Center on Northeast India (Sikkim to Arunachal / Assam / Meghalaya)
  state.gisMap = L.map('gisMap', {
    center: [25.8, 93.0],
    zoom: 7,
    minZoom: 5,
    maxZoom: 14,
    layers: [osmStandard] // Default: Green areas and blue rivers/oceans
  });

  // Layer control switcher for officers and hackathon judges
  const baseMaps = {
    "🌿 Standard GIS (Green Land, Blue Rivers)": osmStandard,
    "🏔️ Topographic Relief (Green Slopes, Rivers)": esriTopo,
    "🛰️ Satellite Imagery (Real Earth)": esriSatellite
  };
  L.control.layers(baseMaps, null, { position: 'topright' }).addTo(state.gisMap);

  document.getElementById('btnResetMapView')?.addEventListener('click', () => {
    state.gisMap.setView([25.8, 93.0], 7, { animate: true });
  });
}

function initFullGisMap() {
  const mapEl = document.getElementById('fullGisMap');
  if (!mapEl) return;

  const fullOsm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
    maxZoom: 19
  });

  const fullTopo = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; USGS, NOAA',
    maxZoom: 19
  });

  const fullSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Earthstar Geographics',
    maxZoom: 18
  });

  state.fullGisMap = L.map('fullGisMap', {
    center: [25.8, 93.0],
    zoom: 7,
    layers: [fullOsm]
  });

  const fullBaseMaps = {
    "🌿 Standard GIS (Green Land, Blue Rivers)": fullOsm,
    "🏔️ Topographic Relief (Green Slopes, Rivers)": fullTopo,
    "🛰️ Satellite Imagery (Real Earth)": fullSatellite
  };
  L.control.layers(fullBaseMaps, null, { position: 'topright' }).addTo(state.fullGisMap);

  // Populate markers on full map
  renderGisMarkers(state.locations, true);

  // Filter buttons on full map
  const filterPills = document.querySelectorAll('.filter-pill');
  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const filter = pill.getAttribute('data-filter');
      filterFullMap(filter);
    });
  });
}

function renderGisMarkers(locations, isFullMap = false) {
  const targetMap = isFullMap ? state.fullGisMap : state.gisMap;
  if (!targetMap) return;

  const markersStore = isFullMap ? state.fullMapMarkers : state.mapMarkers;

  // Clear existing
  Object.values(markersStore).forEach(m => targetMap.removeLayer(m));

  locations.forEach(loc => {
    const pinClass = getPinClass(loc.risk_level);
    const customIcon = L.divIcon({
      className: 'custom-pin-wrapper',
      html: `<div class="custom-pin ${pinClass}">${loc.risk_score}</div>`,
      iconSize: [28, 28],
      iconAnchor: [14, 14]
    });

    const marker = L.marker([loc.latitude, loc.longitude], { icon: customIcon }).addTo(targetMap);

    const popupHtml = `
      <div class="map-popup-container">
        <div class="map-popup-title">${loc.name}</div>
        <div class="map-popup-badge ${getBadgeClass(loc.risk_level)}">${loc.risk_level} • Score: ${loc.risk_score}%</div>
        <div class="map-popup-specs">
          <span>State: ${loc.state} (${loc.district})</span>
          <span>Rainfall: ${loc.last_rainfall} mm</span>
          <span>Soil Moisture: ${loc.last_soil_moisture}%</span>
          <span>Slope: ${loc.slope}°</span>
          <span>Ground Shift: ${loc.last_ground_movement} mm</span>
        </div>
        <button class="btn-popup-inspect" onclick="window.selectLocationFromMap('${loc.id}')">
          Inspect & Analyze Area
        </button>
      </div>
    `;

    marker.bindPopup(popupHtml);

    marker.on('click', () => {
      selectLocation(loc, false);
    });

    markersStore[loc.id] = marker;
  });
}

window.selectLocationFromMap = function(locId) {
  const loc = state.locations.find(l => l.id === locId);
  if (loc) {
    // Switch to Dashboard Tab
    const dashTab = document.querySelector('[data-tab="tab-dashboard"]');
    if (dashTab) dashTab.click();
    selectLocation(loc, true);
  }
};

function updateSingleMarker(locId, newScore, newLevel) {
  const marker = state.mapMarkers[locId];
  if (marker) {
    const pinClass = getPinClass(newLevel);
    const newIcon = L.divIcon({
      className: 'custom-pin-wrapper',
      html: `<div class="custom-pin ${pinClass}">${newScore}</div>`,
      iconSize: [28, 28],
      iconAnchor: [14, 14]
    });
    marker.setIcon(newIcon);
  }
}

function filterFullMap(filter) {
  if (!state.fullGisMap) return;
  state.locations.forEach(loc => {
    const marker = state.fullMapMarkers[loc.id];
    if (!marker) return;

    let show = true;
    if (filter === 'high-crit') {
      show = (loc.risk_level === 'HIGH' || loc.risk_level === 'CRITICAL');
    } else if (filter === 'sikkim-meghalaya') {
      show = (loc.state === 'Sikkim' || loc.state === 'Meghalaya');
    }

    if (show) {
      if (!state.fullGisMap.hasLayer(marker)) marker.addTo(state.fullGisMap);
    } else {
      if (state.fullGisMap.hasLayer(marker)) state.fullGisMap.removeLayer(marker);
    }
  });
}

function getPinClass(level) {
  switch (level) {
    case 'CRITICAL': return 'pin-crit';
    case 'HIGH': return 'pin-high';
    case 'MODERATE': return 'pin-mod';
    default: return 'pin-low';
  }
}

function getBadgeClass(level) {
  switch (level) {
    case 'CRITICAL': return 'badge-crit';
    case 'HIGH': return 'badge-high';
    case 'MODERATE': return 'badge-mod';
    default: return 'badge-low';
  }
}

// ====================================================
// 7. ALERT CENTER & ACKNOWLEDGMENT
// ====================================================
async function loadAlerts() {
  try {
    const res = await fetch(`${API_BASE}/alerts`);
    if (!res.ok) throw new Error('Failed to load alerts');
    const alerts = await res.json();
    state.activeAlerts = alerts;

    const activeCount = alerts.filter(a => a.status === 'ACTIVE').length;
    document.getElementById('activeAlertsBadge').textContent = activeCount;
    document.getElementById('kpiActiveAlerts').textContent = activeCount;

    renderAlertsStream(alerts);
  } catch (err) {
    console.warn('Alerts loading error:', err);
  }
}

function renderAlertsStream(alerts) {
  const container = document.getElementById('alertsStreamContainer');
  container.innerHTML = '';

  if (alerts.length === 0) {
    container.innerHTML = '<div class="obs-notes text-muted" style="padding: 1rem;">No alerts on file. System operational.</div>';
    return;
  }

  alerts.forEach(alert => {
    const card = document.createElement('div');
    const levelClass = alert.risk_level.toLowerCase().substring(0, 4);
    card.className = `alert-card-item ${levelClass}`;
    card.setAttribute('data-status', alert.status);

    const isAck = alert.status === 'ACKNOWLEDGED';

    let factorsHtml = '';
    if (alert.main_factors && Array.isArray(alert.main_factors)) {
      factorsHtml = alert.main_factors.map(f => `<span class="factor-chip">${f}</span>`).join('');
    }

    card.innerHTML = `
      <div class="alert-item-header">
        <div class="alert-title-block">
          <span class="alert-loc-name">${alert.location_name}</span>
          <span class="alert-state-name">${alert.state}</span>
          <span class="risk-badge ${getBadgeClass(alert.risk_level)}">${alert.risk_level} (${alert.risk_score}%)</span>
        </div>
        <div>
          <span class="alert-status-pill ${isAck ? 'status-ack' : 'status-active'}">
            ${alert.status}
          </span>
        </div>
      </div>

      <div class="alert-factors-chips">
        ${factorsHtml}
      </div>

      <div class="alert-action-rec">
        <strong>Recommended Action:</strong> ${alert.recommended_action}
      </div>

      <div class="alert-footer-meta">
        <div>
          <span>Dispatched: ${alert.timestamp}</span>
          ${isAck ? `<span style="margin-left: 1rem; color: #10B981;">• Acknowledged by: ${alert.acknowledged_by || 'Field Officer'}</span>` : ''}
        </div>
        ${!isAck ? `<button class="btn-ack-alert" onclick="window.acknowledgeAlert('${alert.id}')">Acknowledge Alert</button>` : ''}
      </div>
    `;

    container.appendChild(card);
  });
}

function initAlertFilters() {
  const filterBtns = document.querySelectorAll('.alert-tab-btn');
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.getAttribute('data-alert-filter');
      const cards = document.querySelectorAll('.alert-card-item');
      cards.forEach(c => {
        if (filter === 'all') {
          c.style.display = 'flex';
        } else {
          c.style.display = c.getAttribute('data-status') === filter ? 'flex' : 'none';
        }
      });
    });
  });
}

window.acknowledgeAlert = async function(alertId) {
  try {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        officer_name: 'District Disaster Officer (On-Duty)',
        notes: 'Field reconnaissance unit notified.'
      })
    });

    if (res.ok) {
      showToast(`Alert ${alertId} Acknowledged`, 'success');
      loadAlerts();
    } else {
      throw new Error('Failed to acknowledge');
    }
  } catch (err) {
    showToast('Failed to acknowledge alert', 'error');
  }
};

// ====================================================
// 8. ANALYTICS & CHARTS (Chart.js)
// ====================================================
async function renderAnalyticsCharts() {
  const select = document.getElementById('analyticsLocationSelect');
  const locId = select.value || (state.locations[0] ? state.locations[0].id : null);
  if (!locId) return;

  try {
    const res = await fetch(`${API_BASE}/location/${locId}`);
    if (!res.ok) throw new Error('Failed to load history');
    const data = await res.json();
    const history = data.history;

    if (!history || history.length === 0) return;

    // Filter by timeframe
    const displayData = state.analyticsTimeframe === '24h' ? history.slice(-6) : history;

    const labels = displayData.map(d => d.timestamp.split(' ')[1] || d.timestamp);
    const rainVals = displayData.map(d => d.rainfall);
    const soilVals = displayData.map(d => d.soil_moisture);
    const groundVals = displayData.map(d => d.ground_movement);
    const scoreVals = displayData.map(d => d.risk_score);

    createOrUpdateChart('chartRainfall', 'bar', labels, rainVals, 'Rainfall (mm)', '#06B6D4', 'rgba(6, 182, 212, 0.2)');
    createOrUpdateChart('chartSoil', 'line', labels, soilVals, 'Soil Moisture (%)', '#10B981', 'rgba(16, 185, 129, 0.2)', true);
    createOrUpdateChart('chartGround', 'line', labels, groundVals, 'Ground Shift (mm)', '#F59E0B', 'rgba(245, 158, 11, 0.2)');
    createOrUpdateChart('chartRiskScore', 'line', labels, scoreVals, 'Risk Score (0–100)', '#EF4444', 'rgba(239, 68, 68, 0.2)', true);

  } catch (err) {
    console.warn('Analytics loading error:', err);
  }
}

function createOrUpdateChart(canvasId, type, labels, data, label, color, bgColor, fill = false) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  if (state.charts[canvasId]) {
    state.charts[canvasId].destroy();
  }

  const isLight = document.body.classList.contains('light-theme');
  const textColor = isLight ? '#1E293B' : '#94A3B8';
  const gridColor = isLight ? 'rgba(0, 0, 0, 0.06)' : 'rgba(255, 255, 255, 0.05)';
  const tickColor = isLight ? '#475569' : '#64748B';

  state.charts[canvasId] = new Chart(ctx, {
    type: type,
    data: {
      labels: labels,
      datasets: [{
        label: label,
        data: data,
        borderColor: color,
        backgroundColor: bgColor,
        borderWidth: 2,
        fill: fill,
        tension: 0.35,
        pointBackgroundColor: color,
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          labels: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' } }
        }
      },
      scales: {
        x: {
          grid: { color: gridColor },
          ticks: { color: tickColor, font: { family: 'Plus Jakarta Sans', size: 10 } }
        },
        y: {
          grid: { color: gridColor },
          ticks: { color: tickColor, font: { family: 'Plus Jakarta Sans', size: 10 } }
        }
      }
    }
  });
}

// Timeframe toggle buttons
document.querySelectorAll('.btn-toggle').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.btn-toggle').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.analyticsTimeframe = btn.getAttribute('data-timeframe');
    renderAnalyticsCharts();
  });
});

// ====================================================
// 9. FIELD OBSERVATION & SITE PHOTO MODULE
// ====================================================
function initPhotoUpload() {
  const dropZone = document.getElementById('photoDropZone');
  const fileInput = document.getElementById('photoFileInput');
  const previewContainer = document.getElementById('previewContainer');
  const previewImg = document.getElementById('photoPreviewImg');
  const uploadPrompt = document.getElementById('uploadPrompt');
  const removeBtn = document.getElementById('btnRemovePhoto');

  let currentPhotoBase64 = null;

  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        currentPhotoBase64 = event.target.result;
        previewImg.src = currentPhotoBase64;
        previewContainer.classList.remove('hidden');
        uploadPrompt.classList.add('hidden');
      };
      reader.readAsDataURL(file);
    }
  });

  removeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    currentPhotoBase64 = null;
    fileInput.value = '';
    previewImg.src = '';
    previewContainer.classList.add('hidden');
    uploadPrompt.classList.remove('hidden');
  });

  // Submit Observation
  document.getElementById('btnSubmitObservation').addEventListener('click', async () => {
    const locSelect = document.getElementById('obsLocationSelect');
    const locId = locSelect.value;
    const locName = locSelect.options[locSelect.selectedIndex]?.text || 'Sentinel Station';
    const officer = document.getElementById('obsOfficerName').value;
    const notes = document.getElementById('obsNotes').value;

    if (!notes.trim()) {
      showToast('Please enter observation notes', 'error');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/observations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location_id: locId,
          location_name: locName,
          officer_name: officer,
          notes: notes,
          photo_data: currentPhotoBase64
        })
      });

      if (res.ok) {
        showToast('Observation recorded in SQLite database', 'success');
        document.getElementById('obsNotes').value = '';
        removeBtn.click();
        loadObservations();
      } else {
        throw new Error('Failed to record');
      }
    } catch (err) {
      showToast('Failed to save observation to backend', 'error');
    }
  });

  document.getElementById('btnRefreshObservations')?.addEventListener('click', loadObservations);
}

async function loadObservations() {
  try {
    const res = await fetch(`${API_BASE}/observations`);
    if (!res.ok) throw new Error('Failed to load observations');
    const data = await res.json();
    state.observations = data;

    const container = document.getElementById('observationFeedContainer');
    container.innerHTML = '';

    if (data.length === 0) {
      container.innerHTML = '<div class="obs-notes text-muted">No observations recorded yet.</div>';
      return;
    }

    data.forEach(obs => {
      const item = document.createElement('div');
      item.className = 'obs-card';
      item.innerHTML = `
        <div class="obs-header">
          <span class="obs-loc">${obs.location_name}</span>
          <span class="obs-time">${obs.timestamp}</span>
        </div>
        <div class="obs-officer">&#128100; ${obs.officer_name}</div>
        <div class="obs-notes">${obs.notes}</div>
        ${obs.photo_data ? `<div style="margin-top: 0.5rem;"><img src="${obs.photo_data}" style="max-height: 120px; border-radius: 4px; border: 1px solid #1E293B;"></div>` : ''}
        <div class="obs-badge-cv">&#9679; ${obs.cv_status}</div>
      `;
      container.appendChild(item);
    });
  } catch (err) {
    console.warn('Observations load error:', err);
  }
}

function initFormSubmissions() {
  // Prevent any default form reload
  document.querySelectorAll('form').forEach(f => {
    f.addEventListener('submit', (e) => e.preventDefault());
  });
}

// ====================================================
// 10. TOAST NOTIFICATION UTILITY
// ====================================================
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type === 'error' ? 'toast-error' : type === 'success' ? 'toast-success' : ''}`;
  toast.textContent = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ====================================================
// 11. LIVE ML ARCHITECTURE & TELEMETRY LOADER
// ====================================================
async function loadMlArchitectureStatus() {
  try {
    const res = await fetch(`${API_BASE}/ml-status`);
    if (!res.ok) return;
    const data = await res.json();
    state.mlStatus = data;

    const badge = document.getElementById('archMlStatusBadge');
    if (badge && data.ml_pipeline_status === 'LOADED') {
      badge.textContent = '● MODEL LOADED & ACTIVE';
      badge.className = 'badge badge-future';
    }

    const accEl = document.getElementById('archMlAccuracy');
    if (accEl && data.accuracy !== undefined) {
      accEl.textContent = `${(data.accuracy * 100).toFixed(1)}%`;
    }

    const container = document.getElementById('archFeatureImportanceContainer');
    if (container && data.feature_importances) {
      container.innerHTML = '';
      for (const [feat, pct] of Object.entries(data.feature_importances)) {
        const row = document.createElement('div');
        row.className = 'feat-imp-row';
        row.innerHTML = `
          <div class="feat-name-tag"><code>${feat}</code></div>
          <div class="feat-bar-track">
            <div class="feat-bar-fill" style="width: ${Math.min(100, pct * 2.5)}%;"></div>
          </div>
          <div class="feat-pct-val">${pct.toFixed(2)}%</div>
        `;
        container.appendChild(row);
      }
    }
  } catch (err) {
    console.warn('Failed to load ML architecture status:', err);
  }
}
