import React, { useState } from 'react';
import { Sparkles, Download } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const Generator: React.FC = () => {
  const [processType, setProcessType] = useState('etch');
  const [template, setTemplate] = useState('');
  const [nRuns, setNRuns] = useState(100);
  const [timeSeries, setTimeSeries] = useState(false);
  const [saveAsSeedFolder, setSaveAsSeedFolder] = useState(false);
  const [includeDrift, setIncludeDrift] = useState(false);
  const [includeStepChange, setIncludeStepChange] = useState(false);
  const [includeIntermittent, setIncludeIntermittent] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/generate`, {
        processType,
        template: template || null,
        nRuns,
        timeSeries,
        saveAsSeedFolder,
        include_drift: includeDrift,
        include_step_change: includeStepChange,
        include_intermittent: includeIntermittent
      });
      setResult(response.data);
    } catch (error: any) {
      console.error('Generation failed:', error);
      alert(error.response?.data?.detail || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Synthetic Data Generator</h1>
        <p className="text-slate-400">Generate synthetic datasets for process simulation</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form */}
        <div className="card">
          <form onSubmit={handleGenerate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Process Type
              </label>
              <select
                value={processType}
                onChange={(e) => setProcessType(e.target.value)}
                className="w-full input-field"
              >
                <option value="etch">Etch</option>
                <option value="cvd">CVD</option>
                <option value="deposition">Deposition</option>
                <option value="lithography">Lithography</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Template (optional)
              </label>
              <input
                type="text"
                value={template}
                onChange={(e) => setTemplate(e.target.value)}
                className="w-full input-field"
                placeholder="default"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Number of Runs
              </label>
              <input
                type="number"
                value={nRuns}
                onChange={(e) => setNRuns(parseInt(e.target.value))}
                min={1}
                max={10000}
                className="w-full input-field"
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="timeSeries"
                checked={timeSeries}
                onChange={(e) => setTimeSeries(e.target.checked)}
                className="w-4 h-4"
              />
              <label htmlFor="timeSeries" className="text-sm text-slate-300">
                Generate time series data
              </label>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="saveAsSeedFolder"
                checked={saveAsSeedFolder}
                onChange={(e) => setSaveAsSeedFolder(e.target.checked)}
                className="w-4 h-4"
              />
              <label htmlFor="saveAsSeedFolder" className="text-sm text-slate-300">
                Save as seed folder
              </label>
            </div>

            <div className="border-t border-slate-700 pt-4">
              <div className="text-sm font-semibold text-slate-300 mb-3">Anomaly Scenarios (Etch only)</div>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="includeDrift"
                    checked={includeDrift}
                    onChange={(e) => setIncludeDrift(e.target.checked)}
                    className="w-4 h-4"
                    disabled={processType !== 'etch'}
                  />
                  <label htmlFor="includeDrift" className="text-sm text-slate-300">
                    Include Gradual Drift
                  </label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="includeStepChange"
                    checked={includeStepChange}
                    onChange={(e) => setIncludeStepChange(e.target.checked)}
                    className="w-4 h-4"
                    disabled={processType !== 'etch'}
                  />
                  <label htmlFor="includeStepChange" className="text-sm text-slate-300">
                    Include Step Change
                  </label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="includeIntermittent"
                    checked={includeIntermittent}
                    onChange={(e) => setIncludeIntermittent(e.target.checked)}
                    className="w-4 h-4"
                    disabled={processType !== 'etch'}
                  />
                  <label htmlFor="includeIntermittent" className="text-sm text-slate-300">
                    Include Intermittent Spikes
                  </label>
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={generating}
              className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              {generating ? 'Generating...' : 'Generate'}
            </button>
          </form>
        </div>

        {/* Result */}
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-4">Generation Result</h2>
          {result ? (
            <div className="space-y-4">
              <div className="bg-green-500/10 border border-green-500/50 rounded-lg p-4">
                <p className="text-green-400 font-semibold">✓ {result.message}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-2">Output Path:</p>
                <p className="text-white font-mono text-sm break-all">{result.output_path}</p>
              </div>
              <a
                href={`${API_BASE_URL}${result.output_path}`}
                download
                className="btn-secondary flex items-center justify-center gap-2"
              >
                <Download className="w-4 h-4" />
                Download
              </a>
            </div>
          ) : (
            <div className="text-center text-slate-500 py-12">
              <Sparkles className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Configure options and generate synthetic data</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Generator;
