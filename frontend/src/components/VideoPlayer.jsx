import React, { useRef, useEffect, useState, useCallback } from "react";
import { getFramesIndex, getDetections, videoStreamUrl, trackPerson } from "../api";
import AnnotationsPanel from "./AnnotationsPanel";
import Timeline from "./Timeline";

const CLASS_COLORS = {
  person: "#fc8181",
  car: "#63b3ed",
  bus: "#f6ad55",
  truck: "#68d391",
};

function classColor(cls) {
  for (const key of Object.keys(CLASS_COLORS)) {
    if (cls.toLowerCase().includes(key)) return CLASS_COLORS[key];
  }
  let h = 0;
  for (const c of cls) h = (h * 31 + c.charCodeAt(0)) & 0xffffffff;
  return `hsl(${Math.abs(h) % 360}, 65%, 65%)`;
}

export default function VideoPlayer({ uploadId, initialTime = 0, matchFrames }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [detections, setDetections] = useState([]);
  const [framesIndex, setFramesIndex] = useState([]);
  const [trackResult, setTrackResult] = useState(null);
  const [tracking, setTracking] = useState(false);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (!uploadId) return;
    getFramesIndex(uploadId)
      .then((data) => setFramesIndex(data.frames || []))
      .catch(() => {});
  }, [uploadId]);

  useEffect(() => {
    if (videoRef.current && initialTime) {
      videoRef.current.currentTime = initialTime;
    }
  }, [initialTime]);

  const nearestFrame = useCallback(
    (time) => {
      if (!framesIndex.length) return null;
      let best = framesIndex[0];
      let bestDiff = Math.abs(framesIndex[0].timestamp_sec - time);
      for (const f of framesIndex) {
        const diff = Math.abs(f.timestamp_sec - time);
        if (diff < bestDiff) {
          bestDiff = diff;
          best = f;
        }
      }
      return best;
    },
    [framesIndex]
  );

  const drawBoxes = useCallback((dets) => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;
    const { videoWidth: vw, videoHeight: vh } = video;
    if (!vw || !vh) return;
    canvas.width = video.clientWidth;
    canvas.height = video.clientHeight;
    const scaleX = canvas.width / vw;
    const scaleY = canvas.height / vh;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const d of dets) {
      const [x1n, y1n, x2n, y2n] = d.bbox_norm;
      const x = x1n * vw * scaleX;
      const y = y1n * vh * scaleY;
      const w = (x2n - x1n) * vw * scaleX;
      const h = (y2n - y1n) * vh * scaleY;
      const color = classColor(d.class);
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, w, h);
      ctx.fillStyle = color;
      ctx.font = "12px sans-serif";
      const label = `${d.class} ${(d.confidence * 100).toFixed(0)}%`;
      const tw = ctx.measureText(label).width + 6;
      ctx.fillRect(x, y - 16, tw, 16);
      ctx.fillStyle = "#000";
      ctx.fillText(label, x + 3, y - 3);
    }
  }, []);

  const handleTimeUpdate = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    const t = video.currentTime;
    setCurrentTime(t);
    const frame = nearestFrame(t);
    if (!frame) return;
    getDetections(uploadId, frame.frame_idx)
      .then((data) => {
        setDetections(data.detections || []);
        drawBoxes(data.detections || []);
      })
      .catch(() => {});
  }, [uploadId, nearestFrame, drawBoxes]);

  const handleTrack = async (detIdx) => {
    const frame = nearestFrame(currentTime);
    if (!frame) return;
    setTracking(true);
    try {
      const res = await trackPerson(uploadId, frame.frame_idx, detIdx);
      setTrackResult(res);
    } catch {
      alert("Tracking failed");
    } finally {
      setTracking(false);
    }
  };

  const handleSeek = (sec) => {
    if (videoRef.current) videoRef.current.currentTime = sec;
  };

  const togglePlayPause = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      video.play();
      setPaused(false);
    } else {
      video.pause();
      setPaused(true);
    }
  };

  return (
    <div className="camera-view-layout">
      <div className="video-panel">
        <video
          ref={videoRef}
          src={videoStreamUrl(uploadId)}
          autoPlay
          muted
          playsInline
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={() => setDuration(videoRef.current?.duration || 0)}
          className="video-panel-video"
        />
        <canvas ref={canvasRef} />
        <button className="video-pause-btn" onClick={togglePlayPause}>
          {paused ? "▶" : "⏸"}
        </button>
      </div>

      <AnnotationsPanel
        detections={detections}
        timestamp={currentTime}
        onTrack={handleTrack}
        tracking={tracking}
        trackResult={trackResult}
      />

      <Timeline
        duration={duration}
        currentTime={currentTime}
        matchFrames={matchFrames}
        onSeek={handleSeek}
      />
    </div>
  );
}
