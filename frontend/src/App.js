import React from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import MapPage from "./pages/MapPage";
import CameraView from "./pages/CameraView";
import "./styles/main.css";

export default function App() {
  return (
    <BrowserRouter>
      <nav className="navbar">
        <span className="navbar-brand">
          <img src="/LOGO LETS GO.jpg" alt="Argus" className="navbar-logo" />
          Argus
        </span>
        <div className="navbar-links">
          <Link to="/">Map</Link>
          <Link to="/feeds">Camera Feeds</Link>
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<MapPage />} />
        <Route path="/feeds" element={<Dashboard />} />
        <Route path="/camera/:uploadId" element={<CameraView />} />
      </Routes>
    </BrowserRouter>
  );
}
