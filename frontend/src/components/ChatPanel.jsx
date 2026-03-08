import React, { useState } from "react";
import { search } from "../api";

export default function ChatPanel({ onResultsChange }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [features, setFeatures] = useState([]);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await search(query.trim());
      const queryFeatures = data.query_features || [];
      setFeatures(queryFeatures);
      setSearched(true);
      // Persist so CameraView can pick up features after navigation
      sessionStorage.setItem("queryFeatures", JSON.stringify(queryFeatures));
      if (onResultsChange) onResultsChange(data.results || [], data.camera_scores || {}, queryFeatures);
    } catch (err) {
      setError("Search failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="sidebar-title">AI Search</div>
      <form className="chat-input-area" onSubmit={handleSearch}>
        <div className="chat-input-row">
          <input
            className="chat-input"
            placeholder='e.g. "person in red hoodie"'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn" type="submit" disabled={loading}>
            {loading ? <span className="spinner" /> : "Search"}
          </button>
        </div>
        {error && <div className="text-sm mt-2" style={{ color: "#fc8181" }}>{error}</div>}
      </form>
      {searched && !loading && !error && (
        <div style={{ padding: "10px 0", fontSize: 12, color: "#a0aec0" }}>
          {features.length > 0 ? (
            <>
              <div style={{ marginBottom: 6, color: "#718096" }}>Scanning for:</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {features.map((f, i) => (
                  <span key={i} style={{
                    background: "#2d3748", color: "#cbd5e0",
                    borderRadius: 3, padding: "2px 6px", fontSize: 11
                  }}>{f}</span>
                ))}
              </div>
              <div style={{ marginTop: 8, color: "#718096" }}>Map updated — green = strong match.</div>
            </>
          ) : (
            <div style={{ color: "#718096" }}>No structured features found. Map not updated.</div>
          )}
        </div>
      )}
      {!searched && (
        <div className="search-status">Enter a description to search footage.</div>
      )}
    </>
  );
}
