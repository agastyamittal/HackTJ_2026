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
            </div>
          </div>
        );
      })}
    </div>
  );
}
