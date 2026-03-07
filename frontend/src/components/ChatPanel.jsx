import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { search } from "../api";
import SearchResults from "./SearchResults";

export default function ChatPanel({ highlightedCameraIds, onResultsChange }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await search(query.trim());
      setResults(data.results || []);
      if (onResultsChange) onResultsChange(data.results || []);
    } catch (err) {
      setError("Search failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (result) => {
    navigate(`/camera/${result.upload_id}?t=${result.timestamp_sec}`);
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
        {!loading && results.length > 0 && (
          <div className="text-sm text-muted mt-2">{results.length} result(s)</div>
        )}
      </form>
      <SearchResults results={results} onSelect={handleSelect} />
      {!loading && results.length === 0 && !error && (
        <div className="search-status">Enter a description to search footage.</div>
      )}
    </>
  );
}
