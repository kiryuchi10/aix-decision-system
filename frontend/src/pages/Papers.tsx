import React, { useState, useEffect } from 'react';
import { Upload, FileText, Play } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface Paper {
  id: number;
  filename: string;
  status: string;
  created_at: string;
}

const Papers: React.FC = () => {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchPapers();
  }, []);

  const fetchPapers = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/papers`);
      setPapers(response.data);
    } catch (error) {
      console.error('Failed to fetch papers:', error);
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
      await axios.post(`${API_BASE_URL}/api/v1/papers/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      fetchPapers();
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleExtract = async (paperId: number) => {
    try {
      await axios.post(`${API_BASE_URL}/api/v1/papers/${paperId}/extract`);
      fetchPapers();
      alert('Extraction started');
    } catch (error) {
      console.error('Extraction failed:', error);
      alert('Extraction failed');
    }
  };

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Papers</h1>
        <p className="text-slate-400">Upload and extract research papers</p>
      </div>

      {/* Upload Section */}
      <div className="card mb-6">
        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-slate-600 rounded-lg cursor-pointer hover:bg-slate-700/50 transition-colors">
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            <Upload className="w-10 h-10 mb-3 text-slate-400" />
            <p className="mb-2 text-sm text-slate-400">
              <span className="font-semibold">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-slate-500">PDF files only</p>
          </div>
          <input
            type="file"
            className="hidden"
            accept=".pdf"
            onChange={handleUpload}
            disabled={uploading}
          />
        </label>
        {uploading && <p className="mt-2 text-center text-slate-400">Uploading...</p>}
      </div>

      {/* Papers List */}
      {loading ? (
        <div className="text-center text-slate-400">Loading...</div>
      ) : papers.length === 0 ? (
        <div className="text-center text-slate-400 py-12">No papers uploaded yet</div>
      ) : (
        <div className="space-y-4">
          {papers.map((paper) => (
            <div key={paper.id} className="card flex items-center justify-between">
              <div className="flex items-center gap-4">
                <FileText className="w-8 h-8 text-blue-400" />
                <div>
                  <h3 className="font-semibold text-white">{paper.filename}</h3>
                  <p className="text-sm text-slate-400">
                    Status: {paper.status} • {new Date(paper.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              {paper.status === 'uploaded' && (
                <button
                  onClick={() => handleExtract(paper.id)}
                  className="btn-primary flex items-center gap-2"
                >
                  <Play className="w-4 h-4" />
                  Extract
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Papers;
