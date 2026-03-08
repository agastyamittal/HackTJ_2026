import React, { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import { getCameras } from "../api";
import "leaflet/dist/leaflet.css";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

const SHADOW_URL =
  "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png";
const COLOR_MARKER_BASE =
  "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img";

function colorIcon(color) {
  return new L.Icon({
    iconUrl: `${COLOR_MARKER_BASE}/marker-icon-${color}.png`,
    shadowUrl: SHADOW_URL,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });
}

const statusIcons = {
  green: colorIcon("green"),
  yellow: colorIcon("gold"),
  red: colorIcon("red"),
};

const defaultIcon = colorIcon("blue");

function FitBounds({ cameras }) {
  const map = useMap();

  useEffect(() => {
    if (!cameras.length) return;
    const bounds = L.latLngBounds(cameras.map((c) => [c.lat, c.lon]));
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
  }, [map, cameras]);

  return null;
}

export default function MapView({ onCameraClick, cameraScores = {} }) {
  const [cameras, setCameras] = useState([]);

  useEffect(() => {
    getCameras()
      .then((data) => setCameras(Array.isArray(data) ? data : []))
      .catch(() => setCameras([]));
  }, []);

  const parsedCameras = useMemo(() => {
    return cameras
      .map((c) => {
        const lat = Number(c.lat ?? c.latitude);
        const lon = Number(c.lon ?? c.lng ?? c.longitude);
        return { ...c, lat, lon };
      })
      .filter((c) => Number.isFinite(c.lat) && Number.isFinite(c.lon));
  }, [cameras]);

  const center =
    parsedCameras.length > 0
      ? [parsedCameras[0].lat, parsedCameras[0].lon]
      : [38.921894946382345, -77.23348312620747];

  return (
    <MapContainer center={center} zoom={16} style={{ height: "100vh", width: "100%" }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />

      {parsedCameras.length > 0 && <FitBounds cameras={parsedCameras} />}

      {parsedCameras.map((cam) => (
        <Marker
          key={cam.id}
          position={[cam.lat, cam.lon]}
          icon={statusIcons[cameraScores[String(cam.id)]?.status || cam.status] || defaultIcon}
          eventHandlers={{
            click: () => onCameraClick && onCameraClick(cam),
          }}
        >
          <Popup>
            <strong>{cam.name}</strong>
            <br />
            {cam.location}
            <br />
            {cam.lat.toFixed(5)}, {cam.lon.toFixed(5)}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
