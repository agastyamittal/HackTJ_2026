import React, { useState, useEffect, useCallback } from "react";
import MapView from "../components/MapView";
import ChatPanel from "../components/ChatPanel";
import VideoPlayer from "../components/VideoPlayer";
import { getUploads } from "../api";

export default function MapPage() {
  const [highlightedCameraIds, setHighlightedCameraIds] = useState([]);
  const [cameraScores, setCameraScores] = useState({});
  const [selectedUploadId, setSelectedUploadId] = useState(null);
  const [toast, setToast] = useState(null);

  const handleResults = (results, scores) => {
    const ids = [...new Set(results.map((r) => r.camera_id))];
    setHighlightedCameraIds(ids);
    setCameraScores(scores || {});
  };

  const showToast = useCallback((msg) => {
    setToast(msg);
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(timer);
  }, [toast]);

  const handleCameraClick = async (cam) => {
    try {
      const uploads = await getUploads();
      const match = uploads.find(
        (u) => u.camera_id === cam.id && u.status === "done"
      );
      if (match) {
        setSelectedUploadId(match.upload_id);
      } else {
        showToast(`No video available for ${cam.name}`);
      }
    } catch {
      showToast("Failed to load video feeds");
    }
  };

  return (
    <div className="page">
      <div className="sidebar">
        <ChatPanel onResultsChange={handleResults} />
      </div>
      <div style={{ flex: 1, position: "relative" }}>
        <MapView
          highlightedCameraIds={highlightedCameraIds}
          cameraScores={cameraScores}
          onCameraClick={handleCameraClick}
        />
        {selectedUploadId && (
          <>
            <div
              className="map-video-backdrop"
              onClick={() => setSelectedUploadId(null)}
            />
            <div className="map-video-overlay">
              <button
                className="map-video-overlay-close"
                onClick={() => setSelectedUploadId(null)}
              >
                ✕
              </button>
              <VideoPlayer uploadId={selectedUploadId} />
            </div>
          </>
        )}
        {toast && (
          <div className="map-toast">{toast}</div>
        )}
      </div>
    </div>
  );
}
