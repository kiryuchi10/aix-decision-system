import React, { useState, useEffect, useMemo } from 'react';
import { BarChart3, AlertCircle, TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { useSpcChart } from '../features/spc/useSpcChart';
import { getSpcViolations } from '../features/spc/spc.api';

interface ChartData {
  chart_type: string;
  mean: number;
  std_dev: number;
  ucl: number;
  lcl: number;
  cl: number;
  cp?: number;
  cpk?: number;
  data_points: Array<{ index: number; value: number; timestamp: string }>;
  violations: Array<{ rule_number: number; rule_name: string; point_index: number; point_value: number; severity: string }>;
}

const SPCPage: React.FC = () => {
  const [selectedEntity, setSelectedEntity] = useState('chamber');
  const [selectedEntityId, setSelectedEntityId] = useState('CHAMBER-1');
  const [selectedMetric, setSelectedMetric] = useState('temperature');
  const [chartType, setChartType] = useState('xbar_r');
  const [violations, setViolations] = useState<any[]>([]);

  const chartRequest = useMemo(() => ({
    entity_type: selectedEntity,
    entity_id: selectedEntityId,
    metric_name: selectedMetric,
    chart_type: chartType,
    subgroup_size: 5,
    data_range_hours: 24,
  }), [selectedEntity, selectedEntityId, selectedMetric, chartType]);

  const { data: chartData, loading, error } = useSpcChart(chartRequest);

  useEffect(() => {
    loadViolations();
  }, [selectedEntity, selectedEntityId]);

  const loadViolations = async () => {
    try {
      const data = await getSpcViolations(24, selectedEntity, selectedEntityId);
      setViolations(data);
    } catch (error) {
      console.error('Failed to load violations:', error);
    }
  };

  const chartDataForRecharts = useMemo(() => {
    if (!chartData) return [];
    return chartData.data_points.map((pt) => ({
      index: pt.index,
      value: pt.value,
      timestamp: new Date(pt.timestamp).toLocaleTimeString(),
      ucl: chartData.ucl,
      lcl: chartData.lcl,
      cl: chartData.cl,
    }));
  }, [chartData]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <BarChart3 className="w-8 h-8" />
            SPC Center
          </h1>
          <p className="text-slate-400 mt-1">Statistical Process Control - Control Charts & Capability Analysis</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Entity Type</label>
          <select
            value={selectedEntity}
            onChange={(e) => setSelectedEntity(e.target.value)}
            className="w-full input-field"
          >
            <option value="chamber">Chamber</option>
            <option value="recipe">Recipe</option>
            <option value="lot">Lot</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Entity ID</label>
          <input
            type="text"
            value={selectedEntityId}
            onChange={(e) => setSelectedEntityId(e.target.value)}
            className="w-full input-field"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Metric</label>
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            className="w-full input-field"
          >
            <option value="temperature">Temperature</option>
            <option value="pressure">Pressure</option>
            <option value="cd">CD</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Chart Type</label>
          <select
            value={chartType}
            onChange={(e) => setChartType(e.target.value)}
            className="w-full input-field"
          >
            <option value="xbar_r">Xbar-R</option>
            <option value="i_mr">I-MR</option>
            <option value="ewma">EWMA</option>
            <option value="cusum">CUSUM</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Control Chart */}
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-4">Control Chart</h2>
          {loading ? (
            <div className="text-center py-12 text-slate-400">Loading chart...</div>
          ) : chartData ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-sm text-slate-400">Mean</div>
                  <div className="text-2xl font-bold text-white">{chartData.mean.toFixed(2)}</div>
                </div>
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-sm text-slate-400">UCL</div>
                  <div className="text-2xl font-bold text-red-400">{chartData.ucl.toFixed(2)}</div>
                </div>
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-sm text-slate-400">LCL</div>
                  <div className="text-2xl font-bold text-red-400">{chartData.lcl.toFixed(2)}</div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-sm text-slate-400">Cp</div>
                  <div className="text-2xl font-bold text-cyan-400">{chartData.cp?.toFixed(2) || 'N/A'}</div>
                </div>
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="text-sm text-slate-400">Cpk</div>
                  <div className="text-2xl font-bold text-cyan-400">{chartData.cpk?.toFixed(2) || 'N/A'}</div>
                </div>
              </div>
              <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
                <div className="text-sm text-slate-400 mb-2">Control Chart - {chartType.toUpperCase()}</div>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartDataForRecharts}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis 
                      dataKey="timestamp" 
                      stroke="#94a3b8"
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis 
                      stroke="#94a3b8"
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1e293b', 
                        border: '1px solid #334155',
                        borderRadius: '8px',
                        color: '#e2e8f0'
                      }}
                      labelStyle={{ color: '#94a3b8' }}
                    />
                    <Legend />
                    <ReferenceLine 
                      y={chartData.ucl} 
                      stroke="#ef4444" 
                      strokeDasharray="5 5" 
                      label={{ value: "UCL", position: "right", fill: "#ef4444" }}
                    />
                    <ReferenceLine 
                      y={chartData.cl} 
                      stroke="#3b82f6" 
                      strokeDasharray="5 5" 
                      label={{ value: "CL", position: "right", fill: "#3b82f6" }}
                    />
                    <ReferenceLine 
                      y={chartData.lcl} 
                      stroke="#ef4444" 
                      strokeDasharray="5 5" 
                      label={{ value: "LCL", position: "right", fill: "#ef4444" }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#06b6d4" 
                      strokeWidth={2}
                      dot={{ r: 3, fill: '#06b6d4' }}
                      name="Value"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400">No chart data</div>
          )}
        </div>

        {/* Violations */}
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Rule Violations
          </h2>
          {violations.length > 0 ? (
            <div className="space-y-2">
              {violations.slice(0, 10).map((v, idx) => (
                <div key={idx} className="bg-slate-800 rounded-lg p-3 border border-slate-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-white">{v.rule_name}</div>
                      <div className="text-sm text-slate-400">Point {v.point_index}: {v.point_value.toFixed(2)}</div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      v.severity === 'HIGH' ? 'bg-red-500/20 text-red-400' :
                      v.severity === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {v.severity}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400">No violations detected</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SPCPage;
