import React, { useState } from "react";
import MapView from "../components/MapView";

export default function MapPage() {
  const handleCameraClick = (cam) => {
    console.log("Camera clicked:", cam);
  };

  return (
    <div style={{ height: "calc(100vh - 48px)" }}>
      <MapView onCameraClick={handleCameraClick} />
    </div>
  );
}
