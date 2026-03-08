import React, { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import VideoPlayer from "../components/VideoPlayer";
import { pollStatus, getQueryMatches } from "../api";

export default function CameraView() {
  const { uploadId } = useParams();
  const [searchParams] = useSearchParams();
  const initialTime = parseFloat(searchParams.get("t") || "0");
  const [status, setStatus] = useState(null);
  const [matchFrames, setMatchFrames] = useState([]);

  useEffect(() => {
    if (!uploadId) return;
    const check = async () => {
      try {
        const data = await pollStatus(uploadId);
        setStatus(data.status);
        if (data.status === "done") {
          // Load query matches from last search (stored by ChatPanel)
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

  return <VideoPlayer uploadId={uploadId} initialTime={initialTime} matchFrames={matchFrames} />;
}
