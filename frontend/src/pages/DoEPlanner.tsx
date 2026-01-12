import React, { useEffect, useMemo, useReducer, useState } from 'react';
import { Beaker, Play, Save, BarChart3, TrendingUp } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const DOE_API_BASE = `${API_BASE_URL}/api/v1/doe`;

// Types
interface FactorSpec {
  name: string;
  type: 'continuous' | 'categorical';
  low: number;
  high: number;
  unit?: string;
}

interface DesignRow {
  run: number;
  [key: string]: number | string;
}

interface RunResult {
  run: number;
  status: string;
  y: Record<string, string | number>;
}

interface Analysis {
  main_effects?: Array<{ factor: string; effect: number; p?: number }>;
  anova?: Record<string, any>;
  r2?: number;
  adj_r2?: number;
  rmse?: number;
  suggested_next?: Record<string, any>;
}

interface Recommendation {
  points?: Array<Record<string, number>>;
  proposed_runs?: Array<Record<string, number>>;
  acq?: string;
}

interface Project {
  id: string;
  name: string;
}

interface Plan {
  id: string;
  name: string;
  method?: string;
  created_at?: string;
}

// State
interface State {
  projects: Project[];
  plans: Plan[];
  selectedProjectId: string;
  selectedPlanId: string;
  factorSpecs: FactorSpec[];
  method: string;
  runs: number;
  randomize: boolean;
  seed: number;
  designMatrix: DesignRow[];
  runResults: RunResult[];
  analysis: Analysis | null;
  recommendations: Recommendation | null;
  tab: 'Plan' | 'Runs' | 'Analysis' | 'Plots' | 'Optimize';
  loading: boolean;
  error: string;
  toast: string;
}

const initialState: State = {
  projects: [],
  plans: [],
  selectedProjectId: '',
  selectedPlanId: '',
  factorSpecs: [
    { name: 'Temp', type: 'continuous', low: 180, high: 220, unit: '°C' },
    { name: 'Pressure', type: 'continuous', low: 10, high: 30, unit: 'mTorr' },
    { name: 'RFPower', type: 'continuous', low: 200, high: 400, unit: 'W' },
  ],
  method: 'ccd',
  runs: 13,
  randomize: true,
  seed: 42,
  designMatrix: [],
  runResults: [],
  analysis: null,
  recommendations: null,
  tab: 'Plan',
  loading: false,
  error: '',
  toast: '',
};

type Action =
  | { type: 'SET'; payload: Partial<State> }
  | { type: 'LOADING'; value: boolean }
  | { type: 'ERROR'; value: string }
  | { type: 'TOAST'; value: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET':
      return { ...state, ...action.payload };
    case 'LOADING':
      return { ...state, loading: action.value };
    case 'ERROR':
      return { ...state, error: action.value };
    case 'TOAST':
      return { ...state, toast: action.value };
    default:
      return state;
  }
}

// API helpers
async function apiGet(path: string) {
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${DOE_API_BASE}${path}`, { credentials: 'include', headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function apiPost(path: string, body: any) {
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${DOE_API_BASE}${path}`, {
    method: 'POST',
    headers,
    credentials: 'include',
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export default function DoEPlanner() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const {
    projects,
    plans,
    selectedProjectId,
    selectedPlanId,
    factorSpecs,
    method,
    runs,
    randomize,
    seed,
    designMatrix,
    runResults,
    analysis,
    recommendations,
    tab,
    loading,
    error,
    toast,
  } = state;

  const [responseMetric, setResponseMetric] = useState('Yield');
  const [newMetricName, setNewMetricName] = useState('');

  // Load projects
  useEffect(() => {
    (async () => {
      try {
        dispatch({ type: 'LOADING', value: true });
        dispatch({ type: 'ERROR', value: '' });
        // For now, use mock data - replace with actual API call
        dispatch({ type: 'SET', payload: { projects: [{ id: '1', name: 'Default Project' }] } });
      } catch (e: any) {
        dispatch({ type: 'ERROR', value: e.message || String(e) });
      } finally {
        dispatch({ type: 'LOADING', value: false });
      }
    })();
  }, []);

  // Load plans when project changes
  useEffect(() => {
    if (!selectedProjectId) return;
    (async () => {
      try {
        dispatch({ type: 'LOADING', value: true });
        dispatch({ type: 'ERROR', value: '' });
        // Mock for now
        dispatch({ type: 'SET', payload: { plans: [], selectedPlanId: '' } });
      } catch (e: any) {
        dispatch({ type: 'ERROR', value: e.message || String(e) });
      } finally {
        dispatch({ type: 'LOADING', value: false });
      }
    })();
  }, [selectedProjectId]);

  // Initialize run results from design matrix
  useEffect(() => {
    if (!designMatrix.length || runResults.length) return;
    const init = designMatrix.map((row) => ({
      run: row.run ?? (row as any).run_index ?? (row as any).Run ?? (row as any).RUN ?? (row as any).id ?? 0,
      status: 'PENDING',
      y: { [responseMetric]: '' },
    }));
    dispatch({ type: 'SET', payload: { runResults: init } });
  }, [designMatrix, responseMetric, runResults.length]);

  const designColumns = useMemo(() => {
    const factorNames = factorSpecs.map((f) => f.name);
    return ['run', ...factorNames];
  }, [factorSpecs]);

  // Actions
  async function generateDesign() {
    try {
      dispatch({ type: 'LOADING', value: true });
      dispatch({ type: 'ERROR', value: '' });

      // Generate mock design matrix
      const mockRows: DesignRow[] = [];
      for (let i = 1; i <= runs; i++) {
        const row: DesignRow = { run: i };
        factorSpecs.forEach((f) => {
          row[f.name] = f.low + Math.random() * (f.high - f.low);
        });
        mockRows.push(row);
      }

      dispatch({ type: 'SET', payload: { designMatrix: mockRows } });
      dispatch({ type: 'TOAST', value: `Generated ${runs} runs (${method}).` });
      dispatch({ type: 'SET', payload: { tab: 'Plan' } });
    } catch (e: any) {
      dispatch({ type: 'ERROR', value: e.message || String(e) });
    } finally {
      dispatch({ type: 'LOADING', value: false });
    }
  }

  async function savePlan() {
    try {
      dispatch({ type: 'LOADING', value: true });
      dispatch({ type: 'ERROR', value: '' });
      // TODO: Implement actual save
      dispatch({ type: 'TOAST', value: 'Plan saved.' });
    } catch (e: any) {
      dispatch({ type: 'ERROR', value: e.message || String(e) });
    } finally {
      dispatch({ type: 'LOADING', value: false });
    }
  }

  async function submitResults() {
    try {
      if (!selectedPlanId) throw new Error('Select a plan first.');
      dispatch({ type: 'LOADING', value: true });
      dispatch({ type: 'ERROR', value: '' });
      // TODO: Implement actual submit
      dispatch({ type: 'TOAST', value: 'Results submitted.' });
      dispatch({ type: 'SET', payload: { tab: 'Analysis' } });
    } catch (e: any) {
      dispatch({ type: 'ERROR', value: e.message || String(e) });
    } finally {
      dispatch({ type: 'LOADING', value: false });
    }
  }

  async function analyzePlan() {
    try {
      if (!selectedPlanId) throw new Error('Select a plan first.');
      dispatch({ type: 'LOADING', value: true });
      dispatch({ type: 'ERROR', value: '' });
      
      // Mock analysis
      const mockAnalysis: Analysis = {
        main_effects: factorSpecs.map((f, i) => ({
          factor: f.name,
          effect: (Math.random() - 0.5) * 10,
          p: Math.random() * 0.1,
        })),
        r2: 0.85 + Math.random() * 0.1,
        adj_r2: 0.82 + Math.random() * 0.1,
        rmse: 2.5 + Math.random() * 1.5,
        anova: {},
      };
      
      dispatch({ type: 'SET', payload: { analysis: mockAnalysis } });
      dispatch({ type: 'TOAST', value: 'Analysis complete.' });
      dispatch({ type: 'SET', payload: { tab: 'Plots' } });
    } catch (e: any) {
      dispatch({ type: 'ERROR', value: e.message || String(e) });
    } finally {
      dispatch({ type: 'LOADING', value: false });
    }
  }

  async function recommendNext(n = 3) {
    try {
      if (!selectedPlanId) throw new Error('Select a plan first.');
      dispatch({ type: 'LOADING', value: true });
      dispatch({ type: 'ERROR', value: '' });
      
      // Mock recommendations
      const mockRecs: Recommendation = {
        points: Array.from({ length: n }, (_, i) => {
          const point: Record<string, number> = { run: i + 1, score: 0.9 - i * 0.1 };
          factorSpecs.forEach((f) => {
            point[f.name] = f.low + Math.random() * (f.high - f.low);
          });
          return point;
        }),
        acq: 'EI',
      };
      
      dispatch({ type: 'SET', payload: { recommendations: mockRecs } });
      dispatch({ type: 'TOAST', value: `Recommended next ${n} runs.` });
      dispatch({ type: 'SET', payload: { tab: 'Optimize' } });
    } catch (e: any) {
      dispatch({ type: 'ERROR', value: e.message || String(e) });
    } finally {
      dispatch({ type: 'LOADING', value: false });
    }
  }

  function updateFactor(index: number, patch: Partial<FactorSpec>) {
    const next = factorSpecs.map((f, i) => (i === index ? { ...f, ...patch } : f));
    dispatch({ type: 'SET', payload: { factorSpecs: next } });
  }

  function addFactor() {
    dispatch({
      type: 'SET',
      payload: {
        factorSpecs: [
          ...factorSpecs,
          { name: `Factor${factorSpecs.length + 1}`, type: 'continuous', low: 0, high: 1, unit: '' },
        ],
      },
    });
  }

  function removeFactor(index: number) {
    dispatch({ type: 'SET', payload: { factorSpecs: factorSpecs.filter((_, i) => i !== index) } });
  }

  function setRunMetricValue(runIdx: number, metricName: string, value: string | number) {
    const next = runResults.map((r, i) => {
      if (i !== runIdx) return r;
      return {
        ...r,
        y: { ...(r.y || {}), [metricName]: value },
        status: r.status === 'PENDING' ? 'DONE' : r.status,
      };
    });
    dispatch({ type: 'SET', payload: { runResults: next } });
  }

  function addResponseMetric() {
    const name = newMetricName.trim();
    if (!name) return;
    setResponseMetric(name);
    const next = runResults.map((r) => ({ ...r, y: { ...(r.y || {}), [name]: r.y?.[name] ?? '' } }));
    dispatch({ type: 'SET', payload: { runResults: next } });
    setNewMetricName('');
  }

  return (
    <div className="flex h-full bg-slate-900 text-white">
      {/* Left Panel - DOE Controls */}
      <div className="w-80 border-r border-slate-700 bg-slate-800 p-4 overflow-y-auto">
        <div className="text-xl font-bold mb-4 flex items-center gap-2">
          <Beaker className="w-6 h-6 text-yellow-400" />
          DoE Workspace
        </div>

        <div className="space-y-4">
          <div className="card">
            <div className="text-sm font-semibold text-slate-300 mb-2">Project</div>
            <select
              className="w-full input-field"
              value={selectedProjectId}
              onChange={(e) => dispatch({ type: 'SET', payload: { selectedProjectId: e.target.value } })}
            >
              <option value="">Select project…</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div className="card">
            <div className="text-sm font-semibold text-slate-300 mb-2">Plan</div>
            <select
              className="w-full input-field"
              value={selectedPlanId}
              onChange={(e) => dispatch({ type: 'SET', payload: { selectedPlanId: e.target.value } })}
            >
              <option value="">Select plan…</option>
              {plans.map((pl) => (
                <option key={pl.id} value={pl.id}>
                  {pl.name || `${pl.method} · ${pl.created_at || ''}`.trim()}
                </option>
              ))}
            </select>
          </div>

          <div className="card">
            <div className="text-sm font-semibold text-slate-300 mb-2">Design Method</div>
            <select
              className="w-full input-field"
              value={method}
              onChange={(e) => dispatch({ type: 'SET', payload: { method: e.target.value } })}
            >
              <option value="pb">Plackett–Burman (Screen)</option>
              <option value="frac_fact">Fractional Factorial</option>
              <option value="full_fact">Full Factorial</option>
              <option value="ccd">CCD (Response Surface)</option>
              <option value="bb">Box–Behnken (RSM)</option>
              <option value="lhs">Latin Hypercube (Space-filling)</option>
              <option value="bayes">Adaptive / Bayesian</option>
            </select>

            <div className="mt-3 space-y-2">
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400 w-20">Runs</label>
                <input
                  type="number"
                  className="flex-1 input-field"
                  value={runs}
                  onChange={(e) => dispatch({ type: 'SET', payload: { runs: parseInt(e.target.value || '0', 10) } })}
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400 w-20">Randomize</label>
                <input
                  type="checkbox"
                  checked={randomize}
                  onChange={() => dispatch({ type: 'SET', payload: { randomize: !randomize } })}
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400 w-20">Seed</label>
                <input
                  type="number"
                  className="flex-1 input-field"
                  value={seed}
                  onChange={(e) => dispatch({ type: 'SET', payload: { seed: parseInt(e.target.value || '0', 10) } })}
                />
              </div>
            </div>
          </div>

          <div className="card">
            <div className="text-sm font-semibold text-slate-300 mb-2">Actions</div>
            <div className="space-y-2">
              <button className="w-full btn-primary" onClick={generateDesign} disabled={loading}>
                <Play className="w-4 h-4 inline mr-2" />
                Generate Design
              </button>
              <button className="w-full btn-secondary" onClick={savePlan} disabled={loading || !selectedProjectId}>
                <Save className="w-4 h-4 inline mr-2" />
                Save Plan
              </button>
              <button className="w-full btn-secondary" onClick={analyzePlan} disabled={loading || !selectedPlanId}>
                <BarChart3 className="w-4 h-4 inline mr-2" />
                Analyze
              </button>
              <button className="w-full btn-secondary" onClick={() => recommendNext(3)} disabled={loading || !selectedPlanId}>
                <TrendingUp className="w-4 h-4 inline mr-2" />
                Recommend Next
              </button>
            </div>
          </div>

          <div className="text-xs text-slate-500 mt-4">
            Tip: Start with <b>PB</b> to screen many factors → then <b>CCD/BB</b> to optimize.
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Tabs */}
        <div className="flex items-center justify-between border-b border-slate-700 bg-slate-800 px-4">
          <div className="flex gap-2">
            {(['Plan', 'Runs', 'Analysis', 'Plots', 'Optimize'] as const).map((t) => (
              <button
                key={t}
                className={`px-4 py-2 rounded-t-lg transition-colors ${
                  tab === t
                    ? 'bg-slate-900 text-white border-b-2 border-blue-500'
                    : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                }`}
                onClick={() => dispatch({ type: 'SET', payload: { tab: t } })}
              >
                {t}
              </button>
            ))}
          </div>
          <div className="text-xs text-slate-500">{loading ? 'Working…' : 'Ready'}</div>
        </div>

        {/* Toast/Error Messages */}
        {toast && (
          <div className="mx-4 mt-4 bg-green-500/10 border border-green-500/50 text-green-400 px-4 py-3 rounded-lg flex justify-between items-center">
            <span>{toast}</span>
            <button onClick={() => dispatch({ type: 'TOAST', value: '' })} className="text-green-400 hover:text-green-300">
              ✕
            </button>
          </div>
        )}
        {error && (
          <div className="mx-4 mt-4 bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg flex justify-between items-center">
            <span>{error}</span>
            <button onClick={() => dispatch({ type: 'ERROR', value: '' })} className="text-red-400 hover:text-red-300">
              ✕
            </button>
          </div>
        )}

        {/* Tab Content */}
        <div className="flex-1 overflow-auto p-6">
          {tab === 'Plan' && (
            <div>
              <h2 className="text-2xl font-bold mb-2">Plan</h2>
              <p className="text-slate-400 mb-6">
                Define factors and generate a design matrix (CCD/BB/PB/LHS). Preview it before saving.
              </p>

              <div className="mb-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold">Factors</h3>
                  <button className="btn-secondary" onClick={addFactor}>
                    + Add Factor
                  </button>
                </div>
                <div className="card overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className="text-left p-2">Name</th>
                        <th className="text-left p-2">Type</th>
                        <th className="text-left p-2">Low</th>
                        <th className="text-left p-2">High</th>
                        <th className="text-left p-2">Unit</th>
                        <th className="text-left p-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {factorSpecs.map((f, idx) => (
                        <tr key={`${f.name}-${idx}`} className="border-b border-slate-700/50">
                          <td className="p-2">
                            <input
                              className="input-field w-full"
                              value={f.name}
                              onChange={(e) => updateFactor(idx, { name: e.target.value })}
                            />
                          </td>
                          <td className="p-2">
                            <select
                              className="input-field w-full"
                              value={f.type}
                              onChange={(e) => updateFactor(idx, { type: e.target.value as 'continuous' | 'categorical' })}
                            >
                              <option value="continuous">continuous</option>
                              <option value="categorical">categorical</option>
                            </select>
                          </td>
                          <td className="p-2">
                            <input
                              type="number"
                              className="input-field w-full"
                              value={f.low}
                              onChange={(e) => updateFactor(idx, { low: Number(e.target.value) })}
                            />
                          </td>
                          <td className="p-2">
                            <input
                              type="number"
                              className="input-field w-full"
                              value={f.high}
                              onChange={(e) => updateFactor(idx, { high: Number(e.target.value) })}
                            />
                          </td>
                          <td className="p-2">
                            <input
                              className="input-field w-full"
                              value={f.unit || ''}
                              onChange={(e) => updateFactor(idx, { unit: e.target.value })}
                            />
                          </td>
                          <td className="p-2">
                            <button className="btn-secondary text-red-400 hover:text-red-300" onClick={() => removeFactor(idx)}>
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-4">Design Preview</h3>
                {designMatrix.length === 0 ? (
                  <div className="card text-center text-slate-500 py-12">
                    Generate a design to preview runs.
                  </div>
                ) : (
                  <div className="card overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-slate-700">
                          {designColumns.map((c) => (
                            <th key={c} className="text-left p-2">
                              {c}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {designMatrix.map((r, i) => (
                          <tr key={i} className="border-b border-slate-700/50">
                            {designColumns.map((c) => (
                              <td key={c} className="p-2">
                                {typeof r[c] === 'number' ? r[c].toFixed(2) : String(r[c] ?? '')}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {tab === 'Runs' && (
            <div>
              <h2 className="text-2xl font-bold mb-2">Runs</h2>
              <p className="text-slate-400 mb-6">Enter measured responses for each run.</p>

              <div className="flex gap-4 items-center mb-6 flex-wrap">
                <label className="text-sm text-slate-300">Response metric:</label>
                <select className="input-field" value={responseMetric} onChange={(e) => setResponseMetric(e.target.value)}>
                  {Object.keys(runResults?.[0]?.y || { Yield: '' }).map((k) => (
                    <option key={k} value={k}>
                      {k}
                    </option>
                  ))}
                </select>
                <input
                  className="input-field"
                  placeholder="Add metric (e.g., CD, Defects)"
                  value={newMetricName}
                  onChange={(e) => setNewMetricName(e.target.value)}
                />
                <button className="btn-secondary" onClick={addResponseMetric}>
                  Add Metric
                </button>
                <button className="btn-primary" onClick={submitResults} disabled={!selectedPlanId}>
                  Submit Results
                </button>
              </div>

              {runResults.length === 0 ? (
                <div className="card text-center text-slate-500 py-12">
                  No runs initialized yet. Generate a design first.
                </div>
              ) : (
                <div className="card overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className="text-left p-2">run</th>
                        <th className="text-left p-2">status</th>
                        <th className="text-left p-2">{responseMetric}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {runResults.map((r, idx) => (
                        <tr key={idx} className="border-b border-slate-700/50">
                          <td className="p-2">{r.run ?? idx + 1}</td>
                          <td className="p-2">{r.status || 'PENDING'}</td>
                          <td className="p-2">
                            <input
                              className="input-field w-full"
                              value={r?.y?.[responseMetric] ?? ''}
                              onChange={(e) => setRunMetricValue(idx, responseMetric, e.target.value)}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {tab === 'Analysis' && (
            <div>
              <h2 className="text-2xl font-bold mb-2">Analysis</h2>
              <p className="text-slate-400 mb-6">Main effects ranking, ANOVA summary, and model fit.</p>

              <div className="flex gap-4 mb-6">
                <button className="btn-primary" onClick={analyzePlan} disabled={!selectedPlanId}>
                  Run Analysis
                </button>
                <button className="btn-secondary" onClick={() => dispatch({ type: 'SET', payload: { tab: 'Plots' } })}>
                  View Plots →
                </button>
              </div>

              {!analysis ? (
                <div className="card text-center text-slate-500 py-12">
                  No analysis yet. Submit results and run analysis.
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-4">
                  <div className="card">
                    <h3 className="font-semibold mb-4">Main Effects Ranking</h3>
                    {analysis.main_effects && analysis.main_effects.length > 0 ? (
                      <ol className="list-decimal list-inside space-y-2">
                        {analysis.main_effects.slice(0, 10).map((m, i) => (
                          <li key={i} className="text-sm">
                            <b>{m.factor}</b> — effect: {m.effect.toFixed(4)}
                            {m.p != null ? ` (p=${m.p.toFixed(4)})` : ''}
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <div className="text-slate-500 text-sm">No main effects data</div>
                    )}
                  </div>

                  <div className="card">
                    <h3 className="font-semibold mb-4">Model Fit</h3>
                    <div className="space-y-2 text-sm">
                      <div>R²: {analysis.r2 != null ? analysis.r2.toFixed(4) : '—'}</div>
                      <div>Adj R²: {analysis.adj_r2 != null ? analysis.adj_r2.toFixed(4) : '—'}</div>
                      <div>RMSE: {analysis.rmse != null ? analysis.rmse.toFixed(4) : '—'}</div>
                    </div>
                  </div>

                  <div className="card col-span-2">
                    <h3 className="font-semibold mb-4">ANOVA Summary</h3>
                    <pre className="text-xs overflow-auto">{JSON.stringify(analysis.anova || {}, null, 2)}</pre>
                  </div>
                </div>
              )}
            </div>
          )}

          {tab === 'Plots' && (
            <div>
              <h2 className="text-2xl font-bold mb-2">Plots</h2>
              <p className="text-slate-400 mb-6">
                Main effects, interaction/cube, contour, response surface, residuals.
              </p>

              <div className="grid grid-cols-2 gap-4">
                {[
                  { title: 'Main Effects Plot', hint: 'Shows average response change per factor level.' },
                  { title: 'Interaction / Cube Plot', hint: 'Shows factor interactions (2-way/3-way).' },
                  { title: 'Contour Plot', hint: '2D slice (X vs Y) with other factors fixed.' },
                  { title: 'Response Surface', hint: '3D surface plot for RSM designs (CCD/BB).' },
                  { title: 'Residual Diagnostics', hint: 'QQ plot / residual vs fitted to validate model.' },
                  { title: 'Pareto / Effect Ranking', hint: 'Standardized effects ranking (screening).' },
                ].map((plot, i) => (
                  <div key={i} className="card">
                    <h3 className="font-semibold mb-2">{plot.title}</h3>
                    <div className="h-40 border border-dashed border-slate-600 rounded-lg flex items-center justify-center bg-slate-800/50 mb-2">
                      <span className="text-slate-500 text-sm">[Plot area]</span>
                    </div>
                    <p className="text-xs text-slate-500">{plot.hint}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {tab === 'Optimize' && (
            <div>
              <h2 className="text-2xl font-bold mb-2">Optimize</h2>
              <p className="text-slate-400 mb-6">
                Adaptive mode: recommend next best experiments (Bayesian / desirability / constraints).
              </p>

              <div className="flex gap-4 mb-6">
                <button className="btn-primary" onClick={() => recommendNext(3)} disabled={!selectedPlanId}>
                  Recommend Next 3
                </button>
                <button className="btn-secondary" onClick={() => dispatch({ type: 'SET', payload: { tab: 'Runs' } })}>
                  Back to Runs
                </button>
              </div>

              {!recommendations ? (
                <div className="card text-center text-slate-500 py-12">
                  No recommendations yet. Run analysis first, then request "Recommend Next".
                </div>
              ) : (
                <div className="card">
                  <h3 className="font-semibold mb-4">Next Best Experiments</h3>
                  <p className="text-sm text-slate-500 mb-4">Acquisition: {recommendations.acq || '—'}</p>
                  {recommendations.points && recommendations.points.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-slate-700">
                            {Object.keys(recommendations.points[0]).map((k) => (
                              <th key={k} className="text-left p-2">
                                {k}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {recommendations.points.map((p, i) => (
                            <tr key={i} className="border-b border-slate-700/50">
                              {Object.keys(p).map((k) => (
                                <td key={k} className="p-2">
                                  {typeof p[k] === 'number' ? p[k].toFixed(2) : String(p[k])}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-slate-500 text-sm">No recommendation points available</div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
