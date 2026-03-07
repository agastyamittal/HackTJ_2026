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
        <span className="navbar-brand">Sentinal</span>
        <div className="navbar-links">
          <Link to="/">Dashboard</Link>
          <Link to="/map">Map</Link>
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="/camera/:uploadId" element={<CameraView />} />
      </Routes>
    </BrowserRouter>
  );
}
