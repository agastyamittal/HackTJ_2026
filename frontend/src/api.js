import axios from "axios";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
});

export const getCameras = () => api.get("/api/cameras").then((r) => r.data);

export const getUploads = () => api.get("/api/videos").then((r) => r.data);

export const uploadVideo = (file, cameraId) => {
  const form = new FormData();
  form.append("file", file);
  form.append("camera_id", cameraId);
  return api.post("/api/videos", form).then((r) => r.data);
};

export const pollStatus = (uploadId) =>
  api.get(`/api/videos/${uploadId}/status`).then((r) => r.data);

export const search = (query, topK = 20, cameraIds = null) =>
  api
    .post("/api/search", { query, top_k: topK, camera_ids: cameraIds })
    .then((r) => r.data);

export const getFramesIndex = (uploadId) =>
  api.get(`/api/frames/${uploadId}/all`).then((r) => r.data);

export const getDetections = (uploadId, frameIdx) =>
  api
    .get(`/api/frames/${uploadId}/${frameIdx}/detections`)
    .then((r) => r.data);

export const thumbnailUrl = (uploadId, frameIdx) =>
  `${api.defaults.baseURL}/api/frames/${uploadId}/${frameIdx}/thumbnail`;

export const videoStreamUrl = (uploadId) =>
  `${api.defaults.baseURL}/api/video/${uploadId}/clip`;

export const trackPerson = (uploadId, frameIdx, detectionIndex) =>
  api
    .post("/api/track", { upload_id: uploadId, frame_idx: frameIdx, detection_index: detectionIndex })
    .then((r) => r.data);

export const getQueryMatches = (uploadId, queryFeatures) =>
  api
    .post(`/api/frames/${uploadId}/query_matches`, { query_features: queryFeatures })
    .then((r) => r.data);
