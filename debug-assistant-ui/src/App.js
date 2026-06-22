import { useState } from "react";
import axios from "axios";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

const API_URL = "http://localhost:8002";

const styles = {
  app: {
    backgroundColor: "#0d1117",
    minHeight: "100vh",
    color: "#e6edf3",
    fontFamily: "'Segoe UI', system-ui, sans-serif",
    padding: "24px",
  },
  header: {
    textAlign: "center",
    marginBottom: "32px",
  },
  title: {
    fontSize: "28px",
    fontWeight: "700",
    color: "#58a6ff",
    letterSpacing: "-0.5px",
  },
  subtitle: {
    color: "#8b949e",
    fontSize: "14px",
    marginTop: "4px",
  },
  searchBar: {
    display: "flex",
    gap: "12px",
    marginBottom: "32px",
    maxWidth: "800px",
    margin: "0 auto 32px auto",
  },
  input: {
    flex: 1,
    backgroundColor: "#161b22",
    border: "1px solid #30363d",
    borderRadius: "8px",
    padding: "12px 16px",
    color: "#e6edf3",
    fontSize: "15px",
    outline: "none",
  },
  button: {
    backgroundColor: "#238636",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    padding: "12px 24px",
    fontSize: "15px",
    fontWeight: "600",
    cursor: "pointer",
  },
  buttonDisabled: {
    backgroundColor: "#21262d",
    color: "#8b949e",
    border: "none",
    borderRadius: "8px",
    padding: "12px 24px",
    fontSize: "15px",
    fontWeight: "600",
    cursor: "not-allowed",
  },
  followUp: {
    backgroundColor: "#161b22",
    border: "1px solid #f0883e",
    borderRadius: "8px",
    padding: "20px",
    maxWidth: "800px",
    margin: "0 auto",
    color: "#f0883e",
    fontSize: "15px",
  },
  panels: {
    display: "grid",
    gridTemplateColumns: "1fr",
    gap: "16px",
    maxWidth: "900px",
    margin: "0 auto",
  },
  tldrPanel: {
    backgroundColor: "#161b22",
    border: "1px solid #238636",
    borderRadius: "8px",
    padding: "20px",
  },
  tldrLabel: {
    fontSize: "11px",
    fontWeight: "700",
    letterSpacing: "1px",
    color: "#3fb950",
    marginBottom: "8px",
    textTransform: "uppercase",
  },
  tldrText: {
    fontSize: "18px",
    fontWeight: "600",
    color: "#e6edf3",
    lineHeight: "1.5",
  },
  explanationPanel: {
    backgroundColor: "#161b22",
    border: "1px solid #30363d",
    borderRadius: "8px",
    padding: "20px",
  },
  panelLabel: {
    fontSize: "11px",
    fontWeight: "700",
    letterSpacing: "1px",
    color: "#8b949e",
    marginBottom: "12px",
    textTransform: "uppercase",
  },
  explanationText: {
    fontSize: "14px",
    lineHeight: "1.7",
    color: "#c9d1d9",
    whiteSpace: "pre-wrap",
  },
  codePanel: {
    backgroundColor: "#161b22",
    border: "1px solid #30363d",
    borderRadius: "8px",
    padding: "20px",
  },
  citationsPanel: {
    backgroundColor: "#161b22",
    border: "1px solid #30363d",
    borderRadius: "8px",
    padding: "20px",
  },
  citationBadge: {
    display: "inline-block",
    backgroundColor: "#21262d",
    border: "1px solid #30363d",
    borderRadius: "6px",
    padding: "6px 12px",
    fontSize: "12px",
    color: "#58a6ff",
    marginRight: "8px",
    marginBottom: "8px",
    fontFamily: "monospace",
    textDecoration: "none",
    cursor: "pointer",
  },
  citationSubject: {
    color: "#8b949e",
    fontSize: "12px",
    marginLeft: "4px",
  },
  timing: {
    textAlign: "center",
    color: "#8b949e",
    fontSize: "12px",
    marginTop: "16px",
  },
  thinking: {
    textAlign: "center",
    padding: "40px",
    color: "#58a6ff",
    fontSize: "15px",
  },
  negationNote: {
    backgroundColor: "#161b22",
    border: "1px solid #30363d",
    borderRadius: "8px",
    padding: "12px 16px",
    fontSize: "13px",
    color: "#8b949e",
    maxWidth: "900px",
    margin: "0 auto 16px auto",
  }
};

export default function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAsk = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const response = await axios.get(`${API_URL}/ask`, {
        params: { q: query },
        timeout: 120000,
      });
      setResult(response.data);

      if (response.data.confidence === "low") {
        setQuery(query + " ");
      }
    } catch (err) {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleAsk();
  };

  return (
    <div style={styles.app}>
      <div style={styles.header}>
        <div style={styles.title}>⚡ Debug Assistant</div>
        <div style={styles.subtitle}>
          Search historical bug fixes using natural language
        </div>
      </div>

      <div style={styles.searchBar}>
        <input
          style={styles.input}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe the bug, crash, or error..."
          disabled={loading}
        />
        <button
          style={loading ? styles.buttonDisabled : styles.button}
          onClick={handleAsk}
          disabled={loading}
        >
          {loading ? "Thinking..." : "Ask AI"}
        </button>
      </div>

      {loading && (
        <div style={styles.thinking}>
          ⚡ Searching and generating answer...
        </div>
      )}

      {error && (
        <div style={{ ...styles.followUp, borderColor: "#f85149", color: "#f85149" }}>
          {error}
        </div>
      )}

      {result && result.confidence === "low" && (
        <div style={styles.followUp}>
          <strong>Need more details:</strong> {result.follow_up}
          <div style={{ marginTop: "8px", fontSize: "13px", color: "#8b949e" }}>
            Add more detail to your query above and press Ask AI again.
          </div>
        </div>
      )}

      {result && result.confidence === "high" && (
        <div style={styles.panels}>

          {result.negations && result.negations.length > 0 && (
            <div style={styles.negationNote}>
              Excluded from results: {result.negations.join(", ")}
            </div>
          )}

          {result.tldr && (
            <div style={styles.tldrPanel}>
              <div style={styles.tldrLabel}>TL;DR</div>
              <div style={styles.tldrText}>{result.tldr}</div>
            </div>
          )}

          {result.explanation && (
            <div style={styles.explanationPanel}>
              <div style={styles.panelLabel}>Explanation</div>
              <div style={styles.explanationText}>{result.explanation}</div>
            </div>
          )}

          {result.code && (
            <div style={styles.codePanel}>
              <div style={styles.panelLabel}>Code Fix</div>
              <SyntaxHighlighter
                language="diff"
                style={vscDarkPlus}
                customStyle={{
                  borderRadius: "6px",
                  fontSize: "13px",
                  margin: 0,
                }}
              >
                {result.code}
              </SyntaxHighlighter>
            </div>
          )}

          {result.citations && result.citations.length > 0 && (
            <div style={styles.citationsPanel}>
              <div style={styles.panelLabel}>Citations</div>
              {result.citations.map((c, i) => (
                <div key={i} style={{ marginBottom: "4px" }}>
                  <a
                    href={`https://github.com/pandas-dev/pandas/commit/${c.commit}`}
                    target="_blank"
                    rel="noreferrer"
                    style={styles.citationBadge}
                  >
                    {c.commit}
                  </a>
                  <span style={styles.citationSubject}>{c.subject}</span>
                </div>
              ))}
            </div>
          )}

          <div style={styles.timing}>
            Response time: {result.time_taken}s
          </div>

        </div>
      )}
    </div>
  );
}