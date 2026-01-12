import React, { useState, useEffect } from 'react';
import { Upload, Database, Eye } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface Dataset {
  id: number;
  filename: string;
  row_count: number | null;
  column_count: number | null;
  created_at: string;
}

const Datasets: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [, setPreviewDataset] = useState<number | null>(null);
  const [previewData, setPreviewData] = useState<any>(null);

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/datasets`);
      setDatasets(response.data);
    } catch (error) {
      console.error('Failed to fetch datasets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post(`${API_BASE_URL}/api/v1/datasets/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      fetchDatasets();
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handlePreview = async (datasetId: number) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/datasets/${datasetId}/preview?rows=50`);
      setPreviewData(response.data);
      setPreviewDataset(datasetId);
    } catch (error) {
      console.error('Preview failed:', error);
      alert('Preview failed');
    }
  };

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Datasets</h1>
        <p className="text-slate-400">Upload and manage CSV datasets</p>
      </div>

      {/* Upload Section */}
      <div className="card mb-6">
        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-slate-600 rounded-lg cursor-pointer hover:bg-slate-700/50 transition-colors">
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            <Upload className="w-10 h-10 mb-3 text-slate-400" />
            <p className="mb-2 text-sm text-slate-400">
              <span className="font-semibold">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-slate-500">CSV files only</p>
          </div>
          <input
            type="file"
            className="hidden"
            accept=".csv"
            onChange={handleUpload}
            disabled={uploading}
          />
        </label>
        {uploading && <p className="mt-2 text-center text-slate-400">Uploading...</p>}
      </div>

      {/* Datasets List */}
      {loading ? (
        <div className="text-center text-slate-400">Loading...</div>
      ) : datasets.length === 0 ? (
        <div className="text-center text-slate-400 py-12">No datasets uploaded yet</div>
      ) : (
        <div className="space-y-4">
          {datasets.map((dataset) => (
            <div key={dataset.id} className="card flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Database className="w-8 h-8 text-green-400" />
                <div>
                  <h3 className="font-semibold text-white">{dataset.filename}</h3>
                  <p className="text-sm text-slate-400">
                    {dataset.row_count || '?'} rows × {dataset.column_count || '?'} columns • {new Date(dataset.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <button
                onClick={() => handlePreview(dataset.id)}
                className="btn-secondary flex items-center gap-2"
              >
                <Eye className="w-4 h-4" />
                Preview
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {previewData && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl p-6 max-w-4xl w-full max-h-[80vh] overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-white">Preview</h2>
              <button
                onClick={() => setPreviewDataset(null)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    {previewData.columns.map((col: string) => (
                      <th key={col} className="text-left p-2 text-slate-300">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {previewData.rows.slice(0, 50).map((row: any, idx: number) => (
                    <tr key={idx} className="border-b border-slate-700/50">
                      {previewData.columns.map((col: string) => (
                        <td key={col} className="p-2 text-slate-400">{row[col]}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Datasets;
