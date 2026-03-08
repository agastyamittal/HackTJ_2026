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
  const [selectedInitialTime, setSelectedInitialTime] = useState(0);
  const [matchFrames, setMatchFrames] = useState([]);
  const [toast, setToast] = useState(null);
  // trackInfo maps camera_id (number) -> {upload_id, timestamp_sec} from last tracking run
  const [trackInfo, setTrackInfo] = useState({});

  const handleResults = (results, scores, features) => {
    const ids = [...new Set(results.map((r) => r.camera_id))];
    setHighlightedCameraIds(ids);
    setCameraScores(scores || {});
    setQueryFeatures(features || []);
    setTrackInfo({});  // clear tracking state when a new search runs
  };

  const handleTrackResult = useCallback((res) => {
    if (!res.camera_scores) return;
    // Overlay tracking scores on top of existing camera scores
    setCameraScores((prev) => ({ ...prev, ...res.camera_scores }));
    // Store per-camera best timestamp + upload_id for when user clicks the pin
    const info = {};
    for (const [camIdStr, data] of Object.entries(res.camera_scores)) {
      info[Number(camIdStr)] = {
        upload_id:    data.best_upload_id,
        timestamp_sec: data.best_timestamp_sec,
      };
    }
    setTrackInfo(info);
  }, []);

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
      // If this camera has a tracking result, use it directly
      if (trackInfo[cam.id]) {
        const { upload_id, timestamp_sec } = trackInfo[cam.id];
        setSelectedUploadId(upload_id);
        setSelectedInitialTime(timestamp_sec);
        setMatchFrames([]);
        return;
      }

      const uploads = await getUploads();
      const match = uploads.find(
        (u) => u.camera_id === cam.id && u.status === "done"
      );
      if (match) {
        setSelectedUploadId(match.upload_id);
        setSelectedInitialTime(0);
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
              <VideoPlayer
                uploadId={selectedUploadId}
                initialTime={selectedInitialTime}
                matchFrames={matchFrames}
                onTrackResult={handleTrackResult}
              />
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
