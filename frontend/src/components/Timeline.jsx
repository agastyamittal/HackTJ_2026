import React, { useRef } from "react";

function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

const STATUS_COLORS = {
  green:  "#68d391",
  yellow: "#f6e05e",
  red:    "#fc8181",
};

export default function Timeline({ duration, currentTime, matchFrames, onSeek }) {
  const barRef = useRef(null);

  const handleBarClick = (e) => {
    if (!barRef.current || !duration) return;
    const rect = barRef.current.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    onSeek && onSeek(Math.max(0, Math.min(duration, ratio * duration)));
  };

  const progress = duration ? (currentTime / duration) * 100 : 0;

  return (
    <div className="timeline-panel">
      <div
        ref={barRef}
        className="timeline-bar"
        onClick={handleBarClick}
        title="Click to seek"
      >
        <div className="timeline-progress" style={{ width: `${progress}%` }} />
        {matchFrames &&
          duration &&
          matchFrames.map((f, i) => {
            const pct = (f.timestamp_sec / duration) * 100;
            const color = STATUS_COLORS[f.status] || STATUS_COLORS.yellow;
            return (
              <div
                key={i}
                className="timeline-marker"
                style={{ left: `${pct}%`, background: color, borderColor: color }}
                title={`${f.status} match (${Math.round(f.best_ratio * 100)}%) at ${formatTime(f.timestamp_sec)}${f.matched?.length ? " — " + f.matched.join(", ") : ""}`}
                onClick={(e) => {
                  e.stopPropagation();
                  onSeek && onSeek(f.timestamp_sec);
                }}
              />
            );
          })}
      </div>
      <div className="timeline-ts">
        <span>{formatTime(currentTime)}</span>
        <span>{formatTime(duration || 0)}</span>
      </div>
    </div>
  );
}
