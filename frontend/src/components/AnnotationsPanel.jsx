import React from "react";

const CLASS_COLORS = {
  person: "#fc8181",
  car: "#63b3ed",
  bus: "#f6ad55",
  truck: "#68d391",
};

function classColor(cls) {
  for (const key of Object.keys(CLASS_COLORS)) {
    if (cls.toLowerCase().includes(key)) return CLASS_COLORS[key];
  }
  let h = 0;
  for (const c of cls) h = (h * 31 + c.charCodeAt(0)) & 0xffffffff;
  const hue = Math.abs(h) % 360;
  return `hsl(${hue}, 65%, 65%)`;
}

export default function AnnotationsPanel({ detections, timestamp, onTrack, tracking, trackResult }) {
  return (
    <div className="annotations-panel">
      <div className="annotations-title">Detections</div>
      {timestamp !== undefined && (
        <div className="text-sm text-muted" style={{ marginBottom: 10 }}>
          {Math.floor(timestamp / 60)}:{String(Math.floor(timestamp % 60)).padStart(2, "0")}
        </div>
      )}
      {!detections || detections.length === 0 ? (
        <div className="text-sm text-muted">No detections at this frame.</div>
      ) : (
        detections.map((d, i) => (
          <div key={i} className="detection-item" style={{ flexDirection: "column", gap: 4 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span className="detection-class" style={{ color: classColor(d.class) }}>
                {d.class}
              </span>
              <span className="detection-conf">{(d.confidence * 100).toFixed(0)}%</span>
            </div>
            {d.attributes && d.attributes.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 3 }}>
                {d.attributes.map((attr, j) => {
                  const name = typeof attr === "object" ? attr.name : attr;
                  const conf = typeof attr === "object" ? attr.confidence : null;
                  return (
                    <span key={j} style={{
                      fontSize: 10, background: "#2d3748", color: "#cbd5e0",
                      borderRadius: 3, padding: "1px 5px", display: "inline-flex", alignItems: "center", gap: 3
                    }}>
                      {name}
                      {conf != null && (
                        <span style={{ color: "#718096", fontSize: 9 }}>
                          {(conf * 100).toFixed(0)}%
                        </span>
                      )}
                    </span>
                  );
                })}
              </div>
            )}
            {onTrack && d.class.toLowerCase().includes("person") && (
              <button
                className="btn btn-sm btn-ghost"
                onClick={() => onTrack(i)}
                disabled={tracking}
                style={{ fontSize: 10, padding: "2px 8px" }}
              >
                {tracking ? "Tracking…" : "Track across cameras"}
              </button>
            )}
          </div>
        ))
      )}
      {trackResult && trackResult.matches && trackResult.matches.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div className="annotations-title" style={{ marginBottom: 6 }}>Track Results</div>
          {trackResult.matches.slice(0, 5).map((m, i) => (
            <div key={i} className="detection-item" style={{ flexDirection: "column" }}>
              <span style={{ color: "#63b3ed", fontSize: 11, fontWeight: 600 }}>{m.camera_name}</span>
              <span style={{ color: "#a0aec0", fontSize: 11 }}>
                {Math.floor(m.timestamp_sec / 60)}:{String(Math.floor(m.timestamp_sec % 60)).padStart(2, "0")}
                {" · "}{(m.similarity_score * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
