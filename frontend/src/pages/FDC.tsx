import React, { useState, useEffect } from 'react';
import { AlertTriangle, Activity, TrendingDown, CheckCircle, XCircle } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface Alarm {
  id: string;
  timestamp: string;
  severity: string;
  type: string;
  parameter: string;
  current_value: number;
  threshold_value: number;
  sigma_distance: number;
  yield_impact: number;
  status: string;
}

const FDCPage: React.FC = () => {
  const [timeRange, setTimeRange] = useState('24h');
  const [alarms, setAlarms] = useState<Alarm[]>([]);
  const [processCapability, setProcessCapability] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAlarms();
    loadProcessCapability();
    const interval = setInterval(() => {
      loadAlarms();
      loadProcessCapability();
    }, 5000);
    return () => clearInterval(interval);
  }, [timeRange]);

  const loadAlarms = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/fdc/alarms/active`);
      setAlarms(response.data);
    } catch (error) {
      console.error('Failed to load alarms:', error);
    }
  };

  const loadProcessCapability = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/fdc/process-capability`);
      setProcessCapability(response.data);
    } catch (error) {
      console.error('Failed to load process capability:', error);
    }
  };

  const handleAck = async (alarmId: string) => {
    try {
      await axios.post(`${API_BASE_URL}/api/v1/fdc/alarms/${alarmId}/ack`);
      loadAlarms();
    } catch (error) {
      console.error('Failed to acknowledge alarm:', error);
    }
  };

  const handleResolve = async (alarmId: string) => {
    try {
      await axios.post(`${API_BASE_URL}/api/v1/fdc/alarms/${alarmId}/resolve`);
      loadAlarms();
    } catch (error) {
      console.error('Failed to resolve alarm:', error);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'bg-red-500/20 border-red-500 text-red-400';
      case 'HIGH': return 'bg-orange-500/20 border-orange-500 text-orange-400';
      case 'MEDIUM': return 'bg-yellow-500/20 border-yellow-500 text-yellow-400';
      case 'LOW': return 'bg-blue-500/20 border-blue-500 text-blue-400';
      default: return 'bg-slate-500/20 border-slate-500 text-slate-400';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'GRADUAL_DRIFT': return 'text-yellow-400';
      case 'STEP_CHANGE': return 'text-red-400';
      case 'INTERMITTENT': return 'text-orange-400';
      default: return 'text-slate-400';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <AlertTriangle className="w-8 h-8" />
            FDC Drift Sentinel
          </h1>
          <p className="text-slate-400 mt-1">Fault Detection and Classification - Real-time Drift Monitoring</p>
        </div>
        <div className="flex gap-2">
          {['1h', '6h', '24h'].map(range => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                timeRange === range
                  ? 'bg-cyan-600 text-white'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Process Capability */}
      {processCapability && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <div className="text-sm text-slate-400">Process Cpk</div>
            <div className="text-3xl font-bold text-cyan-400 mt-2">{processCapability.cpk.toFixed(2)}</div>
          </div>
          <div className="card">
            <div className="text-sm text-slate-400">Process Cp</div>
            <div className="text-3xl font-bold text-cyan-400 mt-2">{processCapability.cp.toFixed(2)}</div>
          </div>
          <div className="card">
            <div className="text-sm text-slate-400">Drift Rate</div>
            <div className="text-3xl font-bold text-yellow-400 mt-2">{processCapability.drift_rate.toFixed(3)}</div>
          </div>
          <div className="card">
            <div className="text-sm text-slate-400">Yield Estimate</div>
            <div className="text-3xl font-bold text-green-400 mt-2">{processCapability.yield_estimate.toFixed(1)}%</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Alarms */}
        <div className="lg:col-span-2 card">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Active Alarms ({alarms.filter(a => a.status === 'ACTIVE').length})
          </h2>
          {alarms.length > 0 ? (
            <div className="space-y-3">
              {alarms.map((alarm) => (
                <div key={alarm.id} className={`border rounded-lg p-4 ${getSeverityColor(alarm.severity)}`}>
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="font-bold text-white">{alarm.parameter}</div>
                      <div className={`text-sm ${getTypeColor(alarm.type)}`}>{alarm.type.replace('_', ' ')}</div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${getSeverityColor(alarm.severity)}`}>
                      {alarm.severity}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
                    <div>
                      <div className="text-slate-400">Current Value</div>
                      <div className="text-white font-semibold">{alarm.current_value.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-slate-400">Threshold</div>
                      <div className="text-white font-semibold">{alarm.threshold_value.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-slate-400">Sigma Distance</div>
                      <div className="text-white font-semibold">{alarm.sigma_distance.toFixed(2)}σ</div>
                    </div>
                    <div>
                      <div className="text-slate-400">Yield Impact</div>
                      <div className="text-red-400 font-semibold">{alarm.yield_impact.toFixed(1)}%</div>
                    </div>
                  </div>
                  <div className="flex gap-2 mt-4">
                    {alarm.status === 'ACTIVE' && (
                      <>
                        <button
                          onClick={() => handleAck(alarm.id)}
                          className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 rounded text-sm font-semibold flex items-center gap-1"
                        >
                          <CheckCircle className="w-4 h-4" />
                          Acknowledge
                        </button>
                        <button
                          onClick={() => handleResolve(alarm.id)}
                          className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-sm font-semibold flex items-center gap-1"
                        >
                          <XCircle className="w-4 h-4" />
                          Resolve
                        </button>
                      </>
                    )}
                    {alarm.status === 'ACKNOWLEDGED' && (
                      <button
                        onClick={() => handleResolve(alarm.id)}
                        className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-sm font-semibold flex items-center gap-1"
                      >
                        <XCircle className="w-4 h-4" />
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400">
              <CheckCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No active alarms</p>
            </div>
          )}
        </div>

        {/* Drift Chart Placeholder */}
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-4">Drift Detection</h2>
          <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
            <div className="h-64 bg-slate-800 rounded flex items-center justify-center text-slate-500">
              Drift chart visualization (Plotly/Recharts integration needed)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FDCPage;
