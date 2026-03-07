import React, { useEffect, useRef, useState } from "react";
import ChatPanel from "../components/ChatPanel";
import CameraGrid, { sessionUploadIds } from "../components/CameraGrid";
import { getCameras, uploadVideo } from "../api";

export default function Dashboard() {
  const [cameras, setCameras] = useState([]);
  const [selectedCameraId, setSelectedCameraId] = useState("");
  const [uploading, setUploading] = useState(false);
  const [highlightedUploadIds, setHighlightedUploadIds] = useState([]);
  const fileInputRef = useRef(null);

  useEffect(() => {
    getCameras().then((cams) => {
      setCameras(cams);
      if (cams.length > 0) setSelectedCameraId(cams[0].id);
    });
  }, []);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file || !selectedCameraId) return;
    setUploading(true);
    try {
      const result = await uploadVideo(file, selectedCameraId);
      sessionUploadIds.add(result.upload_id);
    } catch {
      alert("Upload failed. Is the backend running?");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleResults = (results) => {
    const ids = [...new Set(results.map((r) => r.upload_id))];
    setHighlightedUploadIds(ids);
  };

  return (
    <div className="page">
      <div className="sidebar">
        <ChatPanel onResultsChange={handleResults} />
      </div>

      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div className="upload-bar">
          <span className="text-muted text-sm">Camera:</span>
          <select
            value={selectedCameraId}
            onChange={(e) => setSelectedCameraId(Number(e.target.value))}
          >
            {cameras.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*"
            style={{ display: "none" }}
            onChange={handleFileChange}
          />
          <button
            className="btn"
            disabled={uploading || !selectedCameraId}
            onClick={() => fileInputRef.current && fileInputRef.current.click()}
          >
            {uploading ? "Uploading…" : "Upload Video"}
          </button>
          <span className="text-muted text-sm">
            Processing may take 30s–2min depending on video length.
          </span>
        </div>

        <div className="main-content">
          <div className="section-header">
            <span className="section-title">Camera Feeds</span>
          </div>
          <CameraGrid highlightedUploadIds={highlightedUploadIds} />
        </div>
      </div>
    </div>
  );
}
