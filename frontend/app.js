import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";

const API_BASE = `${location.origin}/api`;
const cx = (...xs) => xs.filter(Boolean).join(" ");

/* ─── SVG Icons ─── */
const Icons = {
  scan: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><line x1="7" y1="12" x2="17" y2="12"/></svg>,
  alert: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>,
  upload: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>,
  map: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>,
  zap: <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>,
  check: <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>,
  grid: <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>,
  activity: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
};

/* ─── Panel wrapper ─── */
function Panel({ title, icon, color = "blue", children, className = "" }) {
  const dotClass = color === "green" ? "green" : "";
  const cornerClass = color === "green" ? "panel-corner panel-corner-green" : "panel-corner";
  return (
    <div className={`panel ${cornerClass} h-full flex flex-col fade-in ${className}`}>
      <div className="section-label">
        <div className={`dot ${dotClass}`} />
        {icon && <span style={{ opacity: 0.6 }}>{icon}</span>}
        <span>{title}</span>
        <span style={{ marginLeft: "auto", opacity: 0.4, fontFamily: "DM Mono" }}>
          {new Date().toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
      <div className="flex-1" style={{ padding: "16px" }}>{children}</div>
    </div>
  );
}

/* ─── Stat card ─── */
function Stat({ label, value, accent = "blue" }) {
  const colors = { blue: "#00d4ff", green: "#00ffa3", red: "#ff4545", amber: "#ffb800" };
  return (
    <div className="stat-box">
      <div style={{ fontSize: "10px", fontFamily: "DM Mono", letterSpacing: "0.1em", color: "#5a6480", textTransform: "uppercase", marginBottom: "6px" }}>{label}</div>
      <div style={{ fontSize: "22px", fontWeight: 700, fontFamily: "DM Mono", color: colors[accent] || colors.blue, lineHeight: 1 }}>{value}</div>
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
    mapRef.current = window.L.map(divRef.current, { zoomControl: true }).setView(center, 12);
    window.L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: "&copy; OpenStreetMap &copy; CARTO",
    }).addTo(mapRef.current);
    layerRef.current = window.L.layerGroup().addTo(mapRef.current);
    const observer = new ResizeObserver(() => { if (mapRef.current) mapRef.current.invalidateSize(); });
    observer.observe(divRef.current);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    if (!layerRef.current || !mapRef.current) return;
    layerRef.current.clearLayers();
    const pts = points.filter((p) => typeof p.lat === "number" && typeof p.lon === "number");
    pts.forEach((p) => {
      const color = p.severity === "high" ? "#ff4545" : p.severity === "medium" ? "#ffb800" : "#00ffa3";
      const marker = window.L.circleMarker([p.lat, p.lon], { radius: 7, color, weight: 2, fillColor: color, fillOpacity: 0.85 });
      marker.bindPopup(
        `<div style="font-family:'Space Grotesk',sans-serif;font-size:12px;padding:4px 2px">
          <div style="font-family:'DM Mono',monospace;font-size:10px;letter-spacing:0.1em;color:#5a6480;text-transform:uppercase;margin-bottom:4px">Severity</div>
          <div style="font-weight:600;color:${color};font-size:14px">${(p.severity || "").toUpperCase()}</div>
          ${p.timestamp ? `<div style="font-size:10px;color:#5a6480;margin-top:4px;font-family:'DM Mono',monospace">${p.timestamp}</div>` : ""}
        </div>`
      );
      marker.addTo(layerRef.current);
    });
    if (pts.length > 0) mapRef.current.fitBounds(window.L.latLngBounds(pts.map((p) => [p.lat, p.lon])).pad(0.25));
  }, [points]);
  return <div ref={divRef} style={{ height: "400px", width: "100%", borderRadius: "8px", overflow: "hidden", border: "1px solid #1c2235" }} />;
}

/* ─── Bounding Box Canvas ─── */
function BoundingBoxCanvas({ imgSrc, detections }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const draw = () => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    const ctx = canvas.getContext("2d");
    const img = new Image();
    img.src = imgSrc;
    img.onload = () => {
      const cW = container.clientWidth, cH = container.clientHeight;
      const iR = img.width / img.height, cR = cW / cH;
      let rW, rH, oX, oY;
      if (iR > cR) { rW = cW; rH = cW / iR; oX = 0; oY = (cH - rH) / 2; }
      else { rH = cH; rW = cH * iR; oY = 0; oX = (cW - rW) / 2; }
      canvas.width = cW; canvas.height = cH;
      ctx.clearRect(0, 0, cW, cH);
      if (detections?.length > 0) {
        const sX = rW / img.width, sY = rH / img.height;
        detections.forEach((det) => {
          const [x1, y1, x2, y2] = det.bbox;
          const rx1 = x1 * sX + oX, ry1 = y1 * sY + oY, rx2 = x2 * sX + oX, ry2 = y2 * sY + oY;
          ctx.shadowColor = "#00d4ff"; ctx.shadowBlur = 8;
          ctx.strokeStyle = "#00d4ff"; ctx.lineWidth = 1.5; ctx.setLineDash([6, 3]);
          ctx.strokeRect(rx1, ry1, rx2 - rx1, ry2 - ry1);
          ctx.setLineDash([]); ctx.shadowBlur = 0;
          const cs = 10;
          ctx.strokeStyle = "#00ffa3"; ctx.lineWidth = 2;
          [[rx1, ry1, 1, 1], [rx2, ry1, -1, 1], [rx2, ry2, -1, -1], [rx1, ry2, 1, -1]].forEach(([cx2, cy, dx, dy]) => {
            ctx.beginPath(); ctx.moveTo(cx2, cy + dy * cs); ctx.lineTo(cx2, cy); ctx.lineTo(cx2 + dx * cs, cy); ctx.stroke();
          });
          const text = `${det.class}  ${(det.confidence * 100).toFixed(0)}%`;
          ctx.font = "500 11px 'DM Mono', monospace";
          const tw = ctx.measureText(text).width;
          ctx.fillStyle = "rgba(0,15,25,0.85)";
          ctx.fillRect(rx1, ry1 - 24, tw + 16, 22);
          ctx.strokeStyle = "rgba(0,212,255,0.4)"; ctx.lineWidth = 1;
          ctx.strokeRect(rx1, ry1 - 24, tw + 16, 22);
          ctx.fillStyle = "#00d4ff"; ctx.fillText(text, rx1 + 8, ry1 - 8);
        });
      }
    };
  };
  useEffect(() => { draw(); window.addEventListener("resize", draw); return () => window.removeEventListener("resize", draw); }, [imgSrc, detections]);
  return (
    <div ref={containerRef} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }}>
      <canvas ref={canvasRef} style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }} />
    </div>
  );
}

/* ─── Image Overlay ─── */
function ImageOverlay({ file, maskBase64, detections }) {
  const [imgSrc, setImgSrc] = useState(null);
  const [scanning, setScanning] = useState(false);
  useEffect(() => { if (!file) { setImgSrc(null); return; } const u = URL.createObjectURL(file); setImgSrc(u); return () => URL.revokeObjectURL(u); }, [file]);
  useEffect(() => { if (detections) { setScanning(true); setTimeout(() => setScanning(false), 3000); } }, [detections]);

  if (!imgSrc) {
    return (
      <div style={{ height: "400px", display: "flex", alignItems: "center", justifyContent: "center", border: "1px dashed #1c2235", borderRadius: "8px", background: "rgba(0,212,255,0.01)" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "#1c2235", marginBottom: "12px", display: "flex", justifyContent: "center" }}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
          </div>
          <div style={{ fontFamily: "DM Mono", fontSize: "11px", color: "#2a3550", letterSpacing: "0.08em", textTransform: "uppercase" }}>Awaiting input</div>
          <div style={{ fontSize: "12px", color: "#333d55", marginTop: "4px" }}>Upload an image to begin analysis</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", minHeight: "400px" }}>
      <div className="scan-container" style={{ position: "relative", borderRadius: "8px", overflow: "hidden", background: "#000", border: "1px solid #1c2235", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div className="mono-badge" style={{ position: "absolute", top: "10px", left: "10px", zIndex: 10 }}>INPUT + DETECTION</div>
        {scanning && <div className="scan-line" />}
        <img src={imgSrc} alt="uploaded" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "contain" }} />
        <BoundingBoxCanvas imgSrc={imgSrc} detections={detections} />
      </div>
      {maskBase64 ? (
        <div style={{ position: "relative", borderRadius: "8px", overflow: "hidden", background: "#000", border: "1px solid #1c2235", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div className="mono-badge" style={{ position: "absolute", top: "10px", left: "10px", zIndex: 10 }}>SEGMENTATION MASK</div>
          <img src={maskBase64} alt="mask" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "contain", pointerEvents: "none" }} />
        </div>
      ) : (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", border: "1px dashed #1c2235", borderRadius: "8px", background: "rgba(0,0,0,0.2)" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#2a3550", letterSpacing: "0.1em", textTransform: "uppercase" }}>Mask pending</div>
            <div style={{ display: "flex", justifyContent: "center", marginTop: "8px" }}>
              <div style={{ width: "20px", height: "20px", border: "2px solid #1c2235", borderTopColor: "#00d4ff", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Crack Analysis Tab ─── */
function CrackAnalysisApp() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [maskBase64, setMaskBase64] = useState(null);
  const [detections, setDetections] = useState(null);
  const [crackPercent, setCrackPercent] = useState(0);

  async function onAnalyze(e) {
    e.preventDefault();
    if (!file) return setError("Select an image first.");
    setLoading(true); setError(""); setMaskBase64(null); setDetections(null);
    const fd = new FormData(); fd.append("file", file);
    try {
      const segRes = await fetch(`${API_BASE}/predict-segmentation`, { method: "POST", body: fd });
      if (segRes.ok) { const d = await segRes.json(); setMaskBase64(d.mask_base64); setCrackPercent(d.crack_percentage || 0); }
      else throw new Error("Segmentation failed");
      const detRes = await fetch(`${API_BASE}/detect-rdd`, { method: "POST", body: fd });
      if (detRes.ok) { const d = await detRes.json(); setDetections(d.detections); }
      else throw new Error("Detection failed");
    } catch (err) { setError(err?.message || "Analysis failed."); }
    finally { setLoading(false); }
  }

  const severityColor = crackPercent > 15 ? "#ff4545" : crackPercent > 5 ? "#ffb800" : "#00ffa3";

  return (
    <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: "16px" }} className="slide-up">
      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        <Panel title="Image Input" icon={Icons.upload} color="blue">
          <form onSubmit={onAnalyze}>
            <div className="upload-zone">
              <div style={{ display: "flex", justifyContent: "center", color: "#2a3550", marginBottom: "12px" }}>{Icons.upload}</div>
              <label style={{ cursor: "pointer" }}>
                <span style={{ fontSize: "13px", fontWeight: 600, color: "#00d4ff" }}>Choose file</span>
                <input type="file" style={{ display: "none" }} onChange={(e) => setFile(e.target.files?.[0] || null)} accept="image/*" />
              </label>
              <div style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#2a3550", marginTop: "8px", letterSpacing: "0.06em", wordBreak: "break-all", maxWidth: "200px", margin: "8px auto 0" }}>
                {file ? file.name : "PNG · JPG · WEBP — 10MB"}
              </div>
            </div>
            {error && <div style={{ marginTop: "12px", padding: "10px 12px", background: "rgba(255,69,69,0.06)", border: "1px solid rgba(255,69,69,0.2)", borderRadius: "6px", fontSize: "12px", color: "#ff4545", fontWeight: 500 }}>{error}</div>}
            <button type="submit" disabled={loading || !file} className={cx("btn-primary", "")} style={{ marginTop: "14px" }}>
              {loading ? <><div className="spinner" /><span>Processing…</span></> : <>{Icons.zap}<span>Run Analysis</span></>}
            </button>
          </form>
        </Panel>

        {detections && (
          <Panel title="Analysis Results" icon={Icons.activity} color="blue">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "14px" }}>
              <Stat label="Objects" value={detections.length} accent="blue" />
              <Stat label="Crack density" value={`${crackPercent.toFixed(1)}%`} accent={crackPercent > 5 ? "red" : "green"} />
            </div>
            <div style={{ marginBottom: "14px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                <span style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#5a6480", textTransform: "uppercase", letterSpacing: "0.08em" }}>Surface Damage</span>
                <span style={{ fontFamily: "DM Mono", fontSize: "10px", color: severityColor }}>{crackPercent.toFixed(1)}%</span>
              </div>
              <div className="status-bar"><div className="status-bar-fill" style={{ width: `${Math.min(crackPercent * 4, 100)}%`, background: severityColor }} /></div>
            </div>
            {detections.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {detections.map((det, i) => (
                  <div key={i} className="det-row" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 10px", borderRadius: "6px", background: "rgba(0,0,0,0.3)", border: "1px solid #1c2235" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <div style={{ width: "4px", height: "4px", borderRadius: "50%", background: "#00d4ff" }} />
                      <span style={{ fontFamily: "DM Mono", fontSize: "11px", color: "#00d4ff" }}>{det.class}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <div className="status-bar" style={{ width: "60px" }}><div className="status-bar-fill" style={{ width: `${det.confidence * 100}%`, background: "#00d4ff" }} /></div>
                      <span style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#5a6480", minWidth: "28px", textAlign: "right" }}>{(det.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        )}
      </div>

      <Panel title="Visual Analysis" icon={Icons.grid} color="blue">
        <ImageOverlay file={file} maskBase64={maskBase64} detections={detections} />
      </Panel>
    </div>
  );
}

/* ─── Pothole Reporting Tab ─── */
function PotholeReportingApp() {
  const [file, setFile] = useState(null);
  const [loc, setLoc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [potholes, setPotholes] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/clear-potholes`, { method: "DELETE" }).then(() => fetchPotholes());
  }, []);

  async function fetchPotholes() {
    try { const res = await fetch(`${API_BASE}/get-potholes`); if (res.ok) { const d = await res.json(); setPotholes(d.data || []); } } catch (e) { console.error(e); }
  }

  function captureLocation(e) {
    e.preventDefault();
    if (loc) { setLoc({ lat: loc.lat + (Math.random()*0.002-0.001), lon: loc.lon + (Math.random()*0.002-0.001) }); setMessage(null); return; }
    if (navigator.geolocation) { navigator.geolocation.getCurrentPosition((pos) => setLoc({ lat: pos.coords.latitude, lon: pos.coords.longitude }), () => alert("Enable GPS access.")); }
    else alert("Geolocation not supported.");
  }

  async function onReport(e) {
    e.preventDefault();
    if (!file) return setMessage({ type: "error", text: "Select an image." });
    if (!loc) return setMessage({ type: "error", text: "Capture location first." });
    setLoading(true); setMessage(null);
    const fd = new FormData(); fd.append("file", file); fd.append("lat", loc.lat); fd.append("lon", loc.lon);
    try {
      const res = await fetch(`${API_BASE}/report-pothole`, { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      if (data.status === "duplicate") { setMessage({ type: "warn", text: data.message }); }
      else {
        const sev = data.severity?.toUpperCase();
        const pct = data.severity_percent ?? 0;
        setMessage({ type: "success", text: "Reported successfully", severity: sev, percent: pct });
      }
      fetchPotholes();
    } catch (err) { setMessage({ type: "error", text: err.message }); }
    finally { setLoading(false); }
  }

  const sevA = { HIGH: { c: "#ff4545", bg: "rgba(255,69,69,0.08)", b: "rgba(255,69,69,0.2)" }, MEDIUM: { c: "#ffb800", bg: "rgba(255,184,0,0.08)", b: "rgba(255,184,0,0.2)" }, LOW: { c: "#00ffa3", bg: "rgba(0,255,163,0.08)", b: "rgba(0,255,163,0.2)" } };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: "16px" }} className="slide-up">
      <div>
        <Panel title="Incident Report" icon={Icons.alert} color="green">
          <form onSubmit={onReport}>
            <div className="upload-zone green" style={{ marginBottom: "14px" }}>
              <div style={{ display: "flex", justifyContent: "center", color: "#2a3550", marginBottom: "12px" }}>{Icons.upload}</div>
              <label style={{ cursor: "pointer" }}>
                <span style={{ fontSize: "13px", fontWeight: 600, color: "#00ffa3" }}>Capture Photo</span>
                <input type="file" style={{ display: "none" }} onChange={(e) => setFile(e.target.files?.[0] || null)} accept="image/*" capture="environment" />
              </label>
              <div style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#2a3550", marginTop: "8px", letterSpacing: "0.06em" }}>{file ? file.name : "Camera · Gallery"}</div>
            </div>

            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 12px", background: "rgba(0,0,0,0.3)", border: "1px solid #1c2235", borderRadius: "8px", marginBottom: "14px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ color: loc ? "#00ffa3" : "#2a3550" }}>{Icons.map}</span>
                {loc ? <span style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#00ffa3", letterSpacing: "0.05em" }}>{loc.lat.toFixed(4)}, {loc.lon.toFixed(4)}</span>
                     : <span style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#2a3550", letterSpacing: "0.05em" }}>NO LOCATION</span>}
              </div>
              <button type="button" onClick={captureLocation} className="gps-btn">{loc ? "Refresh" : "Get GPS"}</button>
            </div>

            {message && (
              <div style={{ marginBottom: "14px" }}>
                {message.severity ? (
                  <div style={{ padding: "12px", borderRadius: "8px", background: sevA[message.severity]?.bg, border: `1px solid ${sevA[message.severity]?.b}` }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
                      <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: sevA[message.severity]?.c }} />
                      <span style={{ fontSize: "12px", fontWeight: 600, color: sevA[message.severity]?.c }}>{message.severity} SEVERITY</span>
                      <span style={{ marginLeft: "auto", fontFamily: "DM Mono", fontSize: "11px", color: "#5a6480" }}>{message.percent}%</span>
                    </div>
                    <div className="status-bar"><div className="status-bar-fill" style={{ width: `${Math.min(message.percent, 100)}%`, background: sevA[message.severity]?.c }} /></div>
                    <div style={{ fontSize: "11px", color: "#5a6480", marginTop: "8px" }}>{message.text}</div>
                  </div>
                ) : (
                  <div style={{ padding: "10px 12px", borderRadius: "6px", fontSize: "12px", fontWeight: 500, background: message.type === "error" ? "rgba(255,69,69,0.06)" : "rgba(255,184,0,0.06)", border: `1px solid ${message.type === "error" ? "rgba(255,69,69,0.2)" : "rgba(255,184,0,0.2)"}`, color: message.type === "error" ? "#ff4545" : "#ffb800" }}>{message.text}</div>
                )}
              </div>
            )}

            <button type="submit" disabled={loading || !file || !loc} className="btn-primary btn-green">
              {loading ? <><div className="spinner" /><span>Sending…</span></> : <>{Icons.zap}<span>Send Report</span></>}
            </button>
          </form>

          <div style={{ marginTop: "20px", paddingTop: "14px", borderTop: "1px solid #1c2235" }}>
            <div style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#2a3550", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "10px" }}>Severity Legend</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {[["HIGH", "#ff4545"], ["MEDIUM", "#ffb800"], ["LOW", "#00ffa3"]].map(([label, color]) => (
                <div key={label} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: color, flexShrink: 0 }} />
                  <span style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#5a6480", letterSpacing: "0.06em" }}>{label}</span>
                  <div className="status-bar" style={{ flex: 1 }}><div className="status-bar-fill" style={{ width: label === "HIGH" ? "85%" : label === "MEDIUM" ? "55%" : "25%", background: color }} /></div>
                </div>
              ))}
            </div>
          </div>
        </Panel>
      </div>

      <Panel title="Incident Map" icon={Icons.map} color="green">
        <Map points={potholes} center={loc ? [loc.lat, loc.lon] : [28.6139, 77.209]} />
        <div style={{ marginTop: "12px", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", background: "rgba(0,0,0,0.2)", borderRadius: "6px", border: "1px solid #1c2235" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            {[["Critical", "#ff4545"], ["Medium", "#ffb800"], ["Low", "#00ffa3"]].map(([label, color]) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: color }} />
                <span style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#5a6480", letterSpacing: "0.06em" }}>{label}</span>
              </div>
            ))}
          </div>
          <div style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#2a3550" }}>{potholes.length} INCIDENT{potholes.length !== 1 ? "S" : ""}</div>
        </div>
      </Panel>
    </div>
  );
}

/* ─── Root App ─── */
function App() {
  const [tab, setTab] = useState("analysis");

  return (
    <div style={{ minHeight: "100vh", background: "transparent" }}>
      {/* Header */}
      <header style={{ position: "sticky", top: 0, zIndex: 50, borderBottom: "1px solid #1c2235", background: "rgba(5,7,9,0.85)", backdropFilter: "blur(20px)", WebkitBackdropFilter: "blur(20px)" }}>
        <div style={{ maxWidth: "1400px", margin: "0 auto", padding: "0 24px", height: "60px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
            <div style={{ position: "relative" }}>
              <div className="logo-ring" />
              <div style={{ width: "34px", height: "34px", borderRadius: "8px", background: "linear-gradient(135deg, #00d4ff, #00ffa3)", display: "flex", alignItems: "center", justifyContent: "center", position: "relative", zIndex: 1 }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#000" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              </div>
            </div>
            <div>
              <div style={{ fontFamily: "Syne", fontSize: "15px", fontWeight: 800, color: "#e8edf8", letterSpacing: "-0.01em" }}>DriveSafe</div>
              <div style={{ fontFamily: "DM Mono", fontSize: "9px", color: "#2a3550", letterSpacing: "0.12em", textTransform: "uppercase", marginTop: "1px" }}>Autonomous Road Intelligence</div>
            </div>
          </div>

          <nav style={{ display: "flex", alignItems: "center", gap: "6px", padding: "5px", background: "rgba(0,0,0,0.4)", borderRadius: "10px", border: "1px solid #1c2235" }}>
            <button onClick={() => setTab("analysis")} className={cx("nav-tab", tab === "analysis" ? "active-blue" : "")}>{Icons.scan} Crack Analysis</button>
            <button onClick={() => setTab("pothole")} className={cx("nav-tab", tab === "pothole" ? "active-green" : "")}>{Icons.alert} Pothole Reporter</button>
          </nav>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#00ffa3", animation: "pulseDot 2s ease-in-out infinite", boxShadow: "0 0 8px rgba(0,255,163,0.5)" }} />
            <span style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#2a3550", letterSpacing: "0.1em", textTransform: "uppercase" }}>System Online</span>
          </div>
        </div>
      </header>

      {/* Sub-header */}
      <div style={{ borderBottom: "1px solid #0d1120", background: "rgba(0,0,0,0.3)", padding: "8px 24px" }}>
        <div style={{ maxWidth: "1400px", margin: "0 auto", display: "flex", alignItems: "center", gap: "20px" }}>
          <span style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#1c2235", letterSpacing: "0.08em" }}>{tab === "analysis" ? "CRACK SEGMENTATION + RDD DETECTION" : "GEOLOCATION + SEVERITY CLASSIFICATION"}</span>
          <span style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#1c2235" }}>·</span>
          <span style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#1c2235", letterSpacing: "0.08em" }}>{tab === "analysis" ? "" : "ResNet50 · K-MEANS"}</span>
        </div>
      </div>

      {/* Content */}
      <main style={{ maxWidth: "1400px", margin: "0 auto", padding: "24px" }}>
        <div style={tab === "analysis" ? {} : { display: "none" }}><CrackAnalysisApp /></div>
        <div style={tab === "pothole" ? {} : { position: "absolute", visibility: "hidden", height: 0, overflow: "hidden" }}><PotholeReportingApp /></div>
      </main>

      {/* Footer */}
      <footer style={{ borderTop: "1px solid #0d1120", padding: "16px 24px", marginTop: "24px" }}>
        <div style={{ maxWidth: "1400px", margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#1c2235", letterSpacing: "0.08em" }}></span>
          <span style={{ fontFamily: "DM Mono", fontSize: "10px", color: "#1c2235", letterSpacing: "0.08em" }}></span>
        </div>
      </footer>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
