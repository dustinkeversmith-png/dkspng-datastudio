import React, { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

type SourceDefinition = {
  source_key: string;
  display_name: string;
  category: string;
  connector_type: string;
  source_url: string;
  notes?: string;
};

const DEFAULT_COMMAND = `{
  "type": "exclude_columns",
  "columns": ["raw_properties_json"]
}`;

export default function ApiIntakeLab() {
  const [status, setStatus] = useState("Ready.");
  const [sources, setSources] = useState<SourceDefinition[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [datasetId, setDatasetId] = useState("dataset_a");
  const [selectedSourceKey, setSelectedSourceKey] = useState("");
  const [bufferCommands, setBufferCommands] = useState<any[]>([]);
  const [sessionSummary, setSessionSummary] = useState<any>(null);
  const [sessionPreview, setSessionPreview] = useState<any>(null);
  const [bufferPreview, setBufferPreview] = useState<any>(null);
  const [commandJson, setCommandJson] = useState(DEFAULT_COMMAND);

  const [newSource, setNewSource] = useState({
    source_key: "",
    display_name: "",
    category: "custom",
    connector_type: "csv",
    source_url: "",
    notes: "",
  });

  async function loadSources() {
    const res = await fetch(`${API_BASE}/sources`);
    const data = await res.json();
    setSources(data);
    if (!selectedSourceKey && data.length > 0) {
      setSelectedSourceKey(data[0].source_key);
    }
  }

  async function createSource() {
    setStatus("Saving source definition...");
    const body = {
      ...newSource,
      latitude_fields: ["latitude", "lat", "y"],
      longitude_fields: ["longitude", "lon", "lng", "x"],
      year_fields: ["year", "fire_year", "incident_year"],
      county_fields: ["county", "county_name"],
    };
    const res = await fetch(`${API_BASE}/sources`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      setStatus(`Source save failed: ${res.status} ${await res.text()}`);
      return;
    }
    setStatus("Source saved.");
    await loadSources();
  }

  async function createSession() {
    const res = await fetch(`${API_BASE}/session`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    const data = await res.json();
    if (!res.ok) {
      setStatus(`Session create failed: ${res.status}`);
      return;
    }
    setSessionId(data.session_id);
    setSessionSummary(data);
    setStatus(`Session created: ${data.session_id}`);
  }

  async function addDatasetToSession() {
    if (!sessionId) {
      setStatus("Create or enter a session id first.");
      return;
    }
    const res = await fetch(`${API_BASE}/session/${sessionId}/datasets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataset_id: datasetId, source_key: selectedSourceKey }),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus(`AddDataset failed: ${res.status} ${JSON.stringify(data)}`);
      return;
    }
    setSessionSummary(data);
    setStatus(`Dataset '${datasetId}' added.`);
  }

  async function loadBuffer() {
    if (!sessionId) return;
    const res = await fetch(`${API_BASE}/session/${sessionId}/buffer`);
    const data = await res.json();
    if (res.ok) {
      setBufferCommands(data.commands || []);
    }
  }

  async function pushCommand() {
    if (!sessionId) {
      setStatus("Set session id first.");
      return;
    }
    let parsed: any;
    try {
      parsed = JSON.parse(commandJson);
    } catch {
      setStatus("Command JSON is invalid.");
      return;
    }
    const res = await fetch(`${API_BASE}/session/${sessionId}/buffer/commands`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: parsed }),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus(`Push command failed: ${res.status} ${JSON.stringify(data)}`);
      return;
    }
    setSessionSummary(data);
    await loadBuffer();
    setStatus("Command buffered.");
  }

  async function clearBuffer() {
    if (!sessionId) return;
    const res = await fetch(`${API_BASE}/session/${sessionId}/buffer`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok) {
      setStatus(`Clear failed: ${res.status}`);
      return;
    }
    setSessionSummary(data);
    setBufferCommands([]);
    setStatus("Buffer cleared.");
  }

  async function applyBuffer() {
    if (!sessionId) return;
    const res = await fetch(`${API_BASE}/session/${sessionId}/buffer/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ clear_after_apply: true }),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus(`Apply failed: ${res.status}`);
      return;
    }
    setSessionSummary(data);
    await loadBuffer();
    setStatus("Buffer applied to pipeline.");
  }

  async function previewSession() {
    if (!sessionId) return;
    const res = await fetch(`${API_BASE}/session/${sessionId}/preview?limit=50`);
    const data = await res.json();
    if (!res.ok) {
      setStatus(`Session preview failed: ${res.status}`);
      return;
    }
    setSessionPreview(data);
    setStatus(`Session preview rows: ${data.row_count}`);
  }

  async function previewBuffer() {
    if (!sessionId) return;
    const res = await fetch(`${API_BASE}/session/${sessionId}/buffer/preview?limit=50`);
    const data = await res.json();
    if (!res.ok) {
      setStatus(`Buffer preview failed: ${res.status}`);
      return;
    }
    setBufferPreview(data);
    setStatus(`Buffer preview rows: ${data.row_count}`);
  }

  useEffect(() => {
    loadSources();
  }, []);

  return (
    <main className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Lab</p>
          <h1>Natural API / Dataset Intake Lab</h1>
          <p>Test source registry upserts, session datasets, and command-buffer manipulation endpoints.</p>
        </div>
        <a className="button" href="/">
          Back to Dashboard
        </a>
      </header>

      <p className="status">{status}</p>

      <section className="panel lab-grid">
        <div>
          <h2>1) Add Source To Registry</h2>
          <label>Source Key<input value={newSource.source_key} onChange={(e) => setNewSource({ ...newSource, source_key: e.target.value })} /></label>
          <label>Display Name<input value={newSource.display_name} onChange={(e) => setNewSource({ ...newSource, display_name: e.target.value })} /></label>
          <label>Category<input value={newSource.category} onChange={(e) => setNewSource({ ...newSource, category: e.target.value })} /></label>
          <label>Connector Type<input value={newSource.connector_type} onChange={(e) => setNewSource({ ...newSource, connector_type: e.target.value })} /></label>
          <label>Source URL<input value={newSource.source_url} onChange={(e) => setNewSource({ ...newSource, source_url: e.target.value })} /></label>
          <label>Notes<input value={newSource.notes} onChange={(e) => setNewSource({ ...newSource, notes: e.target.value })} /></label>
          <button onClick={createSource}>Save Source</button>
        </div>

        <div>
          <h2>2) Session + Dataset Binding</h2>
          <div className="action-grid">
            <button onClick={createSession}>Create Session</button>
            <button onClick={previewSession}>Preview Session Rows</button>
          </div>
          <label>Session ID<input value={sessionId} onChange={(e) => setSessionId(e.target.value)} /></label>
          <label>Dataset ID<input value={datasetId} onChange={(e) => setDatasetId(e.target.value)} /></label>
          <label>
            Source Key
            <select value={selectedSourceKey} onChange={(e) => setSelectedSourceKey(e.target.value)}>
              {sources.map((s) => (
                <option key={s.source_key} value={s.source_key}>{s.source_key}</option>
              ))}
            </select>
          </label>
          <button onClick={addDatasetToSession}>AddDataset</button>
        </div>
      </section>

      <section className="panel lab-grid">
        <div>
          <h2>3) Data Manipulation Buffer</h2>
          <div className="action-grid">
            <button onClick={loadBuffer}>Load Buffer</button>
            <button onClick={pushCommand}>Push Command</button>
            <button onClick={previewBuffer}>Preview Buffer Result</button>
            <button onClick={applyBuffer}>Apply Buffer To Pipeline</button>
            <button onClick={clearBuffer}>Clear Buffer</button>
          </div>
          <label>Command JSON<textarea className="lab-textarea" value={commandJson} onChange={(e) => setCommandJson(e.target.value)} /></label>
        </div>
        <div>
          <h2>Buffer Commands</h2>
          <pre className="json-block">{JSON.stringify(bufferCommands, null, 2)}</pre>
        </div>
      </section>

      <section className="grid">
        <div className="panel">
          <h2>Session Summary</h2>
          <pre className="json-block">{JSON.stringify(sessionSummary, null, 2)}</pre>
        </div>
        <div className="panel">
          <h2>Session Preview</h2>
          <pre className="json-block">{JSON.stringify(sessionPreview, null, 2)}</pre>
        </div>
        <div className="panel">
          <h2>Buffer Preview</h2>
          <pre className="json-block">{JSON.stringify(bufferPreview, null, 2)}</pre>
        </div>
        <div className="panel">
          <h2>Registry Sources</h2>
          <pre className="json-block">{JSON.stringify(sources, null, 2)}</pre>
        </div>
      </section>
    </main>
  );
}
