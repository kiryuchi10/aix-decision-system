import React, { useState, useEffect } from 'react';
import { BarChart3, AlertCircle, TrendingUp } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [violations, setViolations] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadChart();
    loadViolations();
  }, [selectedEntity, selectedEntityId, selectedMetric, chartType]);

  const loadChart = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/spc/chart`, {
        entity_type: selectedEntity,
        entity_id: selectedEntityId,
        metric_name: selectedMetric,
        chart_type: chartType,
        subgroup_size: 5,
        data_range_hours: 24
      });
      setChartData(response.data);
    } catch (error) {
      console.error('Failed to load chart:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadViolations = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/spc/violations`, {
        params: { range_hours: 24, entity_type: selectedEntity, entity_id: selectedEntityId }
      });
      setViolations(response.data);
    } catch (error) {
      console.error('Failed to load violations:', error);
    }
  };

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
                <div className="text-sm text-slate-400 mb-2">Chart Placeholder</div>
                <div className="h-64 bg-slate-800 rounded flex items-center justify-center text-slate-500">
                  Chart visualization (Plotly/Recharts integration needed)
                </div>
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
