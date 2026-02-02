import React, { useState, useMemo } from 'react';
import { Database, Sparkles, Play, Save, Download, MessageSquare, BarChart3, Eye, EyeOff, Grid3x3, ChevronDown, ChevronUp, X, Upload } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiPost } from '../app/apiClient';

// ========== TYPES ==========
interface ColumnMeta {
  name: string;
  type: 'datetime' | 'categorical' | 'numeric';
  description: string;
  missingCount: number;
}

interface Keyword {
  id: string;
  text: string;
  category: 'process' | 'quality' | 'statistical' | 'temporal';
  confidence: number;
  columns: string[];
}

interface Snapshot {
  id: string;
  stage: 'raw' | 'clean' | 'eda';
  rowCount: number;
  missingRatio: number;
  timestamp: string;
}

interface PipelineStep {
  id: string;
  order: number;
  name: string;
  type: string;
  params: Record<string, any>;
}

interface PromptTemplate {
  category: string;
  name: string;
  prompt: string;
}

// ========== MOCK DATA ==========
const mockDataset = {
  id: 'ds-001',
  name: 'Etch Process Data',
  rowCount: 5000,
  columnCount: 12,
  columns: [
    { name: 'timestamp', type: 'datetime', description: 'Process timestamp', missingCount: 0 },
    { name: 'chamber_id', type: 'categorical', description: 'Chamber identifier', missingCount: 0 },
    { name: 'pressure_torr', type: 'numeric', description: 'Chamber pressure in Torr', missingCount: 23 },
    { name: 'temperature_c', type: 'numeric', description: 'Process temperature', missingCount: 15 },
    { name: 'rf_power_w', type: 'numeric', description: 'RF power in watts', missingCount: 8 },
    { name: 'gas_flow_sccm', type: 'numeric', description: 'Gas flow rate', missingCount: 12 },
    { name: 'etch_rate', type: 'numeric', description: 'Etch rate nm/min', missingCount: 45 },
    { name: 'uniformity_pct', type: 'numeric', description: 'Uniformity percentage', missingCount: 31 },
  ] as ColumnMeta[]
};

const mockKeywords: Keyword[] = [
  { id: 'kw-1', text: 'pressure', category: 'process', confidence: 0.95, columns: ['pressure_torr'] },
  { id: 'kw-2', text: 'temperature', category: 'process', confidence: 0.92, columns: ['temperature_c'] },
  { id: 'kw-3', text: 'quality', category: 'quality', confidence: 0.88, columns: ['etch_rate', 'uniformity_pct'] },
  { id: 'kw-4', text: 'power', category: 'process', confidence: 0.85, columns: ['rf_power_w'] },
  { id: 'kw-5', text: 'drift', category: 'statistical', confidence: 0.78, columns: ['pressure_torr', 'temperature_c'] },
];

const mockSnapshots: Snapshot[] = [
  { id: 'snap-1', stage: 'raw', rowCount: 5000, missingRatio: 0.027, timestamp: '2 min ago' },
  { id: 'snap-2', stage: 'clean', rowCount: 4955, missingRatio: 0.000, timestamp: '1 min ago' },
  { id: 'snap-3', stage: 'eda', rowCount: 4955, missingRatio: 0.000, timestamp: 'Just now' },
];

const mockChartData = Array.from({ length: 100 }, (_, i) => ({
  index: i,
  pressure: 35 + Math.random() * 10,
  temperature: 850 + Math.random() * 20,
  power: 200 + Math.random() * 50,
}));

const promptTemplates: PromptTemplate[] = [
  { category: 'Data Quality', name: 'Quality Summary', prompt: 'Summarize top 10 data quality issues' },
  { category: 'EDA', name: 'Graph Interpretation', prompt: 'Explain current plot grid and insights' },
  { category: 'Preprocessing', name: 'Pipeline Recommendation', prompt: 'Recommend preprocessing pipeline' },
  { category: 'Model', name: 'Model Selection', prompt: 'Suggest appropriate models for this data' },
  { category: 'Export', name: 'Report Generation', prompt: 'Generate analysis summary report' },
  { category: 'Next Actions', name: '7-Day Plan', prompt: 'Create 7-day execution plan' },
];

// ========== COMPONENTS ==========
const KeywordToggle = ({ keyword, active, onToggle }: { keyword: Keyword; active: boolean; onToggle: () => void }) => {
  const categoryColors = {
    process: 'bg-blue-500',
    quality: 'bg-green-500',
    statistical: 'bg-purple-500',
    temporal: 'bg-orange-500'
  };

  return (
    <button
      onClick={onToggle}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition-all ${
        active 
          ? `${categoryColors[keyword.category]} border-transparent text-white` 
          : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
      }`}
    >
      <span className="font-medium">{keyword.text}</span>
      <span className="text-xs opacity-75">({keyword.columns.length})</span>
      {active ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
    </button>
  );
};

const PlotCard = ({ title, children }: { title: string; type: string; children: React.ReactNode }) => {
  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-semibold text-white">{title}</h3>
        </div>
        <div className="flex gap-1">
          <button className="p-1 hover:bg-slate-700 rounded">
            <Save className="w-4 h-4 text-slate-400" />
          </button>
          <button className="p-1 hover:bg-slate-700 rounded">
            <Download className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>
      <div className="bg-slate-900 rounded-lg p-3" style={{ height: '220px' }}>
        {children}
      </div>
    </div>
  );
};

const PipelineStepCard = ({ step, onRemove }: { step: PipelineStep; onRemove: () => void }) => {
  return (
    <div className="flex items-center gap-3 p-3 bg-slate-800 rounded-lg border border-slate-700">
      <div className="w-8 h-8 rounded bg-blue-500/20 flex items-center justify-center">
        <span className="text-blue-400 font-bold text-sm">{step.order}</span>
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium text-white">{step.name}</p>
        <p className="text-xs text-slate-400">{step.type}</p>
      </div>
      <button onClick={onRemove} className="p-1 hover:bg-slate-700 rounded">
        <X className="w-4 h-4 text-slate-400" />
      </button>
    </div>
  );
};

const DataStudioPage = () => {
  const [activeKeywords, setActiveKeywords] = useState<Set<string>>(new Set(['kw-1', 'kw-2']));
  const [selectedSnapshot, setSelectedSnapshot] = useState('snap-2');
  const [viewMode, setViewMode] = useState<'single' | 'compare'>('single');
  const [chatOpen, setChatOpen] = useState(false);
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>([
    { id: 'step-1', order: 1, name: 'Handle Missing Values', type: 'missing', params: { method: 'fill_mean' } },
    { id: 'step-2', order: 2, name: 'Remove Outliers', type: 'outlier', params: { method: 'iqr', threshold: 1.5 } },
  ]);
  const [, setUploading] = useState(false);

  const toggleKeyword = (id: string) => {
    const newSet = new Set(activeKeywords);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setActiveKeywords(newSet);
  };

  const activeColumns = useMemo(() => {
    return mockKeywords
      .filter(kw => activeKeywords.has(kw.id))
      .flatMap(kw => kw.columns);
  }, [activeKeywords]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', file.name);
      formData.append('process_type', 'etch');

      const response = await fetch('/api/v1/viz/sources/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Upload successful:', data);
        // Refresh dataset list or update UI
      }
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleRunPipeline = async () => {
    try {
      // Call backend to run pipeline
      const response = await apiPost('/api/v1/viz/pipeline/run', {
        source_id: mockDataset.id,
        snapshot_id: selectedSnapshot,
        steps: pipelineSteps
      });
      console.log('Pipeline run:', response);
    } catch (error) {
      console.error('Pipeline run failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
      {/* TopBar */}
      <div className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Database className="w-6 h-6 text-blue-400" />
            <div>
              <h1 className="text-lg font-bold text-white">Visualization Automation Studio</h1>
              <p className="text-sm text-slate-400">{mockDataset.name} • {mockDataset.rowCount.toLocaleString()} rows</p>
            </div>
          </div>
          <div className="flex gap-2">
            <label className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white text-sm font-medium flex items-center gap-2 cursor-pointer">
              <Upload className="w-4 h-4" />
              Upload
              <input type="file" accept=".csv,.parquet" onChange={handleFileUpload} className="hidden" />
            </label>
            <button className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white text-sm font-medium flex items-center gap-2">
              <Download className="w-4 h-4" />
              Export
            </button>
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm font-medium flex items-center gap-2">
              <Save className="w-4 h-4" />
              Save View
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel */}
        <div className="w-64 bg-slate-800 border-r border-slate-700 p-4 overflow-y-auto">
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Database className="w-4 h-4" />
              Schema ({mockDataset.columnCount})
            </h3>
            <div className="space-y-2">
              {mockDataset.columns.slice(0, 6).map(col => (
                <div 
                  key={col.name}
                  className={`p-2 rounded-lg border ${
                    activeColumns.includes(col.name) 
                      ? 'bg-blue-500/20 border-blue-500' 
                      : 'bg-slate-900 border-slate-700'
                  }`}
                >
                  <p className="text-xs font-medium text-white">{col.name}</p>
                  <p className="text-xs text-slate-400">{col.type}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                Keywords
              </h3>
              <button className="text-xs text-blue-400 hover:text-blue-300">
                Extract
              </button>
            </div>
            <div className="space-y-2">
              {mockKeywords.map(kw => (
                <KeywordToggle 
                  key={kw.id}
                  keyword={kw}
                  active={activeKeywords.has(kw.id)}
                  onToggle={() => toggleKeyword(kw.id)}
                />
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-white mb-3">Snapshots</h3>
            <div className="space-y-2">
              {mockSnapshots.map(snap => (
                <button
                  key={snap.id}
                  onClick={() => setSelectedSnapshot(snap.id)}
                  className={`w-full text-left p-3 rounded-lg border ${
                    selectedSnapshot === snap.id
                      ? 'bg-blue-500/20 border-blue-500'
                      : 'bg-slate-900 border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-white capitalize">{snap.stage}</span>
                    <span className="text-xs text-slate-400">{snap.timestamp}</span>
                  </div>
                  <p className="text-xs text-slate-400">{snap.rowCount.toLocaleString()} rows</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Main Canvas */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* View Mode Switcher */}
          <div className="bg-slate-800 border-b border-slate-700 px-6 py-3 flex items-center justify-between">
            <div className="flex gap-2">
              <button
                onClick={() => setViewMode('single')}
                className={`px-3 py-1 rounded text-sm font-medium ${
                  viewMode === 'single' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-slate-700 text-slate-400'
                }`}
              >
                Single View
              </button>
              <button
                onClick={() => setViewMode('compare')}
                className={`px-3 py-1 rounded text-sm font-medium ${
                  viewMode === 'compare' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-slate-700 text-slate-400'
                }`}
              >
                Compare View
              </button>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Grid3x3 className="w-4 h-4" />
              <span>2x2 Grid</span>
            </div>
          </div>

          {/* Plot Grid */}
          <div className="flex-1 p-6 overflow-y-auto">
            <div className="grid grid-cols-2 gap-4">
              <PlotCard title="Pressure Distribution" type="histogram">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={mockChartData.slice(0, 20)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="index" stroke="#9ca3af" tick={{ fontSize: 10 }} />
                    <YAxis stroke="#9ca3af" tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} />
                    <Bar dataKey="pressure" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </PlotCard>

              <PlotCard title="Temperature vs Pressure" type="scatter">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="pressure" stroke="#9ca3af" tick={{ fontSize: 10 }} />
                    <YAxis dataKey="temperature" stroke="#9ca3af" tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} />
                    <Scatter data={mockChartData} fill="#10b981" />
                  </ScatterChart>
                </ResponsiveContainer>
              </PlotCard>

              <PlotCard title="Temperature Trend" type="line">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={mockChartData.slice(0, 50)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="index" stroke="#9ca3af" tick={{ fontSize: 10 }} />
                    <YAxis stroke="#9ca3af" tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} />
                    <Line type="monotone" dataKey="temperature" stroke="#f59e0b" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </PlotCard>

              <PlotCard title="Power Levels" type="boxplot">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={mockChartData.slice(0, 20)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="index" stroke="#9ca3af" tick={{ fontSize: 10 }} />
                    <YAxis stroke="#9ca3af" tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} />
                    <Bar dataKey="power" fill="#8b5cf6" />
                  </BarChart>
                </ResponsiveContainer>
              </PlotCard>
            </div>
          </div>
        </div>

        {/* Right Panel */}
        <div className="w-80 bg-slate-800 border-l border-slate-700 p-4 overflow-y-auto">
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Play className="w-4 h-4" />
              Pipeline Builder
            </h3>
            <div className="space-y-2 mb-3">
              {pipelineSteps.map(step => (
                <PipelineStepCard 
                  key={step.id}
                  step={step}
                  onRemove={() => setPipelineSteps(steps => steps.filter(s => s.id !== step.id))}
                />
              ))}
            </div>
            <button 
              onClick={handleRunPipeline}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm font-medium flex items-center justify-center gap-2"
            >
              <Play className="w-4 h-4" />
              Run Pipeline
            </button>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-white mb-3">Metrics</h3>
            <div className="space-y-3">
              <div className="p-3 bg-slate-900 rounded-lg border border-slate-700">
                <p className="text-xs text-slate-400">Missing Values</p>
                <p className="text-lg font-bold text-white">2.7%</p>
              </div>
              <div className="p-3 bg-slate-900 rounded-lg border border-slate-700">
                <p className="text-xs text-slate-400">Outliers Detected</p>
                <p className="text-lg font-bold text-yellow-400">156</p>
              </div>
              <div className="p-3 bg-slate-900 rounded-lg border border-slate-700">
                <p className="text-xs text-slate-400">Data Quality Score</p>
                <p className="text-lg font-bold text-green-400">87/100</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Chat Drawer */}
      <div className={`bg-slate-800 border-t border-slate-700 transition-all ${chatOpen ? 'h-96' : 'h-12'}`}>
        <button 
          onClick={() => setChatOpen(!chatOpen)}
          className="w-full px-6 py-3 flex items-center justify-between hover:bg-slate-700"
        >
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-blue-400" />
            <span className="font-semibold text-white">AI Assistant & Chat</span>
          </div>
          {chatOpen ? <ChevronDown className="w-5 h-5 text-slate-400" /> : <ChevronUp className="w-5 h-5 text-slate-400" />}
        </button>

        {chatOpen && (
          <div className="px-6 pb-4">
            <div className="mb-4">
              <p className="text-sm text-slate-400 mb-3">Quick Prompts:</p>
              <div className="flex flex-wrap gap-2">
                {promptTemplates.slice(0, 6).map((template, idx) => (
                  <button 
                    key={idx}
                    className="px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded-lg text-xs text-white"
                  >
                    {template.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-slate-900 rounded-lg p-4 h-48 mb-3 overflow-y-auto">
              <div className="mb-4">
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">AI</div>
                  <div className="flex-1 bg-slate-800 rounded-lg p-3">
                    <p className="text-sm text-white">I've analyzed your current dataset. The pressure and temperature data show strong correlation (r=0.87). Would you like me to explain the drift patterns I detected?</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              <input 
                type="text"
                placeholder="Ask about your data..."
                className="flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400"
              />
              <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium">
                Send
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DataStudioPage;
