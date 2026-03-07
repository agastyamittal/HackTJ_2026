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

function FitBounds({ cameras }) {
  const map = useMap();

  useEffect(() => {
    if (!cameras.length) return;
    const bounds = L.latLngBounds(cameras.map((c) => [c.lat, c.lon]));
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
  }, [map, cameras]);

  return null;
}

export default function MapView({ onCameraClick }) {
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
