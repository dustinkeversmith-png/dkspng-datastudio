import React, { useEffect, useMemo, useRef, useState } from "react";
import Plot from "react-plotly.js";
import Plotly from "plotly.js-dist-min";

type SourceDefinition = {
  source_key: string;
  display_name: string;
  category: string;
  connector_type: string;
  source_url: string;
  notes?: string;
};

type Observation = {
  id: string;
  source_key: string;
  source_name: string;
  dataset_category: string;
  year: number | null;
  county: string | null;
  city: string | null;
  latitude: number | null;
  longitude: number | null;
  metric_name: string | null;
  metric_value: number | null;
  session_dataset_id?: string;
};

type Regions = {
  counties: string[];
  cities: string[];
  categories: string[];
};

const API_BASE = "http://127.0.0.1:8000";

const SESSION_STORAGE_KEY = "rds-viz-session-id";

function buildQuery(params: Record<string, string>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value.trim().length > 0) search.set(key, value);
  });
  return search.toString();
}

export default function App() {
  const [sources, setSources] = useState<SourceDefinition[]>([]);
  const [regions, setRegions] = useState<Regions>({ counties: [], cities: [], categories: [] });
  const [observations, setObservations] = useState<Observation[]>([]);
  const [sourceKey, setSourceKey] = useState("");
  const [county, setCounty] = useState("");
  const [yearMin, setYearMin] = useState("");
  const [yearMax, setYearMax] = useState("");
  const [status, setStatus] = useState("Ready.");
  const [analysis, setAnalysis] = useState<any>(null);
  const [modeling, setModeling] = useState<any>(null);
  const [comparison, setComparison] = useState<any>(null);
  const [sankey, setSankey] = useState<any>(null);


  const [latitude, setLatitude] = useState("45.5152");
  const [longitude, setLongitude] = useState("-122.6784");
  const [radiusKm, setRadiusKm] = useState("50");
  const [variables, setVariables] = useState("year,latitude,longitude,metric_value");
  const [trends, setTrends] = useState<any[]>([]);
  const [selectedCorrelation, setSelectedCorrelation] = useState<any>(null);

  const [selectedSourceKeys, setSelectedSourceKeys] = useState<string[]>([]);
  const [datasetComparison, setDatasetComparison] = useState<any>(null);

  const [sessionId, setSessionId] = useState("");
  const [useSessionContext, setUseSessionContext] = useState(false);
  const plotRefs = useRef<Record<string, any>>({});

  function bindPlotRef(key: string) {
    return (_figure: any, graphDiv: any) => {
      plotRefs.current[key] = graphDiv;
    };
  }

  async function saveChartImage(key: string, format: "png" | "svg") {
    const graphDiv = plotRefs.current[key];
    if (!graphDiv) {
      setStatus(`Chart '${key}' is not ready yet.`);
      return;
    }
    try {
      await Plotly.downloadImage(graphDiv, {
        format,
        filename: `rds_${key}`,
        width: 1400,
        height: 900,
        scale: 2,
      });
      setStatus(`Saved ${key}.${format}`);
    } catch (error) {
      setStatus(`Failed to save ${key}.${format}: ${String(error)}`);
    }
  }

  async function loadSources() {
    const response = await fetch(`${API_BASE}/sources`);
    setSources(await response.json());
  }

  async function loadRegions() {
    const response = await fetch(`${API_BASE}/regions`);
    setRegions(await response.json());
  }

  const filterQuery = buildQuery(
    useSessionContext && sessionId
      ? {
          session_id: sessionId,
          county,
          year_min: yearMin,
          year_max: yearMax,
          latitude,
          longitude,
          radius_km: radiusKm,
        }
      : {
          source_key: sourceKey,
          county,
          year_min: yearMin,
          year_max: yearMax,
          latitude,
          longitude,
          radius_km: radiusKm,
        }
  );

  async function loadObservations() {
    const query = buildQuery(
      useSessionContext && sessionId
        ? {
            session_id: sessionId,
            county,
            year_min: yearMin,
            year_max: yearMax,
            limit: "1000",
          }
        : {
            source_key: sourceKey,
            county,
            year_min: yearMin,
            year_max: yearMax,
            limit: "1000",
          }
    );

    setStatus("Loading observations...");
    const response = await fetch(`${API_BASE}/observations/query?${query}`);

    if (!response.ok) {
      setStatus(`Failed: ${response.status}`);
      return;
    }

    const rows = await response.json();
    setObservations(rows);
    setStatus(`Loaded ${rows.length} observations.`);
  }

  async function runAnalysis(kind: "correlation" | "regression" | "county-compare") {
    setStatus(`Running ${kind} analysis...`);
    const suffix = kind === "regression"
      ? `analysis/regression?${filterQuery}&x=year&y=metric_value`
      : `analysis/${kind}?${filterQuery}`;

    const response = await fetch(`${API_BASE}/${suffix}`);
    const result = await response.json();
    setAnalysis(result);
    setStatus(result.status === "success" ? `${kind} analysis complete.` : `${kind} failed.`);
  }

  async function runModel(kind: "risk-surface" | "spatial-interpolation" | "matrix-compare") {
    setStatus(`Running ${kind} model...`);
    const query = kind === "matrix-compare" ? filterQuery : `${filterQuery}&resolution=24`;

    const response = await fetch(`${API_BASE}/modeling/${kind}?${query}`);
    const result = await response.json();
    setModeling(result);
    setStatus(result.status === "success" ? `${kind} model complete.` : `${kind} failed.`);
  }

  async function buildSankey() {
    setStatus("Building Sankey diagram...");
    const response = await fetch(`${API_BASE}/comparison/sankey?${filterQuery}`);
    const result = await response.json();
    setSankey(result);
    setStatus(result.status === "success" ? "Sankey ready." : "Sankey failed.");
  }

  async function runCrossDomainCompare() {
    setStatus("Running cross-domain comparison...");
    const response = await fetch(`${API_BASE}/comparison/cross-domain?${filterQuery}`);
    const result = await response.json();
    setComparison(result);
    setStatus(result.status === "success" ? "Cross-domain comparison complete." : "Cross-domain comparison failed.");
  }

  async function ingestSelected() {
    if (!sourceKey) {
      setStatus("Choose a source first.");
      return;
    }

    setStatus(`Ingesting ${sourceKey}...`);
    const response = await fetch(`${API_BASE}/ingest/${sourceKey}`, { method: "POST" });
    const result = await response.json();

    setStatus(`${result.status}: read ${result.rows_read}, wrote ${result.rows_written}${result.error_message ? ` — ${result.error_message}` : ""}`);
    await loadRegions();
    await loadObservations();
  }

  async function loadDatasetTrends() {
    const response = await fetch(`${API_BASE}/trends/datasets?${filterQuery}`);
    setTrends(await response.json());
  }

  async function runSelectedCorrelation() {
    const query = `${filterQuery}&variables=${encodeURIComponent(variables)}`;
    const response = await fetch(`${API_BASE}/analysis/selected-correlation?${query}`);
    setSelectedCorrelation(await response.json());
  }

  async function compareSelectedDatasets() {
    const query =
      useSessionContext && sessionId
        ? buildQuery({
            session_id: sessionId,
            county,
            year_min: yearMin,
            year_max: yearMax,
            latitude,
            longitude,
            radius_km: radiusKm,
          })
        : buildQuery({
            source_keys: selectedSourceKeys.join(","),
            county,
            year_min: yearMin,
            year_max: yearMax,
            latitude,
            longitude,
            radius_km: radiusKm,
          });

    const response = await fetch(`${API_BASE}/comparison/datasets?${query}`);
    setDatasetComparison(await response.json());
  }

  async function createVisualizationSession() {
    setStatus("Creating visualization session...");
    const response = await fetch(`${API_BASE}/session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const data = await response.json();
    if (!response.ok) {
      setStatus(`Session create failed: ${response.status}`);
      return;
    }
    setSessionId(data.session_id);
    localStorage.setItem(SESSION_STORAGE_KEY, data.session_id);
    setUseSessionContext(true);
    setStatus(`Session ${data.session_id} — add datasets from checkboxes, then Apply Filter.`);
  }

  async function registerCheckedToSession() {
    if (!sessionId) {
      setStatus("Create a session first.");
      return;
    }
    if (selectedSourceKeys.length === 0) {
      setStatus("Select at least one source checkbox.");
      return;
    }
    setStatus("Registering datasets...");
    for (const key of selectedSourceKeys) {
      const datasetId = key.replace(/[^a-zA-Z0-9_-]/g, "_");
      const response = await fetch(`${API_BASE}/session/${sessionId}/datasets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_id: datasetId, source_key: key }),
      });
      if (!response.ok) {
        setStatus(`Register failed: ${response.status} ${await response.text()}`);
        return;
      }
    }
    setStatus(`Registered ${selectedSourceKeys.length} dataset(s) on session.`);
    await loadObservations();
  }

  useEffect(() => {
    const saved = localStorage.getItem(SESSION_STORAGE_KEY);
    if (saved) {
      setSessionId(saved);
    }
    loadSources();
    loadRegions();
    loadObservations();
  }, []);

  const spatialRows = useMemo(
    () => observations.filter((row) => row.latitude != null && row.longitude != null),
    [observations]
  );

  const countyCounts = useMemo(() => {
    const counts = new Map<string, number>();
    observations.forEach((row) => {
      const key = row.county || "Unknown";
      counts.set(key, (counts.get(key) || 0) + 1);
    });
    return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]);
  }, [observations]);

  const surface = modeling?.grid ? modeling : null;

  return (
    <main className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Phase 5</p>
          <h1>Regional Data Studio</h1>
          <p>Visualize, analyze, model, and compare regional datasets through Sankey and cross-domain workflows.</p>
        </div>
        <div className="hero-actions">
          <a className="button" href="/lab">Open Intake Lab</a>
          <a className="button" href={`${API_BASE}/exports/observations.csv?${filterQuery}`}>
            Export CSV
          </a>
        </div>
      </header>

      <section className="panel controls">
        <div className="session-bar">
          <label className="inline">
            <input
              type="checkbox"
              checked={useSessionContext}
              onChange={(e) => setUseSessionContext(e.target.checked)}
            />
            Use visualization session for queries & exports
          </label>
          <span className="session-id">
            Session: {sessionId || "(none)"}
          </span>
          <button type="button" onClick={createVisualizationSession}>
            New session
          </button>
          <button type="button" onClick={registerCheckedToSession}>
            Register checked sources
          </button>
        </div>
        <div className="dataset-checkboxes">
        {sources.map((source) => (
          <label key={source.source_key}>
            <input
              type="checkbox"
              checked={selectedSourceKeys.includes(source.source_key)}
              onChange={(event) => {
                if (event.target.checked) {
                  setSelectedSourceKeys([...selectedSourceKeys, source.source_key]);
                } else {
                  setSelectedSourceKeys(
                    selectedSourceKeys.filter((key) => key !== source.source_key)
                  );
                }
              }}
            />
            {source.display_name}
          </label>
        ))}
      </div>

        <label>
          Latitude
          <input value={latitude} onChange={(e) => setLatitude(e.target.value)} />
        </label>

        <label>
          Longitude
          <input value={longitude} onChange={(e) => setLongitude(e.target.value)} />
        </label>

        <label>
          Radius KM
          <input value={radiusKm} onChange={(e) => setRadiusKm(e.target.value)} />
        </label>

        <label>
          Correlation Variables
          <input
            value={variables}
            onChange={(e) => setVariables(e.target.value)}
            placeholder="year,latitude,longitude,metric_value"
          />
        </label>

        <label>
          County
          <select value={county} onChange={(event) => setCounty(event.target.value)}>
            <option value="">All counties</option>
            {regions.counties.map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        </label>

        <label>
          Year min
          <input value={yearMin} onChange={(event) => setYearMin(event.target.value)} placeholder="2020" />
        </label>

        <label>
          Year max
          <input value={yearMax} onChange={(event) => setYearMax(event.target.value)} placeholder="2026" />
        </label>

        <button onClick={loadObservations}>Apply Filter</button>
        <button onClick={ingestSelected}>Ingest Selected Source</button>
      </section>

      <section className="panel action-grid">
        <button onClick={() => runAnalysis("correlation")}>Run Correlation</button>
        <button onClick={() => runAnalysis("regression")}>Run Regression</button>
        <button onClick={() => runAnalysis("county-compare")}>Compare Counties</button>
        <button onClick={() => runModel("risk-surface")}>Run Risk Surface</button>
        <button onClick={() => runModel("spatial-interpolation")}>Run Interpolation</button>
        <button onClick={() => runModel("matrix-compare")}>Run Matrix Compare</button>
        <button onClick={buildSankey}>Build Sankey</button>
        <button onClick={runCrossDomainCompare}>Run Cross-Domain Compare</button>
        <button onClick={loadDatasetTrends}>Load Dataset Trends</button>
        <button onClick={runSelectedCorrelation}>Run 5-Variable Correlation</button>
        <button onClick={compareSelectedDatasets}>
          Compare Selected Datasets
        </button>
      </section>

      <p className="status">{status}</p>

      <section className="grid">
        <div className="panel">
          <h2>Scatter Plot</h2>
          <div className="action-grid">
            <button onClick={() => saveChartImage("scatter_plot", "png")}>Save PNG</button>
            <button onClick={() => saveChartImage("scatter_plot", "svg")}>Save SVG</button>
          </div>
          <Plot
            data={[{
              x: spatialRows.map((row) => row.longitude),
              y: spatialRows.map((row) => row.latitude),
              text: spatialRows.map((row) => `${row.county || ""} ${row.year || ""}`),
              mode: "markers",
              type: "scatter",
            }]}
            layout={{
              autosize: true,
              height: 360,
              margin: { t: 20, r: 20, b: 40, l: 50 },
              xaxis: { title: "Longitude" },
              yaxis: { title: "Latitude" },
            }}
            useResizeHandler
            style={{ width: "100%" }}
            onInitialized={bindPlotRef("scatter_plot")}
            onUpdate={bindPlotRef("scatter_plot")}
          />
        </div>

        <div className="panel">
          <h2>Comparison Chart</h2>
          <div className="action-grid">
            <button onClick={() => saveChartImage("comparison_chart", "png")}>Save PNG</button>
            <button onClick={() => saveChartImage("comparison_chart", "svg")}>Save SVG</button>
          </div>
          {datasetComparison?.datasets && (
          <Plot
            data={[
              {
                x: datasetComparison.datasets.map((d: any) => d.dataset_id || d.source_key),
                y: datasetComparison.datasets.map((d: any) => d.row_count),
                type: "bar",
                name: "Observation Count",
              },
              {
                x: datasetComparison.datasets.map((d: any) => d.dataset_id || d.source_key),
                y: datasetComparison.datasets.map((d: any) => d.metric_mean),
                type: "bar",
                name: "Metric Mean",
              },
            ]}
            layout={{
              height: 420,
              barmode: "group",
              title: "Dataset Comparison",
            }}
            style={{ width: "100%" }}
            onInitialized={bindPlotRef("comparison_chart")}
            onUpdate={bindPlotRef("comparison_chart")}
          />
        )}
        </div>

        <div className="panel">
          <h2>County Chart</h2>
          <div className="action-grid">
            <button onClick={() => saveChartImage("county_chart", "png")}>Save PNG</button>
            <button onClick={() => saveChartImage("county_chart", "svg")}>Save SVG</button>
          </div>
          <Plot
            data={[{
              x: countyCounts.map(([name]) => name),
              y: countyCounts.map(([, count]) => count),
              type: "bar",
            }]}
            layout={{
              autosize: true,
              height: 360,
              margin: { t: 20, r: 20, b: 80, l: 50 },
              yaxis: { title: "Observation Count" },
            }}
            useResizeHandler
            style={{ width: "100%" }}
            onInitialized={bindPlotRef("county_chart")}
            onUpdate={bindPlotRef("county_chart")}
          />
        </div>

        <div className="panel">

          <h2>Dataset Trends</h2>
          <div className="action-grid">
            <button onClick={() => saveChartImage("dataset_trends", "png")}>Save PNG</button>
            <button onClick={() => saveChartImage("dataset_trends", "svg")}>Save SVG</button>
          </div>
          <Plot
          data={[
            {
              x: trends.map((row) => row.year),
              y: trends.map((row) => row.mean),
              text: trends.map((row) => row.source_key),
              mode: "lines+markers",
              type: "scatter",
            },
          ]}
          layout={{
            height: 360,
            title: "Dataset Trends",
            xaxis: { title: "Year" },
            yaxis: { title: "Mean Metric Value" },
          }}
          style={{ width: "100%" }}
          onInitialized={bindPlotRef("dataset_trends")}
          onUpdate={bindPlotRef("dataset_trends")}
        />
        </div>

        <div className="panel">

          <h2>Selected Variable Correlation</h2>
          <div className="action-grid">
            <button onClick={() => saveChartImage("selected_correlation", "png")}>Save PNG</button>
            <button onClick={() => saveChartImage("selected_correlation", "svg")}>Save SVG</button>
          </div>
          {selectedCorrelation?.matrix && (
          <Plot
            data={[
              {
                z: selectedCorrelation.matrix,
                x: selectedCorrelation.variables,
                y: selectedCorrelation.variables,
                type: "heatmap",
              },
            ]}
            layout={{
              height: 420,
              title: "Selected Variable Correlation",
            }}
            style={{ width: "100%" }}
            onInitialized={bindPlotRef("selected_correlation")}
            onUpdate={bindPlotRef("selected_correlation")}
          />
        )}
        </div>

        <div className="panel">
          <h2>Risk / Interpolation Surface</h2>
          <div className="action-grid">
            <button onClick={() => saveChartImage("risk_surface", "png")}>Save PNG</button>
            <button onClick={() => saveChartImage("risk_surface", "svg")}>Save SVG</button>
          </div>
          {surface ? (
            <Plot
              data={[{
                z: surface.grid,
                x: surface.longitudes,
                y: surface.latitudes,
                type: "heatmap",
              }]}
              layout={{
                autosize: true,
                height: 360,
                margin: { t: 20, r: 20, b: 40, l: 50 },
                xaxis: { title: "Longitude" },
                yaxis: { title: "Latitude" },
              }}
              useResizeHandler
              style={{ width: "100%" }}
              onInitialized={bindPlotRef("risk_surface")}
              onUpdate={bindPlotRef("risk_surface")}
            />
          ) : (
            <p>Run Risk Surface or Interpolation to generate a heat map.</p>
          )}
        </div>

        <div className="panel">
          <h2>Sankey Diagram</h2>
          <div className="action-grid">
            <button onClick={() => saveChartImage("sankey_chart", "png")}>Save PNG</button>
            <button onClick={() => saveChartImage("sankey_chart", "svg")}>Save SVG</button>
          </div>
          {sankey?.labels?.length ? (
            <Plot
              data={[{
                type: "sankey",
                orientation: "h",
                node: {
                  label: sankey.labels,
                  pad: 15,
                  thickness: 15,
                },
                link: {
                  source: sankey.sources,
                  target: sankey.targets,
                  value: sankey.values,
                },
              }]}
              layout={{
                autosize: true,
                height: 420,
                margin: { t: 20, r: 20, b: 20, l: 20 },
              }}
              useResizeHandler
              style={{ width: "100%" }}
              onInitialized={bindPlotRef("sankey_chart")}
              onUpdate={bindPlotRef("sankey_chart")}
            />
          ) : (
            <p>Click Build Sankey to render source → category → county → metric flow.</p>
          )}
        </div>

        <div className="panel">
          <h2>Cross-Domain Comparison</h2>
          <pre className="json-block">{JSON.stringify(comparison, null, 2)}</pre>
        </div>

        <div className="panel">
          <h2>Analysis / Model JSON</h2>
          <pre className="json-block">{JSON.stringify({ analysis, modeling }, null, 2)}</pre>
        </div>
      </section>
    </main>
  );
}
