import React from "react";
import { useNavigate } from "react-router-dom";
import { thumbnailUrl } from "../api";

export default function CameraCard({ upload, highlighted }) {
  const navigate = useNavigate();

  const handleClick = () => {
    if (upload.status === "done") {
      navigate(`/camera/${upload.upload_id}`);
    }
  };

  const statusClass =
    upload.status === "done"
      ? "status-done"
      : upload.status === "error"
      ? "status-error"
      : "status-processing";

  const statusLabel =
    upload.status === "done"
      ? "Ready"
      : upload.status === "error"
      ? "Error"
      : "Processing…";

  return (
    <div
      className={`camera-card${highlighted ? " highlighted" : ""}`}
      onClick={handleClick}
    >
      {upload.status === "done" ? (
        <img
          className="camera-card-thumb"
          src={thumbnailUrl(upload.upload_id, 0)}
          alt={upload.camera_name}
          onError={(e) => { e.target.style.display = "none"; }}
        />
      ) : (
        <div className="camera-card-thumb-placeholder">
          {upload.status === "processing" ? (
            <span className="spinner" />
          ) : (
            "No preview"
          )}
        </div>
      )}
      <div className="camera-card-body">
        <div className="camera-card-name">{upload.camera_name}</div>
        <div className="camera-card-location">{upload.filename}</div>
        <div className={`camera-card-status ${statusClass}`}>{statusLabel}</div>
      </div>
    </div>
  );
}
