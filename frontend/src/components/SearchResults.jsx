import React from "react";
import { thumbnailUrl } from "../api";

function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

export default function SearchResults({ results, onSelect }) {
  if (!results || results.length === 0) return null;

  return (
    <div className="search-results">
      {results.map((r, i) => {
        const classes = [...new Set(r.detections.map((d) => d.class))].join(", ");
        const rawAttrs = r.detections.flatMap((d) => d.attributes || []);
        const seen = new Set();
        const attrs = rawAttrs.filter((a) => {
          const key = typeof a === "object" ? a.name : a;
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        });
        return (
          <div
            key={i}
            className="result-card"
            onClick={() => onSelect && onSelect(r)}
          >
            <img
              className="result-thumb"
              src={thumbnailUrl(r.upload_id, r.frame_idx)}
              alt="frame"
              onError={(e) => { e.target.style.display = "none"; }}
            />
            <div className="result-info">
              <div className="result-camera">{r.camera_name}</div>
              <div className="result-ts">{formatTime(r.timestamp_sec)}</div>
              <div className="result-score">Score: {(r.similarity_score * 100).toFixed(1)}%</div>
              {classes && <div className="result-classes">{classes}</div>}
              {attrs.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 3, marginTop: 3 }}>
                  {attrs.map((a, j) => {
                    const name = typeof a === "object" ? a.name : a;
                    const conf = typeof a === "object" ? a.confidence : null;
                    return (
                      <span key={j} style={{
                        fontSize: 9, background: "#2d3748", color: "#a0aec0",
                        borderRadius: 3, padding: "1px 4px", display: "inline-flex", alignItems: "center", gap: 2
                      }}>
                        {name}
                        {conf != null && (
                          <span style={{ color: "#718096", fontSize: 8 }}>
                            {(conf * 100).toFixed(0)}%
                          </span>
                        )}
                      </span>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
