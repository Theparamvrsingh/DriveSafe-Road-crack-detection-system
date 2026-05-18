import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";

const API_BASE = `${location.origin}/api`;
const cx = (...xs) => xs.filter(Boolean).join(" ");

/* ─── SVG Icons ─── */
const Icons = {
  scan: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="12" y1="8" x2="12" y2="16"/></svg>,
  alert: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>,
  upload: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>,
  map: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>,
  history: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>,
  trending: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>,
  info: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>,
};

const DEMO_IMAGES = [
  { url: "/assets/sample_road.png", label: "Crack 1" },
  { url: "/assets/test_pothole_D40.png", label: "Pothole" },
  { url: "/assets/test_longitudinal_crack_D00.png", label: "Crack 2" },
];

/* ─── UI Components ─── */
function Panel({ title, icon, children, className = "" }) {
  return (
    <div className={cx("panel fade-in", className)}>
      <div className="panel-header">
        <div className="panel-header-dot" />
        {icon && <span style={{ opacity: 0.7 }}>{icon}</span>}
        <span className="panel-title">{title}</span>
      </div>
      <div className="panel-body">{children}</div>
    </div>
  );
}

/* ─── Leaflet Map ─── */
function Map({ points, center = [28.6139, 77.209] }) {
  const mapRef = useRef(null);
  const layerRef = useRef(null);
  const divRef = useRef(null);

  useEffect(() => {
    if (!divRef.current || !window.L || mapRef.current) return;
    mapRef.current = window.L.map(divRef.current, { zoomControl: true, attributionControl: false }).setView(center, 12);
    window.L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png").addTo(mapRef.current);
    layerRef.current = window.L.layerGroup().addTo(mapRef.current);
    const obs = new ResizeObserver(() => mapRef.current?.invalidateSize());
    obs.observe(divRef.current);
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    if (!layerRef.current || !mapRef.current) return;
    layerRef.current.clearLayers();
    const pts = points.filter(p => typeof p.lat === "number" && typeof p.lon === "number");
    pts.forEach(p => {
      const color = p.severity === "high" ? "var(--red)" : p.severity === "medium" ? "var(--amber)" : "var(--green)";
      const marker = window.L.circleMarker([p.lat, p.lon], { radius: 8, color, weight: 2, fillColor: color, fillOpacity: 0.7 });
      marker.bindPopup(`<div style="font-size:12px"><b>Severity:</b> ${(p.severity || "N/A").toUpperCase()}<br/><b>Time:</b> ${p.timestamp || "Unknown"}</div>`);
      marker.addTo(layerRef.current);
    });
    if (pts.length > 0) mapRef.current.fitBounds(window.L.latLngBounds(pts.map(p => [p.lat, p.lon])).pad(0.2));
  }, [points]);

  return <div ref={divRef} className="map-wrap" style={{ height: "450px", width: "100%" }} />;
}

/* ─── Workflow Section ─── */
function WorkflowOverview() {
  return (
    <Panel title="System Workflow" icon={Icons.info}>
      <div className="workflow-step">
        <div className="step-num">1</div>
        <div className="step-content">
          <h4>Capture Road Damage</h4>
          <p>Upload a high-quality photo of the road surface using your device.</p>
        </div>
      </div>
      <div className="workflow-step">
        <div className="step-num">2</div>
        <div className="step-content">
          <h4>Autonomous AI Analysis</h4>
          <p>Deep learning models segment cracks and detect potholes in real-time.</p>
        </div>
      </div>
      <div className="workflow-step" style={{ marginBottom: 0 }}>
        <div className="step-num">3</div>
        <div className="step-content">
          <h4>Geo-Tagged Reporting & Prediction</h4>
          <p>Severity is calculated, geo-tagged, and used for 30-day maintenance risk forecasting.</p>
        </div>
      </div>
    </Panel>
  );
}

/* ─── Crack Analysis Tab ─── */
function CrackAnalysisTab() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  async function loadDemoImage(url, filename) {
    try {
      const res = await fetch(url);
      const blob = await res.blob();
      setFile(new File([blob], filename, { type: blob.type }));
      setResult(null);
    } catch (err) { alert("Failed to load demo image"); }
  }

  async function handleAnalyze(e) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    const fd = new FormData(); fd.append("file", file);
    try {
      const [seg, det] = await Promise.all([
        fetch(`${API_BASE}/predict-segmentation`, { method: "POST", body: fd }).then(r => r.json()),
        fetch(`${API_BASE}/detect-rdd`, { method: "POST", body: fd }).then(r => r.json())
      ]);
      setResult({ 
        mask: seg.mask_base64, 
        density: seg.crack_percentage,
        severity: seg.severity,
        action: seg.action,
        rationale: seg.rationale,
        metrics: seg.metrics,
        source: seg.source,
        detections: det.detections || [] 
      });
    } catch (err) { alert("Analysis failed. Render free tier backend might be restarting. Please try again in 60 seconds."); }
    finally { setLoading(false); }
  }

  return (
    <div className="slide-up" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", alignItems: "start" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        <Panel title="Analysis Input" icon={Icons.upload}>
          <form onSubmit={handleAnalyze}>
            <div className="upload-zone" onClick={() => document.getElementById("file-input").click()}>
              <div style={{ color: "var(--cyan)", marginBottom: "16px", display: "flex", justifyContent: "center" }}>{Icons.upload}</div>
              <p style={{ fontSize: "14px", fontWeight: 600 }}>{file ? file.name : "Click to select road image"}</p>
              <input id="file-input" type="file" hidden onChange={e => {setFile(e.target.files[0]); setResult(null);}} />
            </div>
            
            <div style={{ marginTop: "16px" }}>
              <p style={{ fontSize: "11px", color: "var(--text-dim)", textTransform: "uppercase" }}>Or test with demo images:</p>
              <div className="demo-images-container">
                {DEMO_IMAGES.map((demo, i) => (
                  <button key={i} type="button" className="demo-image-btn" onClick={() => loadDemoImage(demo.url, demo.url.split('/').pop())} title={demo.label}>
                    <img src={demo.url} alt={demo.label} />
                  </button>
                ))}
              </div>
            </div>

            <button type="submit" disabled={!file || loading} className="btn-primary" style={{ marginTop: "20px" }}>
              {loading ? "Analyzing..." : "Run AI Diagnostics"}
            </button>
          </form>
        </Panel>

        {result ? (
          <Panel title="Diagnostic Results" icon={Icons.trending}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
              <div className="stat-box">
                <p style={{ fontSize: "10px", color: "var(--text-ghost)", textTransform: "uppercase" }}>Damage Density</p>
                <p style={{ fontSize: "20px", fontWeight: 700, color: result.density > 10 ? "var(--red)" : "var(--green)" }}>{result.density?.toFixed(1) || 0}%</p>
              </div>
              <div className="stat-box">
                <p style={{ fontSize: "10px", color: "var(--text-ghost)", textTransform: "uppercase" }}>Severity Level</p>
                <p style={{ fontSize: "20px", fontWeight: 700, color: result.severity === 'High' ? "var(--red)" : (result.severity === 'Medium' ? "var(--amber)" : "var(--green)") }}>{result.severity || "N/A"}</p>
              </div>
            </div>

            {result.metrics && Object.keys(result.metrics).length > 0 && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
                <div className="stat-box" style={{ padding: "10px" }}>
                   <p style={{ fontSize: "9px", color: "var(--text-ghost)", textTransform: "uppercase" }}>Est. Crack Length</p>
                   <p style={{ fontSize: "14px", fontWeight: 600, color: "var(--cyan)" }}>{result.metrics.crack_length_px?.toFixed(0)} px</p>
                </div>
                <div className="stat-box" style={{ padding: "10px" }}>
                   <p style={{ fontSize: "9px", color: "var(--text-ghost)", textTransform: "uppercase" }}>Max Crack Width</p>
                   <p style={{ fontSize: "14px", fontWeight: 600, color: "var(--cyan)" }}>{result.metrics.crack_width_p95_px?.toFixed(1)} px</p>
                </div>
              </div>
            )}
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid var(--border)", marginBottom: "16px" }}>
               <p style={{ fontSize: "11px", color: "var(--text-dim)", textTransform: "uppercase", marginBottom: "4px" }}>Recommended Action</p>
               <p style={{ fontSize: "14px", fontWeight: 600, color: "var(--cyan)" }}>{result.action || "Inspect Manually"}</p>
               <p style={{ fontSize: "12px", color: "var(--text-dim)", marginTop: "4px" }}>{result.rationale}</p>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {result.detections?.map((d, i) => (
                <div key={i} className="record-row" style={{ gridTemplateColumns: "1fr auto", margin: 0 }}>
                  <span style={{ fontSize: "13px", fontWeight: 600 }}>{d.class}</span>
                  <span style={{ fontSize: "12px", color: "var(--cyan)" }}>{(d.confidence * 100).toFixed(0)}%</span>
                </div>
              ))}
              {result.detections?.length === 0 && (
                <p style={{ fontSize: "12px", color: "var(--text-dim)" }}>No bounding box detections found.</p>
              )}
            </div>
          </Panel>
        ) : (
          <WorkflowOverview />
        )}
      </div>

      <Panel title="Advanced Visual Overlay" icon={Icons.scan}>
        {!result && !file && (
          <div style={{ height: "450px", display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,0.3)", borderRadius: "8px", border: "1px dashed var(--border)" }}>
            <p style={{ color: "var(--text-ghost)", fontSize: "14px" }}>Awaiting input image for visual processing...</p>
          </div>
        )}
        {(file || result) && (
          <div style={{ display: "grid", gridTemplateRows: "auto auto", gap: "16px" }}>
            <div style={{ position: "relative", borderRadius: "8px", overflow: "hidden", border: "1px solid var(--border)", background: "#000", height: "250px" }}>
              <img src={file ? URL.createObjectURL(file) : ""} alt="input" style={{ width: "100%", height: "100%", objectFit: "contain" }} />
              <div style={{ position: "absolute", top: "8px", left: "8px", background: "rgba(0,0,0,0.6)", color: "white", padding: "4px 8px", borderRadius: "4px", fontSize: "10px", fontFamily: "var(--font-mono)" }}>ORIGINAL INPUT</div>
            </div>
            <div style={{ position: "relative", borderRadius: "8px", overflow: "hidden", border: "1px solid var(--border)", background: "#000", height: "250px" }}>
              {result?.mask ? (
                <img src={result.mask} alt="mask" style={{ width: "100%", height: "100%", objectFit: "contain" }} />
              ) : (
                <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
                   <p style={{ color: "var(--text-ghost)", fontSize: "12px" }}>Mask generating...</p>
                </div>
              )}
              <div style={{ position: "absolute", top: "8px", left: "8px", background: "rgba(0,0,0,0.6)", color: "var(--cyan)", padding: "4px 8px", borderRadius: "4px", fontSize: "10px", fontFamily: "var(--font-mono)" }}>AI SEGMENTATION MASK</div>
            </div>
          </div>
        )}
      </Panel>
    </div>
  );
}

/* ─── Pothole Reporting Tab ─── */
function PotholeTab() {
  const [file, setFile] = useState(null);
  const [loc, setLoc] = useState(null);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => { fetchReports(); }, []);

  async function fetchReports() {
    try { const r = await fetch(`${API_BASE}/get-potholes`).then(r => r.json()); setReports(r.data || []); } catch (e) {}
  }

  function getGPS() {
    navigator.geolocation.getCurrentPosition(
      p => setLoc({ lat: p.coords.latitude, lon: p.coords.longitude }),
      err => { alert("Failed to get GPS. Setting mock location for demo."); setLoc({ lat: 28.6139 + Math.random()*0.01, lon: 77.209 + Math.random()*0.01 }); }
    );
  }

  async function loadDemoImage(url, filename) {
    try {
      const res = await fetch(url);
      const blob = await res.blob();
      setFile(new File([blob], filename, { type: blob.type }));
    } catch (err) { alert("Failed to load demo image"); }
  }

  async function handleReport(e) {
    e.preventDefault();
    if (!file || !loc) return;
    setLoading(true);
    const fd = new FormData(); fd.append("file", file); fd.append("lat", loc.lat); fd.append("lon", loc.lon);
    try {
      const res = await fetch(`${API_BASE}/report-pothole`, { method: "POST", body: fd }).then(r => r.json());
      fetchReports();
      alert(`Incident reported successfully!\n\nAn automated alert email has been dispatched to: paramveercse@gmail.com`);
    } catch (e) { alert("Failed to report. Render backend might be waking up, please try again in 60 seconds."); }
    finally { setLoading(false); }
  }

  return (
    <div className="slide-up" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", alignItems: "start" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        <Panel title="Report Incident" icon={Icons.alert}>
          <form onSubmit={handleReport}>
            <div className="upload-zone" onClick={() => document.getElementById("p-input").click()}>
              <div style={{ color: "var(--green)", marginBottom: "16px", display: "flex", justifyContent: "center" }}>{Icons.upload}</div>
              <p style={{ fontSize: "14px", fontWeight: 600 }}>{file ? file.name : "Capture Pothole Photo"}</p>
              <input id="p-input" type="file" hidden onChange={e => setFile(e.target.files[0])} capture="environment" />
            </div>

            <div style={{ marginTop: "16px" }}>
              <p style={{ fontSize: "11px", color: "var(--text-dim)", textTransform: "uppercase" }}>Demo Image:</p>
              <div className="demo-images-container">
                <button type="button" className="demo-image-btn" onClick={() => loadDemoImage("/assets/test_pothole_D40.png", "pothole.png")}>
                  <img src="/assets/test_pothole_D40.png" alt="Demo Pothole" />
                </button>
              </div>
            </div>

            <div style={{ margin: "16px 0", padding: "12px", background: "rgba(0,0,0,0.3)", borderRadius: "8px", border: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "12px", fontWeight: 600, fontFamily: "var(--font-mono)", color: loc ? "var(--green)" : "var(--text-dim)" }}>
                {loc ? `${loc.lat.toFixed(4)}, ${loc.lon.toFixed(4)}` : "Location Missing"}
              </span>
              <button type="button" onClick={getGPS} className="nav-tab" style={{ padding: "4px 8px", fontSize: "11px", border: "1px solid var(--border)" }}>{loc ? "Update" : "Get GPS"}</button>
            </div>
            <button type="submit" disabled={!file || !loc || loading} className="btn-primary" style={{ background: "linear-gradient(135deg, #10b981, #059669)" }}>
              {loading ? "Reporting..." : "Submit Incident"}
            </button>
          </form>
        </Panel>
      </div>
      <Panel title="Real-time Incident Map" icon={Icons.map}>
        <Map points={reports} center={loc ? [loc.lat, loc.lon] : [28.6139, 77.209]} />
      </Panel>
    </div>
  );
}

/* ─── Maintenance & History Tab ─── */
function HistoryTab() {
  const [records, setRecords] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/records`).then(r => r.json()).then(d => setRecords(d.items || []));
    fetch(`${API_BASE}/predictions`).then(r => r.json()).then(d => setPredictions(d.items || []));
  }, []);

  async function generatePrediction() {
    if (records.length === 0) return alert("No records available to predict.");
    setGenerating(true);
    // Use the coordinates of the most recent record
    const { lat, lon } = records[0];
    try {
        const res = await fetch(`${API_BASE}/predict?lat=${lat}&lon=${lon}&horizon_days=30`).then(r => r.json());
        if (res.detail) {
            alert("Error: " + res.detail);
        } else {
            alert(`Prediction generated successfully! Projected Risk: ${res.risk}`);
            // Refresh predictions
            fetch(`${API_BASE}/predictions`).then(r => r.json()).then(d => setPredictions(d.items || []));
        }
    } catch (e) {
        alert("Failed to generate prediction. Server might be asleep.");
    } finally {
        setGenerating(false);
    }
  }

  return (
    <div className="slide-up" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
      <Panel title="Inspection History" icon={Icons.history}>
        <div style={{ maxHeight: "600px", overflowY: "auto", paddingRight: "8px" }}>
          {records.map((r, i) => (
            <div key={i} className="record-row">
              <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: r.severity === "high" ? "var(--red)" : "var(--green)", marginTop: "4px" }} />
              <div>
                <p style={{ fontSize: "13px", fontWeight: 700 }}>{r.image_path ? r.image_path.split('/').pop() : "Unknown Record"}</p>
                <p style={{ fontSize: "11px", color: "var(--text-ghost)", fontFamily: "var(--font-mono)" }}>{r.lat}, {r.lon}</p>
              </div>
              <span style={{ fontSize: "11px", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>{r.timestamp?.split('T')[0]}</span>
            </div>
          ))}
          {records.length === 0 && <p style={{ textAlign: "center", color: "var(--text-ghost)", padding: "40px" }}>No historical records found.</p>}
        </div>
      </Panel>
      <Panel title="AI Risk Predictions" icon={Icons.trending}>
        <div style={{ maxHeight: "600px", overflowY: "auto", paddingRight: "8px" }}>
          {predictions.map((p, i) => (
            <div key={i} className="record-row" style={{ gridTemplateColumns: "1fr auto" }}>
              <div>
                <p style={{ fontSize: "13px", fontWeight: 700, color: p.predicted_severity === "high" ? "var(--red)" : "var(--amber)" }}>{p.predicted_severity?.toUpperCase()} RISK</p>
                <p style={{ fontSize: "11px", color: "var(--text-dim)" }}>{p.rationale}</p>
                <p style={{ fontSize: "10px", color: "var(--text-ghost)", marginTop: "4px", fontFamily: "var(--font-mono)" }}>{p.lat}, {p.lon}</p>
              </div>
              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: "14px", fontWeight: 700, color: "var(--cyan)" }}>{p.predicted_score?.toFixed(1)}%</span>
                <p style={{ fontSize: "9px", color: "var(--text-ghost)" }}>{p.horizon_days}d Forecast</p>
              </div>
            </div>
          ))}
          {predictions.length === 0 && (
            <div style={{ textAlign: "center", padding: "40px" }}>
              <p style={{ color: "var(--text-ghost)", fontSize: "14px" }}>Collect more history at a location to unlock predictive analysis.</p>
            </div>
          )}
          <div style={{ marginTop: "16px" }}>
            <button onClick={generatePrediction} disabled={generating} className="btn-primary" style={{ width: "100%" }}>
              {generating ? "Generating..." : "Generate 30-Day Risk Forecast"}
            </button>
          </div>
        </div>
      </Panel>
    </div>
  );
}

/* ─── Main App ─── */
function App() {
  const [tab, setTab] = useState("analysis");

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <div className="bg-subtle-grid" />
      <div className="bg-soft-glow bg-glow-1" />
      <div className="bg-soft-glow bg-glow-2" />

      <header style={{ background: "rgba(10, 13, 20, 0.8)", backdropFilter: "blur(20px)", borderBottom: "1px solid var(--border)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "0 24px", height: "70px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ width: "40px", height: "40px", borderRadius: "10px", background: "linear-gradient(135deg, #00CFFF, #0099CC)", display: "flex", alignItems: "center", justifyContent: "center", color: "#000" }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            </div>
            <div>
              <h1 style={{ fontSize: "18px", fontWeight: 800, letterSpacing: "-0.02em", color: "var(--text)" }}>DriveSafe</h1>
              <p style={{ fontSize: "10px", color: "var(--cyan)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", fontFamily: "var(--font-mono)" }}>AI Road Intelligence</p>
            </div>
          </div>

          <nav style={{ display: "flex", gap: "4px", background: "rgba(0,0,0,0.3)", padding: "4px", borderRadius: "10px", border: "1px solid var(--border)" }}>
            <button onClick={() => setTab("analysis")} className={cx("nav-tab", tab === "analysis" && "active-blue")}>{Icons.scan} Diagnostics</button>
            <button onClick={() => setTab("pothole")} className={cx("nav-tab", tab === "pothole" && "active-green")}>{Icons.alert} Reporter</button>
            <button onClick={() => setTab("history")} className={cx("nav-tab", tab === "history" && "active-blue")}>{Icons.history} Maintenance</button>
          </nav>

          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "11px", fontWeight: 600, color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
            <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--green)", boxShadow: "0 0 8px var(--green)" }} />
            SYSTEM ACTIVE
          </div>
        </div>
      </header>

      <main style={{ maxWidth: "1200px", margin: "0 auto", width: "100%", padding: "40px 24px", flex: 1 }}>
        <div style={{ marginBottom: "40px" }}>
           <h2 style={{ fontSize: "28px", fontWeight: 800, marginBottom: "8px" }}>
             {tab === "analysis" ? "Autonomous Road Diagnostics" : tab === "pothole" ? "Community Incident Reporting" : "Maintenance Insights & History"}
           </h2>
           <p style={{ color: "var(--text-dim)" }}>Using pixel-level segmentation and real-time object detection to monitor infrastructure health.</p>
        </div>

        {tab === "analysis" && <CrackAnalysisTab />}
        {tab === "pothole" && <PotholeTab />}
        {tab === "history" && <HistoryTab />}
      </main>

      <footer className="footer-branding">
        <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "0 24px" }}>
          <p style={{ marginBottom: "12px" }}>© 2026 DriveSafe AI Road Health Monitoring System</p>
          <div className="developer-card">
            <span style={{ fontWeight: 700, color: "var(--text)" }}>Paramveer Singh</span>
            <span style={{ margin: "0 12px", color: "var(--border-hi)" }}>|</span>
            <span style={{ color: "var(--cyan)", fontFamily: "var(--font-mono)" }}>+91 7658828271</span>
            <span style={{ margin: "0 12px", color: "var(--border-hi)" }}>|</span>
            <span style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>paramveercse@gmail.com</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

const root = createRoot(document.getElementById("root"));
root.render(<App />);
