import "react";
import { useState, useEffect } from "react";
import { MCQChallenge } from "../challenge/MCQChallenge.jsx";
import { useApi } from "../utils/api.js";

export function HistoryPanel() {
  const { makeRequest } = useApi();
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await makeRequest("my-history");
      // console.log(data);
      setHistory(data.Challenges || []);
    } catch (err) {
      setError("Failed to load history.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="loading">Loading history...</div>;
  }

  if (error) {
    return (
      <div className="error-message">
        <p>{error}</p>
        <button onClick={fetchHistory}>Retry</button>
      </div>
    );
  }

  const deleteHistoryItem = async (id) => {
    try {
      await makeRequest(`my-history/${id}`, { method: "DELETE" });
      setHistory(history.filter((item) => item.id !== id));
    } catch (err) {
      setError("Failed to delete history item.");
    }
  };

  const clearAllHistory = async () => {
    try {
      await makeRequest("my-history", { method: "DELETE" });
      setHistory([]);
    } catch (err) {
      setError("Failed to clear history.");
    }
  };

  return (
  <div className="history-panel">
    <h2>History</h2>
    {history.length > 0 && (
      <button className="clear-all-btn" onClick={clearAllHistory}>
        Clear All
      </button>
    )}
    {history.length === 0 ? (
      <p>No challenge history</p>
    ) : (
      <div className="history-list">
        {history.map((challenge) => (
          <div key={challenge.id} className="history-item">
            <MCQChallenge challenge={challenge} showExplanation />
            <button
              className="delete-btn"
              onClick={() => deleteHistoryItem(challenge.id)}
            >
              Delete
            </button>
          </div>
        ))}
      </div>
    )}
  </div>
);
}
