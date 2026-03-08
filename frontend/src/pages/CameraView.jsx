import React, { useEffect, useState, useCallback } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import VideoPlayer from "../components/VideoPlayer";
import { pollStatus, getQueryMatches, thumbnailUrl } from "../api";

function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

export default function CameraView() {
  const { uploadId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const initialTime = parseFloat(searchParams.get("t") || "0");
  const [status, setStatus] = useState(null);
  const [matchFrames, setMatchFrames] = useState([]);
  const [trackMatches, setTrackMatches] = useState([]);

  useEffect(() => {
    if (!uploadId) return;
    const check = async () => {
      try {
        const data = await pollStatus(uploadId);
        setStatus(data.status);
        if (data.status === "done") {
          const stored = sessionStorage.getItem("queryFeatures");
          if (stored) {
            const features = JSON.parse(stored);
            if (features.length > 0) {
              try {
                const frames = await getQueryMatches(uploadId, features);
                setMatchFrames(frames);
              } catch {
                setMatchFrames([]);
              }
            }
          }
        }
      } catch {
        setStatus("error");
      }
    };
    check();
  }, [uploadId]);

  const handleTrackResult = useCallback((res) => {
    if (!res.matches?.length) return;
    // Deduplicate: one entry per camera (best combined_score)
    const seen = new Set();
    const deduped = [];
    for (const m of res.matches) {
      if (!seen.has(m.camera_id)) {
        seen.add(m.camera_id);
        deduped.push(m);
      }
    }
    setTrackMatches(deduped.slice(0, 5));
  }, []);

  if (status === null) {
    return (
      <div className="page" style={{ alignItems: "center", justifyContent: "center" }}>
        <span className="spinner" />
      </div>
    );
  }

  if (status === "processing") {
    return (
      <div className="page" style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 12 }}>
        <span className="spinner" />
        <span className="text-muted">Video is still being processed…</span>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="page" style={{ alignItems: "center", justifyContent: "center" }}>
        <span style={{ color: "#fc8181" }}>Processing failed for this upload.</span>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden" }}>
      <VideoPlayer
        uploadId={uploadId}
        initialTime={initialTime}
        matchFrames={matchFrames}
        onTrackResult={handleTrackResult}
      />
      {trackMatches.length > 0 && (
        <div style={{
          background: "#1a202c", borderTop: "1px solid #2d3748",
          padding: "10px 16px", flexShrink: 0,
        }}>
          <div style={{ fontSize: 11, color: "#718096", marginBottom: 8 }}>
            Spotted in {trackMatches.length} other camera{trackMatches.length > 1 ? "s" : ""}
          </div>
          <div style={{ display: "flex", gap: 10, overflowX: "auto" }}>
            {trackMatches.map((m, i) => (
              <div
                key={i}
                onClick={() => navigate(`/camera/${m.upload_id}?t=${m.timestamp_sec}`)}
                style={{
                  cursor: "pointer", flexShrink: 0, width: 120,
                  background: "#2d3748", borderRadius: 6, overflow: "hidden",
                  border: "1px solid #4a5568",
                }}
              >
                <img
                  src={thumbnailUrl(m.upload_id, m.frame_idx)}
                  alt={m.camera_name}
                  style={{ width: "100%", height: 68, objectFit: "cover", display: "block" }}
                  onError={(e) => { e.target.style.display = "none"; }}
                />
                <div style={{ padding: "4px 6px" }}>
                  <div style={{ fontSize: 10, color: "#e2e8f0", fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {m.camera_name}
                  </div>
                  <div style={{ fontSize: 10, color: "#a0aec0" }}>
                    {formatTime(m.timestamp_sec)} · {Math.round(m.combined_score * 100)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
