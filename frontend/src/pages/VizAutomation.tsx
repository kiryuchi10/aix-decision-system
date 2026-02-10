import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Database, Play, AlertCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import {
  getDatasets,
  getVizSummary,
  getVizArtifacts,
  runStep,
  artifactImageUrl,
  checkBackendHealth,
  VIZ_SERVER,
  type DatasetMeta,
  type ArtifactItem,
} from '../features/viz/vizAutomationApi';

const PIPELINE_STEPS = [
  { id: 'raw', label: 'Raw' },
  { id: 'clean', label: 'Clean' },
  { id: 'eda', label: 'EDA' },
  { id: 'fe', label: 'FE' },
  { id: 'pca', label: 'PCA' },
  { id: 'cluster', label: 'Cluster' },
  { id: 'models', label: 'Models' },
  { id: 'policy', label: 'Policy' },
];

function getErrorMessage(e: unknown, serverUrl?: string): string {
  const base = serverUrl ?? 'http://localhost:8000';
  if (e instanceof Error) {
    if (e.message === 'Failed to fetch') {
      return `Cannot reach the backend at ${base}. (1) Start backend: cd backend && uvicorn app.main:app --reload (2) Set VITE_API_BASE_URL in .env to your backend URL (3) Check CORS allows your frontend origin.`;
    }
    return e.message;
  }
  if (e && typeof e === 'object' && 'status' in e && 'message' in e) {
    const err = e as { status: number; message: string; details?: unknown };
    const detail = typeof err.details === 'string' ? err.details : (err.details as { detail?: string })?.detail;
    if (err.status === 401) return 'Please log in to load datasets.';
    return detail || err.message || 'Failed to load datasets';
  }
  return 'Failed to load datasets';
}

const VizAutomationPage: React.FC = () => {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [searchParams] = useSearchParams();
  const datasetIdParam = searchParams.get('datasetId');
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [currentStep, setCurrentStep] = useState<string>('raw');
  const [summary, setSummary] = useState<{ row_count: number } | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [runLoading, setRunLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendReachable, setBackendReachable] = useState<boolean | null>(null);

  const selectedDataset = datasets.find((d) => d.id === selectedId);

  useEffect(() => {
    let cancelled = false;
    checkBackendHealth().then((ok) => {
      if (!cancelled) setBackendReachable(ok);
    });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (authLoading || !isAuthenticated) {
      setError(null);
      return;
    }
    let cancelled = false;
    setError(null);
    getDatasets()
      .then((list) => {
        if (!cancelled) setDatasets(Array.isArray(list) ? list : []);
        const id = datasetIdParam ? parseInt(datasetIdParam, 10) : (Array.isArray(list) ? list[0]?.id : undefined) ?? null;
        if (!cancelled && id != null) setSelectedId(id);
      })
      .catch((e) => {
        if (!cancelled) setError(getErrorMessage(e, VIZ_SERVER));
      });
    return () => { cancelled = true; };
  }, [authLoading, isAuthenticated, datasetIdParam]);

  useEffect(() => {
    if (selectedId == null) {
      setSummary(null);
      setArtifacts([]);
      return;
    }
    let cancelled = false;
    setError(null);
    setLoading(true);
    Promise.all([
      getVizSummary(selectedId, currentStep),
      getVizArtifacts(selectedId, currentStep),
    ])
      .then(([s, a]) => {
        if (!cancelled) {
          setSummary(s as { row_count: number });
          setArtifacts(a.artifacts ?? []);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load summary/artifacts');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [selectedId, currentStep]);

  const handleRunStep = async () => {
    if (selectedId == null) return;
    setError(null);
    setRunLoading(true);
    try {
      const result = await runStep(selectedId, currentStep);
      if (result.status === 'ok') {
        const [s, a] = await Promise.all([
          getVizSummary(selectedId, currentStep),
          getVizArtifacts(selectedId, currentStep),
        ]);
        setSummary(s as { row_count: number });
        setArtifacts(a.artifacts ?? []);
      } else {
        setError(result.error ?? 'Step failed');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Run step failed');
    } finally {
      setRunLoading(false);
    }
  };

  const canRun = selectedDataset?.committed === true;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Database className="w-8 h-8 text-cyan-400" />
          Viz Automation
        </h1>
        <p className="text-slate-400 mt-1">8-step pipeline. Run step only when dataset is committed. Artifact-first (png/csv/json).</p>
      </div>

      {backendReachable === false && (
        <div className="mb-4 p-4 bg-amber-900/30 border border-amber-700 rounded-lg text-amber-200 flex items-start gap-2" role="alert">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Backend not reachable at {VIZ_SERVER}</p>
            <ul className="mt-2 list-disc list-inside text-sm">
              <li>Start backend: <code className="bg-black/30 px-1 rounded">cd backend && uvicorn app.main:app --reload</code></li>
              <li>Set <code className="bg-black/30 px-1 rounded">VITE_API_BASE_URL={VIZ_SERVER}</code> in frontend <code className="bg-black/30 px-1 rounded">.env</code></li>
              <li>If using MySQL: run <code className="bg-black/30 px-1 rounded">scripts/mysql_setup.sh</code> and <code className="bg-black/30 px-1 rounded">setup_database.sql</code> then ensure <code className="bg-black/30 px-1 rounded">DATABASE_URL</code> in backend <code className="bg-black/30 px-1 rounded">.env</code></li>
            </ul>
          </div>
        </div>
      )}
      {backendReachable === false && (
        <div className="mb-4 p-4 bg-amber-900/30 border border-amber-700 rounded-lg text-amber-200 flex items-start gap-2" role="alert">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Backend not reachable at {VIZ_SERVER}</p>
            <ul className="mt-2 list-disc list-inside text-sm">
              <li>Start backend: <code className="bg-black/30 px-1 rounded">cd backend && uvicorn app.main:app --reload</code></li>
              <li>Set <code className="bg-black/30 px-1 rounded">VITE_API_BASE_URL={VIZ_SERVER}</code> in frontend <code className="bg-black/30 px-1 rounded">.env</code></li>
              <li>If using MySQL: run <code className="bg-black/30 px-1 rounded">scripts/mysql_setup.sh</code> and <code className="bg-black/30 px-1 rounded">setup_database.sql</code> then set <code className="bg-black/30 px-1 rounded">DATABASE_URL</code> in backend <code className="bg-black/30 px-1 rounded">.env</code></li>
            </ul>
          </div>
        </div>
      )}
      {error && (
        <div className="mb-4 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-200 flex items-start gap-2" role="alert">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <div className="card mb-6">
        <h2 className="text-lg font-bold text-white mb-3">Dataset</h2>
        {authLoading ? (
          <p className="text-slate-400">Checking auth...</p>
        ) : !isAuthenticated ? (
          <p className="text-amber-400">Log in to see and select datasets.</p>
        ) : (
          <>
            <select
              value={selectedId ?? ''}
              onChange={(e) => setSelectedId(e.target.value ? Number(e.target.value) : null)}
              className="input-field w-full max-w-md"
              aria-label="Select dataset"
            >
              <option value="">Select dataset</option>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename} · {d.stage ?? 'DRAFT'} {d.committed ? '✓' : ''}
                </option>
              ))}
            </select>
            {datasets.length === 0 && !error && (
              <p className="mt-2 text-slate-400 text-sm">
                No datasets yet. <Link to="/datasets" className="text-cyan-400 hover:underline">Upload one on the Datasets page</Link>.
              </p>
            )}
            {selectedDataset && !selectedDataset.committed && (
              <p className="mt-2 text-amber-400 text-sm">Commit this dataset in Datasets page to run pipeline steps.</p>
            )}
          </>
        )}
      </div>

      <div className="card mb-6">
        <h2 className="text-lg font-bold text-white mb-3">Step</h2>
        <div className="flex flex-wrap gap-2">
          {PIPELINE_STEPS.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setCurrentStep(s.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                currentStep === s.id ? 'bg-cyan-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
        <div className="mt-4 flex items-center gap-4">
          <button
            type="button"
            onClick={handleRunStep}
            disabled={!canRun || runLoading}
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            {runLoading ? 'Running...' : 'Run step'}
          </button>
          {summary != null && (
            <span className="text-slate-400 text-sm">Rows: {summary.row_count ?? 0}</span>
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-bold text-white mb-3">Artifacts</h2>
        {loading ? (
          <p className="text-slate-400">Loading...</p>
        ) : artifacts.length === 0 ? (
          <p className="text-slate-400">No artifacts yet. Run a step above.</p>
        ) : (
          <div className="space-y-6">
            {artifacts.map((a) => (
              <div key={a.id} className="border border-slate-700 rounded-lg p-4">
                <p className="text-sm font-medium text-white mb-2">{a.title}</p>
                {a.kind === 'png' && a.url && (
                  <img
                    src={artifactImageUrl(a.url)}
                    alt={a.title}
                    className="max-w-full h-auto rounded border border-slate-700"
                    style={{ maxHeight: '400px' }}
                  />
                )}
                {a.kind !== 'png' && a.url && (
                  <a
                    href={artifactImageUrl(a.url)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cyan-400 hover:underline"
                  >
                    Download {a.title}
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default VizAutomationPage;
