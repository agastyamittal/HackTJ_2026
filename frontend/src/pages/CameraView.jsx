import React, { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import VideoPlayer from "../components/VideoPlayer";
import { pollStatus } from "../api";

export default function CameraView() {
  const { uploadId } = useParams();
  const [searchParams] = useSearchParams();
  const initialTime = parseFloat(searchParams.get("t") || "0");
  const [status, setStatus] = useState(null);

  useEffect(() => {
    if (!uploadId) return;
    const check = async () => {
      try {
        const data = await pollStatus(uploadId);
        setStatus(data.status);
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

  return <VideoPlayer uploadId={uploadId} initialTime={initialTime} />;
}
