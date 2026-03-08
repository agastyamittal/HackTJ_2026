import React, { useState, useEffect, useCallback } from "react";
import MapView from "../components/MapView";
import ChatPanel from "../components/ChatPanel";
import VideoPlayer from "../components/VideoPlayer";
import { getUploads, getQueryMatches } from "../api";

export default function MapPage() {
  const [highlightedCameraIds, setHighlightedCameraIds] = useState([]);
  const [cameraScores, setCameraScores] = useState({});
  const [queryFeatures, setQueryFeatures] = useState([]);
  const [selectedUploadId, setSelectedUploadId] = useState(null);
  const [matchFrames, setMatchFrames] = useState([]);
  const [toast, setToast] = useState(null);

  const handleResults = (results, scores, features) => {
    const ids = [...new Set(results.map((r) => r.camera_id))];
    setHighlightedCameraIds(ids);
    setCameraScores(scores || {});
    setQueryFeatures(features || []);
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
        // Fetch per-frame query matches if a search has been performed
        if (queryFeatures.length > 0) {
          try {
            const frames = await getQueryMatches(match.upload_id, queryFeatures);
            setMatchFrames(frames);
          } catch {
            setMatchFrames([]);
          }
        } else {
          setMatchFrames([]);
        }
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
              <VideoPlayer uploadId={selectedUploadId} matchFrames={matchFrames} />
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
