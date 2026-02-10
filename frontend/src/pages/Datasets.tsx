import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  getDatasets,
  uploadDataset,
  postPreview,
  undoPreview,
  commitDataset,
  type DatasetMeta,
  type PreviewResponse,
} from '../features/viz/vizAutomationApi';

const DatasetsPage: React.FC = () => {
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [commitLoading, setCommitLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    getDatasets()
      .then((list) => {
        if (!cancelled) setDatasets(Array.isArray(list) ? list : []);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load datasets');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setUploading(true);
    try {
      await uploadDataset(file);
      const list = await getDatasets();
      setDatasets(Array.isArray(list) ? list : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const loadPreview = (id: number) => {
    setSelectedId(id);
    setPreview(null);
    setPreviewLoading(true);
    setError(null);
    postPreview(id, 50)
      .then(setPreview)
      .catch((e) => setError(e instanceof Error ? e.message : 'Preview failed'))
      .finally(() => setPreviewLoading(false));
  };

  const handleUndoPreview = async (id: number) => {
    setError(null);
    try {
      await undoPreview(id);
      setPreview(null);
      const list = await getDatasets();
      setDatasets(Array.isArray(list) ? list : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Undo failed');
    }
  };

  const handleCommit = async (id: number) => {
    setError(null);
    setCommitLoading(true);
    try {
      await commitDataset(id);
      const list = await getDatasets();
      setDatasets(Array.isArray(list) ? list : []);
      setPreview(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Commit failed');
    } finally {
      setCommitLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold text-white mb-2">Datasets</h1>
      <p className="text-slate-400 mb-6">
        Upload CSV or .mat files. Preview → Commit to use in Viz Automation.
      </p>

      {error && (
        <div className="mb-4 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-200">
          {error}
        </div>
      )}

      <div className="card mb-6">
        <h2 className="text-lg font-bold text-white mb-3">Upload</h2>
        <input
          type="file"
          accept=".csv,.mat"
          onChange={handleFileChange}
          disabled={uploading}
          className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-cyan-600 file:text-white file:cursor-pointer hover:file:bg-cyan-500"
        />
        {uploading && <p className="mt-2 text-slate-400 text-sm">Uploading...</p>}
      </div>

      <div className="card">
        <h2 className="text-lg font-bold text-white mb-3">My datasets</h2>
        {loading ? (
          <p className="text-slate-400">Loading...</p>
        ) : datasets.length === 0 ? (
          <p className="text-slate-400">
            No datasets yet. Upload a file above or{' '}
            <Link to="/viz-automation" className="text-cyan-400 hover:underline">
              run seed import
            </Link>{' '}
            and refresh.
          </p>
        ) : (
          <div className="space-y-4">
            {datasets.map((d) => (
              <div
                key={d.id}
                className="border border-slate-700 rounded-lg p-4 flex flex-wrap items-center justify-between gap-3"
              >
                <div>
                  <span className="font-medium text-white">{d.filename}</span>
                  <span className="ml-2 text-slate-400 text-sm">
                    {d.stage ?? 'DRAFT'} {d.committed ? '✓ committed' : ''}
                  </span>
                  {d.row_count != null && (
                    <span className="ml-2 text-slate-500 text-sm">
                      {d.row_count} rows{d.column_count != null ? ` · ${d.column_count} cols` : ''}
                    </span>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => loadPreview(d.id)}
                    className="px-3 py-1.5 rounded-lg bg-slate-600 text-white text-sm hover:bg-slate-500"
                  >
                    Preview
                  </button>
                  {d.stage === 'PREVIEW' && (
                    <>
                      <button
                        type="button"
                        onClick={() => handleUndoPreview(d.id)}
                        className="px-3 py-1.5 rounded-lg bg-slate-600 text-white text-sm hover:bg-slate-500"
                      >
                        Undo
                      </button>
                      <button
                        type="button"
                        onClick={() => handleCommit(d.id)}
                        disabled={commitLoading}
                        className="px-3 py-1.5 rounded-lg bg-cyan-600 text-white text-sm hover:bg-cyan-500 disabled:opacity-50"
                      >
                        Commit
                      </button>
                    </>
                  )}
                  {d.committed && (
                    <Link
                      to={`/viz-automation?datasetId=${d.id}`}
                      className="px-3 py-1.5 rounded-lg bg-cyan-600 text-white text-sm hover:bg-cyan-500 inline-block"
                    >
                      Viz Automation
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {selectedId != null && (
          <div className="mt-6 pt-6 border-t border-slate-700">
            <h3 className="text-md font-semibold text-white mb-2">
              Preview {previewLoading ? '...' : `(dataset ${selectedId})`}
            </h3>
            {previewLoading ? (
              <p className="text-slate-400">Loading preview...</p>
            ) : preview ? (
              <div className="text-sm text-slate-300 space-y-2">
                <p>Rows: {preview.rowCount} · Cols: {preview.columnCount} · Stage: {preview.stage}</p>
                {preview.columns && preview.columns.length > 0 && (
                  <p>Columns: {(preview.columns as string[]).slice(0, 10).join(', ')}
                    {preview.columns.length > 10 ? '...' : ''}
                  </p>
                )}
                {preview.wafersPreview && preview.wafersPreview.length > 0 && (
                  <p>Wafers preview: {preview.wafersPreview.length} items</p>
                )}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
};

export default DatasetsPage;
