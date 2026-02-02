import React, { useState, useMemo } from 'react';
import { BarChart3, AlertCircle, RefreshCw, Download } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { getSpcViolations } from '../features/spc/spc.api';

// Mock data generator
const generateControlChartData = (type: string) => {
  const points = 100;
  const baseValue = 850;
  const data = [];
  
  for (let i = 0; i < points; i++) {
    const noise = Math.random() * 10 - 5;
    const drift = type === 'drift' ? (i / 20) : 0;
    const step = type === 'step' && i > 50 ? 10 : 0;
    const value = baseValue + noise + drift + step;
    
    data.push({
      index: i,
      value: value,
      timestamp: new Date(Date.now() - (points - i) * 60000).toLocaleTimeString(),
    });
  }
  return data;
};

const ControlChart = ({ data, chartType, limits }: { data: any[], chartType: string, limits: { ucl: number, lcl: number, cl: number } }) => {
  const { ucl, lcl, cl } = limits;

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Control Chart - {chartType}</h3>
        <div className="flex gap-2">
          <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors">
            <RefreshCw className="w-4 h-4 text-gray-400" />
          </button>
          <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors">
            <Download className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="index" 
            stroke="#9ca3af"
            label={{ value: 'Sample', position: 'insideBottom', offset: -5, fill: '#9ca3af' }}
          />
          <YAxis 
            stroke="#9ca3af"
            label={{ value: 'Value', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
            labelStyle={{ color: '#9ca3af' }}
          />
          <Legend />
          
          {/* Control Limits */}
          <ReferenceLine y={ucl} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'UCL', fill: '#ef4444', position: 'right' }} />
          <ReferenceLine y={cl} stroke="#3b82f6" strokeDasharray="3 3" label={{ value: 'CL', fill: '#3b82f6', position: 'right' }} />
          <ReferenceLine y={lcl} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'LCL', fill: '#ef4444', position: 'right' }} />
          
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke="#10b981" 
            strokeWidth={2}
            dot={{ fill: '#10b981', r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Chart Statistics */}
      <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-gray-700">
        <div>
          <p className="text-xs text-gray-400">Mean</p>
          <p className="text-lg font-semibold text-white">{cl.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">UCL</p>
          <p className="text-lg font-semibold text-red-400">{ucl.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">LCL</p>
          <p className="text-lg font-semibold text-red-400">{lcl.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Range</p>
          <p className="text-lg font-semibold text-white">{(ucl - lcl).toFixed(2)}</p>
        </div>
      </div>
    </div>
  );
};

const CapabilityCard = ({ title, value, status, trend }: { title: string, value: string, status: string, trend?: number }) => {
  const statusColors: Record<string, string> = {
    good: 'border-green-500 bg-green-500/10',
    warning: 'border-yellow-500 bg-yellow-500/10',
    critical: 'border-red-500 bg-red-500/10'
  };

  return (
    <div className={`border-2 rounded-xl p-4 ${statusColors[status]}`}>
      <p className="text-sm text-gray-400 mb-1">{title}</p>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-bold text-white">{value}</span>
      </div>
      {trend !== undefined && (
        <p className={`text-xs mt-2 ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
          {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% from target
        </p>
      )}
    </div>
  );
};

const ViolationRow = ({ violation }: { violation: any }) => {
  const severityColors: Record<string, string> = {
    HIGH: 'bg-red-500',
    MEDIUM: 'bg-yellow-500',
    LOW: 'bg-blue-500'
  };

  return (
    <div className="flex items-center gap-4 p-3 bg-gray-800 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors">
      <div className={`w-2 h-2 rounded-full ${severityColors[violation.severity] || 'bg-gray-500'}`}></div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-semibold text-white">{violation.rule_name}</span>
          <span className="text-xs text-gray-500">Point #{violation.point_index}</span>
        </div>
        <p className="text-xs text-gray-400">
          Value: {violation.point_value?.toFixed(2) || violation.value?.toFixed(2) || 'N/A'} | Time: {violation.detected_at || violation.timestamp || 'N/A'}
        </p>
      </div>
      <span className={`px-2 py-1 rounded text-xs font-medium ${severityColors[violation.severity] || 'bg-gray-500'} text-white`}>
        {violation.severity}
      </span>
    </div>
  );
};

const CpkTrendChart = ({ data }: { data: any[] }) => {
  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">Cpk Trend - Last 30 Days</h3>
      
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="date" stroke="#9ca3af" />
          <YAxis stroke="#9ca3af" domain={[0, 2]} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
          />
          <Legend />
          <ReferenceLine y={1.33} stroke="#10b981" strokeDasharray="3 3" label={{ value: 'Target', fill: '#10b981' }} />
          <ReferenceLine y={1.0} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'Min', fill: '#ef4444' }} />
          <Line type="monotone" dataKey="cpk" stroke="#3b82f6" strokeWidth={2} dot={{ fill: '#3b82f6', r: 4 }} />
          <Line type="monotone" dataKey="cp" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6', r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

const SPCPage: React.FC = () => {
  const [selectedEntity, setSelectedEntity] = useState('chamber');
  const [selectedMetric, setSelectedMetric] = useState('temperature');
  const [chartType, setChartType] = useState('xbar_r');
  const [timeRange, setTimeRange] = useState('24h');
  const [violations, setViolations] = useState<any[]>([]);

  // Generate mock data (will be replaced with API data)
  const controlData = useMemo(() => generateControlChartData('normal'), [selectedMetric]);
  
  const limits = {
    ucl: 865,
    cl: 850,
    lcl: 835
  };

  const capabilities = {
    cpk: { value: '1.45', status: 'good', trend: 3 },
    cp: { value: '1.52', status: 'good', trend: 2 },
    yield: { value: '96.2%', status: 'good', trend: 1.5 },
    sigma: { value: '4.5σ', status: 'warning', trend: -2 }
  };

  // Load violations from API
  React.useEffect(() => {
    const loadViolations = async () => {
      try {
        const data = await getSpcViolations(24, selectedEntity);
        setViolations(data);
      } catch (error) {
        console.error('Failed to load violations:', error);
        // Fallback to mock data
        setViolations([
          { id: 1, rule_name: 'Point beyond 3-sigma', point_index: 87, point_value: 866.5, severity: 'HIGH', detected_at: '2 min ago' },
          { id: 2, rule_name: '2 of 3 beyond 2-sigma', point_index: 72, point_value: 863.2, severity: 'MEDIUM', detected_at: '15 min ago' },
          { id: 3, rule_name: '8 points same side', point_index: 65, point_value: 852.1, severity: 'LOW', detected_at: '1 hr ago' },
          { id: 4, rule_name: 'Point beyond 3-sigma', point_index: 45, point_value: 833.8, severity: 'HIGH', detected_at: '2 hr ago' },
        ]);
      }
    };
    loadViolations();
  }, [selectedEntity]);

  const cpkTrendData = Array.from({ length: 30 }, (_, i) => ({
    date: new Date(Date.now() - (29 - i) * 86400000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    cpk: 1.35 + Math.random() * 0.3,
    cp: 1.45 + Math.random() * 0.3
  }));

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-blue-400" />
            <div>
              <h1 className="text-3xl font-bold text-white">SPC Center</h1>
              <p className="text-gray-400">Statistical Process Control & Capability Analysis</p>
            </div>
          </div>
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition-colors">
            Generate Report
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Entity Type</label>
            <select 
              value={selectedEntity}
              onChange={(e) => setSelectedEntity(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
            >
              <option value="chamber">Chamber</option>
              <option value="recipe">Recipe</option>
              <option value="lot">Lot</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm text-gray-400 mb-2">Metric</label>
            <select 
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
            >
              <option value="temperature">Temperature</option>
              <option value="pressure">Pressure</option>
              <option value="cd">Critical Dimension</option>
              <option value="uniformity">Uniformity</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Chart Type</label>
            <select 
              value={chartType}
              onChange={(e) => setChartType(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
            >
              <option value="xbar_r">Xbar-R</option>
              <option value="i_mr">I-MR</option>
              <option value="ewma">EWMA</option>
              <option value="cusum">CUSUM</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Time Range</label>
            <select 
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
            >
              <option value="1h">Last Hour</option>
              <option value="6h">Last 6 Hours</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Process Capability Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <CapabilityCard title="Cpk" {...capabilities.cpk} />
        <CapabilityCard title="Cp" {...capabilities.cp} />
        <CapabilityCard title="Yield" {...capabilities.yield} />
        <CapabilityCard title="Sigma Level" {...capabilities.sigma} />
      </div>

      {/* Control Chart */}
      <div className="mb-6">
        <ControlChart data={controlData} chartType={chartType} limits={limits} />
      </div>

      {/* Bottom Grid: Violations and Cpk Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Rule Violations */}
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-yellow-400" />
              <h3 className="text-lg font-semibold text-white">Rule Violations</h3>
            </div>
            <span className="text-sm text-gray-400">{violations.length} active</span>
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {violations.map((violation, idx) => (
              <ViolationRow key={violation.id || idx} violation={violation} />
            ))}
          </div>
        </div>

        {/* Cpk Trend */}
        <CpkTrendChart data={cpkTrendData} />
      </div>

      {/* Additional Metrics */}
      <div className="mt-6 bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Process Statistics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-400">Mean (μ)</p>
            <p className="text-2xl font-bold text-white">850.2</p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Std Dev (σ)</p>
            <p className="text-2xl font-bold text-white">5.3</p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Min Value</p>
            <p className="text-2xl font-bold text-white">832.1</p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Max Value</p>
            <p className="text-2xl font-bold text-white">868.5</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SPCPage;
