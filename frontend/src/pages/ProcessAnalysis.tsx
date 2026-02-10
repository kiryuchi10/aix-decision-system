import React, { useState, useEffect } from 'react';
import { Database, TrendingUp, BarChart3, FileText, Download, Calendar } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

function isNumericCol(rows: Record<string, string | number>[], col: string): boolean {
  if (!rows.length) return false;
  const v = rows[0][col];
  return typeof v === 'number' || (typeof v === 'string' && v !== '' && !Number.isNaN(Number(v)));
}

function computeCorrelationMatrix(
  rows: Record<string, string | number>[],
  columns: string[]
): number[][] {
  const numericCols = columns.filter((c) => isNumericCol(rows, c));
  const n = numericCols.length;
  if (n === 0) return [];
  const getNum = (r: Record<string, string | number>, c: string) => {
    const v = r[c];
    return typeof v === 'number' ? v : Number(v);
  };
  const mat = numericCols.map((c) => rows.map((r) => getNum(r, c)));
  const corr: number[][] = Array(n)
    .fill(0)
    .map(() => Array(n).fill(0));
  for (let i = 0; i < n; i++) {
    corr[i][i] = 1;
    for (let j = i + 1; j < n; j++) {
      const a = mat[i];
      const b = mat[j];
      const meanA = a.reduce((s, x) => s + x, 0) / a.length;
      const meanB = b.reduce((s, x) => s + x, 0) / b.length;
      let num = 0,
        denA = 0,
        denB = 0;
      for (let k = 0; k < a.length; k++) {
        const da = a[k] - meanA;
        const db = b[k] - meanB;
        num += da * db;
        denA += da * da;
        denB += db * db;
      }
      const r = denA && denB ? num / Math.sqrt(denA * denB) : 0;
      corr[i][j] = r;
      corr[j][i] = r;
    }
  }
  return corr;
}

// Generate mock process data (fallback when no seed data)
const generateProcessData = (metric: string, days = 7) => {
  const data = [];
  const baseValues: Record<string, number> = {
    temperature: 850,
    pressure: 2.5,
    gas_flow: 150,
    rf_power: 1800,
    etch_rate: 450
  };
  
  for (let i = 0; i < days * 24; i++) {
    const base = baseValues[metric] || 100;
    const trend = i * 0.1;
    const noise = (Math.random() - 0.5) * (base * 0.05);
    
    data.push({
      time: new Date(Date.now() - (days * 24 - i) * 3600000).toLocaleString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit' 
      }),
      value: base + trend + noise,
      min: base - base * 0.1,
      max: base + base * 0.1,
      target: base
    });
  }
  return data;
};

const StatCard = ({ title, value, unit, change, icon: Icon, color }: { 
  title: string, 
  value: string | number, 
  unit?: string, 
  change?: number, 
  icon: any, 
  color: string 
}) => {
  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-lg ${color} bg-opacity-20`}>
          <Icon className={`w-6 h-6 ${color.replace('bg-', 'text-')}`} />
        </div>
        {change !== undefined && (
          <span className={`text-sm font-medium ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {change >= 0 ? '↑' : '↓'} {Math.abs(change).toFixed(1)}%
          </span>
        )}
      </div>
      <h3 className="text-sm text-gray-400 mb-1">{title}</h3>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-bold text-white">{value}</span>
        {unit && <span className="text-lg text-gray-400">{unit}</span>}
      </div>
    </div>
  );
};

const TrendChart = ({ data, metric, color }: { data: any[], metric: string, color: string }) => {
  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white capitalize">{metric} Trend</h3>
        <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors">
          <Download className="w-4 h-4 text-gray-400" />
        </button>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="time" 
            stroke="#9ca3af"
            tick={{ fontSize: 10 }}
            interval={Math.floor(data.length / 10)}
          />
          <YAxis stroke="#9ca3af" />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1f2937', 
              border: '1px solid #374151', 
              borderRadius: '8px' 
            }}
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="target" 
            stroke="#6b7280" 
            strokeDasharray="5 5"
            strokeWidth={2}
            dot={false}
            name="Target"
          />
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke={color} 
            strokeWidth={2}
            dot={false}
            name="Actual"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

const DistributionChart = ({ data, metric }: { data: any[], metric: string }) => {
  // Create histogram bins
  const values = data.map(d => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const binCount = 20;
  const binSize = (max - min) / binCount;
  
  const histogram = Array.from({ length: binCount }, (_, i) => {
    const binStart = min + i * binSize;
    const binEnd = binStart + binSize;
    const count = values.filter(v => v >= binStart && v < binEnd).length;
    return {
      range: `${binStart.toFixed(1)}-${binEnd.toFixed(1)}`,
      count: count,
      binCenter: (binStart + binEnd) / 2
    };
  });

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4 capitalize">{metric} Distribution</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={histogram}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="binCenter" stroke="#9ca3af" tick={{ fontSize: 10 }} />
          <YAxis stroke="#9ca3af" />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1f2937', 
              border: '1px solid #374151', 
              borderRadius: '8px' 
            }}
          />
          <Bar dataKey="count" fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

const StatisticsTable = ({ data, metric: _metric }: { data: any[]; metric: string }) => {
  const values = data.map(d => d.value);
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const sorted = [...values].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min;
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
  const stdDev = Math.sqrt(variance);
  const cv = (stdDev / mean) * 100;

  const stats = [
    { label: 'Count', value: values.length.toLocaleString() },
    { label: 'Mean', value: mean.toFixed(2) },
    { label: 'Median', value: median.toFixed(2) },
    { label: 'Std Dev', value: stdDev.toFixed(2) },
    { label: 'Min', value: min.toFixed(2) },
    { label: 'Max', value: max.toFixed(2) },
    { label: 'Range', value: range.toFixed(2) },
    { label: 'CV (%)', value: cv.toFixed(2) },
  ];

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">Statistical Summary</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((stat, idx) => (
          <div key={idx} className="p-4 bg-gray-900 rounded-lg border border-gray-700">
            <p className="text-xs text-gray-400 mb-1">{stat.label}</p>
            <p className="text-xl font-bold text-white">{stat.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

const CorrelationMatrix = ({
  metrics,
  seedData,
}: {
  metrics: string[];
  seedData?: { columns: string[]; rows: Record<string, string | number>[] } | null;
}) => {
  const useReal = seedData?.rows?.length && seedData?.columns?.length;
  const numericCols = useReal
    ? seedData!.columns.filter((c) => isNumericCol(seedData!.rows, c)).slice(0, 12)
    : metrics.slice(0, 12);
  const corrMatrix = useReal
    ? computeCorrelationMatrix(seedData!.rows, numericCols)
    : null;
  const correlationData =
    corrMatrix !== null
      ? numericCols.flatMap((_, i) =>
          numericCols.map((_, j) => ({
            x: numericCols[i],
            y: numericCols[j],
            value: corrMatrix[i][j],
          }))
        )
      : numericCols.flatMap((m1, i) =>
          numericCols.map((m2, j) => ({
            x: m1,
            y: m2,
            value: i === j ? 1.0 : Math.random() * 2 - 1,
          }))
        );

  const getColor = (value: number) => {
    if (value > 0.7) return '#10b981';
    if (value > 0.3) return '#3b82f6';
    if (value > -0.3) return '#6b7280';
    if (value > -0.7) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">
        Correlation Matrix
        {useReal && (
          <span className="ml-2 text-xs font-normal text-green-400">(from seed data)</span>
        )}
      </h3>
      <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${numericCols.length}, 1fr)` }}>
        {correlationData.map((item, idx) => (
          <div 
            key={idx}
            className="aspect-square rounded flex items-center justify-center text-xs font-semibold"
            style={{ backgroundColor: getColor(item.value) }}
            title={`${item.x} vs ${item.y}: ${item.value.toFixed(2)}`}
          >
            {item.value.toFixed(2)}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-700">
        <span className="text-xs text-gray-400">Correlation:</span>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-500"></div>
          <span className="text-xs text-gray-400">-1.0</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-gray-500"></div>
          <span className="text-xs text-gray-400">0.0</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-green-500"></div>
          <span className="text-xs text-gray-400">+1.0</span>
        </div>
      </div>
    </div>
  );
};

interface SeedFolderInfo {
  id: string;
  path: string;
  process_type: string;
  columns: string[];
  row_count?: number;
}

const ProcessAnalysisPage: React.FC = () => {
  const [selectedMetric, setSelectedMetric] = useState('temperature');
  const [timeRange, setTimeRange] = useState(7);
  const [seedFolders, setSeedFolders] = useState<SeedFolderInfo[]>([]);
  const [selectedSeedPath, setSelectedSeedPath] = useState<string | null>(null);
  const [seedData, setSeedData] = useState<{ columns: string[]; rows: Record<string, string | number>[] } | null>(null);
  const [seedLoading, setSeedLoading] = useState(false);
  const [seedError, setSeedError] = useState<string | null>(null);
  const [foldersError, setFoldersError] = useState<string | null>(null);

  const metricsFromSeed = seedData?.columns?.filter(c => c !== 'timestamp') || ['temperature', 'pressure', 'gas_flow', 'rf_power', 'etch_rate'];
  const metrics = seedData ? metricsFromSeed : ['temperature', 'pressure', 'gas_flow', 'rf_power', 'etch_rate'];

  useEffect(() => {
    setFoldersError(null);
    fetch(`${API_BASE}/api/v1/seeds/folders`, { credentials: 'include' })
      .then((res) => {
        if (!res.ok) {
          setFoldersError(res.status === 401 ? 'Sign in required' : `Failed to load folders (${res.status})`);
          return [];
        }
        return res.json();
      })
      .then((list: SeedFolderInfo[]) => {
        setSeedFolders(list);
        if (list.length > 0 && !selectedSeedPath) setSelectedSeedPath(list[0].path);
      })
      .catch(() => {
        setFoldersError('Cannot reach server');
        setSeedFolders([]);
      });
  }, []);

  useEffect(() => {
    if (!selectedSeedPath) {
      setSeedData(null);
      setSeedError(null);
      return;
    }
    setSeedLoading(true);
    setSeedError(null);
    fetch(`${API_BASE}/api/v1/seeds/folders/${encodeURIComponent(selectedSeedPath)}/data?limit=5000`, {
      credentials: 'include',
    })
      .then((res) => {
        if (!res.ok) {
          const msg = res.status === 404 ? 'No data for this folder' : res.status === 401 ? 'Sign in required' : `Error ${res.status}`;
          setSeedError(msg);
          setSeedData(null);
          return null;
        }
        return res.json();
      })
      .then((data: { columns: string[]; rows: Record<string, string | number>[] } | null) => {
        if (data) setSeedData(data);
      })
      .catch(() => {
        setSeedError('Failed to load seed data');
        setSeedData(null);
      })
      .finally(() => setSeedLoading(false));
  }, [selectedSeedPath]);

  const processDataFromSeed = (metric: string): { time: string; value: number; target: number; min: number; max: number }[] => {
    if (!seedData?.rows?.length || !seedData.columns.includes(metric)) return [];
    const num = seedData.rows.map(r => Number(r[metric]));
    const target = num.length ? num.reduce((a, b) => a + b, 0) / num.length : 0;
    const min = Math.min(...num);
    const max = Math.max(...num);
    return seedData.rows.slice(0, 500).map((row, i) => ({
      time: String(row['timestamp'] ?? row['time'] ?? i),
      value: Number(row[metric]),
      target,
      min,
      max,
    }));
  };

  const processData = seedData && metrics.includes(selectedMetric)
    ? processDataFromSeed(selectedMetric)
    : generateProcessData(selectedMetric, timeRange);

  const summaryStats = {
    dataPoints: processData.length * metrics.length,
    avgYield: seedData?.rows?.length
      ? (seedData.rows.reduce((s, r) => s + Number(r['yield'] ?? r['y'] ?? 0), 0) / seedData.rows.length).toFixed(1)
      : 94.2,
    processUptime: 98.7,
    alarmsToday: 3
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Database className="w-8 h-8 text-green-400" />
            <div>
              <h1 className="text-3xl font-bold text-white">Process Data Analysis</h1>
              <p className="text-gray-400">Comprehensive data summaries and statistical reports</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition-colors flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Generate Report
            </button>
            <button className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white font-medium transition-colors flex items-center gap-2">
              <Download className="w-4 h-4" />
              Export Data
            </button>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Select Metric</label>
            <select 
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
            >
              {metrics.map(m => (
                <option key={m} value={m} className="capitalize">
                  {m.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm text-gray-400 mb-2">Time Range</label>
            <select 
              value={timeRange}
              onChange={(e) => setTimeRange(Number(e.target.value))}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
            >
              <option value={1}>Last 24 Hours</option>
              <option value={3}>Last 3 Days</option>
              <option value={7}>Last 7 Days</option>
              <option value={30}>Last 30 Days</option>
            </select>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-2">
              <label className="block text-sm text-gray-400">Data source (seed)</label>
              <span
                className={`text-xs font-medium px-2 py-0.5 rounded ${
                  seedData ? 'bg-green-900/50 text-green-400' : 'bg-gray-700 text-gray-400'
                }`}
              >
                {seedData ? 'REAL (seed)' : 'MOCK'}
              </span>
            </div>
            <select
              value={selectedSeedPath ?? ''}
              onChange={(e) => setSelectedSeedPath(e.target.value || null)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
            >
              <option value="">Mock data</option>
              {seedFolders.map((f) => (
                <option key={f.id} value={f.path}>
                  {f.path} ({f.row_count ?? '?'} rows)
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
      {foldersError && (
        <div className="mb-4 p-3 rounded-lg bg-amber-900/30 border border-amber-700 text-amber-200 text-sm">
          {foldersError}
        </div>
      )}
      {seedLoading && <p className="text-sm text-gray-400 mb-2">Loading seed data...</p>}
      {seedError && selectedSeedPath && (
        <div className="mb-4 p-3 rounded-lg bg-red-900/30 border border-red-700 text-red-200 text-sm">
          {seedError}
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <StatCard 
          title="Total Data Points" 
          value={summaryStats.dataPoints.toLocaleString()} 
          icon={Database}
          color="bg-blue-500"
        />
        <StatCard 
          title="Average Yield" 
          value={summaryStats.avgYield} 
          unit="%" 
          change={1.2}
          icon={TrendingUp}
          color="bg-green-500"
        />
        <StatCard 
          title="Process Uptime" 
          value={summaryStats.processUptime} 
          unit="%" 
          change={0.5}
          icon={BarChart3}
          color="bg-purple-500"
        />
        <StatCard 
          title="Alarms Today" 
          value={summaryStats.alarmsToday} 
          change={-15}
          icon={Calendar}
          color="bg-orange-500"
        />
      </div>

      {/* Main Trend Chart */}
      <div className="mb-6">
        <TrendChart 
          data={processData} 
          metric={selectedMetric}
          color="#10b981"
        />
      </div>

      {/* Distribution and Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <DistributionChart data={processData} metric={selectedMetric} />
        <StatisticsTable data={processData} metric={selectedMetric} />
      </div>

      {/* Correlation Matrix */}
      <div className="mb-6">
        <CorrelationMatrix metrics={metrics} seedData={seedData} />
      </div>

      {/* Export Options */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Export Options</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="p-4 bg-gray-700 hover:bg-gray-600 rounded-lg border border-gray-600 transition-colors">
            <FileText className="w-6 h-6 text-blue-400 mx-auto mb-2" />
            <p className="text-white font-medium">Export as CSV</p>
            <p className="text-xs text-gray-400 mt-1">Raw data export</p>
          </button>
          <button className="p-4 bg-gray-700 hover:bg-gray-600 rounded-lg border border-gray-600 transition-colors">
            <BarChart3 className="w-6 h-6 text-green-400 mx-auto mb-2" />
            <p className="text-white font-medium">Export as Excel</p>
            <p className="text-xs text-gray-400 mt-1">With charts and formatting</p>
          </button>
          <button className="p-4 bg-gray-700 hover:bg-gray-600 rounded-lg border border-gray-600 transition-colors">
            <FileText className="w-6 h-6 text-purple-400 mx-auto mb-2" />
            <p className="text-white font-medium">Generate PDF Report</p>
            <p className="text-xs text-gray-400 mt-1">Complete analysis report</p>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProcessAnalysisPage;
