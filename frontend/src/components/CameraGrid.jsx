import React, { useEffect, useState, useCallback } from "react";
import { getUploads } from "../api";
import CameraCard from "./CameraCard";

export const sessionUploadIds = new Set();

export default function CameraGrid({ highlightedUploadIds }) {
  const [uploads, setUploads] = useState([]);

  const refresh = useCallback(async () => {
    if (sessionUploadIds.size === 0) return;
    try {
      const data = await getUploads();
      setUploads(data.filter((u) => sessionUploadIds.has(u.upload_id)));
    } catch {
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 3000);
    return () => clearInterval(id);
  }, [refresh]);

  if (uploads.length === 0) {
    return (
      <div className="text-muted text-sm" style={{ padding: "20px" }}>
        No videos uploaded yet. Use the upload bar above to add footage.
      </div>
    );
  }

  return (
    <div className="camera-grid">
      {uploads.map((u) => (
        <CameraCard
          key={u.upload_id}
          upload={u}
          highlighted={highlightedUploadIds?.includes(u.upload_id)}
        />
      ))}
    </div>
  );
}
