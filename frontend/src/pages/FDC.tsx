import React, { useState, useEffect, useMemo } from 'react';
import { Activity, AlertTriangle, CheckCircle, Clock, TrendingDown, TrendingUp, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area, AreaChart } from 'recharts';
import { useFdc } from '../features/fdc/useFdcAlarms';
import { acknowledgeAlarm, resolveAlarm } from '../features/fdc/fdc.api';

// Generate mock drift data
const generateDriftData = (type: string) => {
  const points = 150;
  const baseValue = 850;
  const data = [];
  
  for (let i = 0; i < points; i++) {
    let value = baseValue;
    const noise = (Math.random() - 0.5) * 3;
    
    if (type === 'gradual') {
      value += (i / 10) + noise;
    } else if (type === 'step') {
      value += (i > 75 ? 15 : 0) + noise;
    } else if (type === 'intermittent') {
      value += (i % 20 === 0 ? 12 : 0) + noise;
    } else {
      value += noise;
    }
    
    data.push({
      time: i,
      value: value,
      upper_limit: baseValue + 15,
      lower_limit: baseValue - 15,
      sigma_2: baseValue + 10,
      sigma_minus_2: baseValue - 10,
    });
  }
  return data;
};

const AlarmCard = ({ alarm, onAcknowledge, onResolve }: { alarm: any, onAcknowledge: (id: string) => void, onResolve: (id: string) => void }) => {
  const severityConfig: Record<string, { bg: string, border: string, text: string, icon: any }> = {
    HIGH: { bg: 'bg-red-500/10', border: 'border-red-500', text: 'text-red-400', icon: AlertTriangle },
    MEDIUM: { bg: 'bg-yellow-500/10', border: 'border-yellow-500', text: 'text-yellow-400', icon: AlertTriangle },
    LOW: { bg: 'bg-blue-500/10', border: 'border-blue-500', text: 'text-blue-400', icon: Activity },
    CRITICAL: { bg: 'bg-red-600/20', border: 'border-red-600', text: 'text-red-300', icon: Zap }
  };

  const config = severityConfig[alarm.severity] || severityConfig.MEDIUM;
  const Icon = config.icon;

  const typeIcons: Record<string, any> = {
    GRADUAL_DRIFT: TrendingUp,
    STEP_CHANGE: Activity,
    INTERMITTENT: Zap
  };
  const TypeIcon = typeIcons[alarm.type] || Activity;

  return (
    <div className={`${config.bg} border-2 ${config.border} rounded-xl p-6 transition-all hover:scale-[1.02]`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${config.bg}`}>
            <Icon className={`w-6 h-6 ${config.text}`} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white text-lg">{alarm.id}</span>
              <span className={`px-2 py-1 rounded text-xs font-medium ${config.bg} ${config.text} border ${config.border}`}>
                {alarm.severity}
              </span>
            </div>
            <p className="text-sm text-gray-400 mt-1">{alarm.timestamp}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <TypeIcon className="w-5 h-5 text-gray-400" />
          <span className="text-sm text-gray-400">{alarm.type.replace('_', ' ')}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-400">Parameter</p>
          <p className="text-sm font-semibold text-white">{alarm.parameter}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Current Value</p>
          <p className="text-sm font-semibold text-white">{alarm.current_value.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Threshold</p>
          <p className="text-sm font-semibold text-white">{alarm.threshold_value.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Sigma Distance</p>
          <p className={`text-sm font-semibold ${alarm.sigma_distance > 3 ? 'text-red-400' : 'text-yellow-400'}`}>
            {alarm.sigma_distance.toFixed(2)}σ
          </p>
        </div>
      </div>

      <div className="mb-4 p-3 bg-gray-800 rounded-lg border border-gray-700">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">Estimated Yield Impact</span>
          <span className={`text-sm font-bold ${alarm.yield_impact < 0 ? 'text-red-400' : 'text-green-400'}`}>
            {alarm.yield_impact > 0 ? '+' : ''}{alarm.yield_impact.toFixed(1)}%
          </span>
        </div>
      </div>

      {alarm.status === 'ACTIVE' && (
        <div className="flex gap-2">
          <button 
            onClick={() => onAcknowledge(alarm.id)}
            className="flex-1 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg text-white text-sm font-medium transition-colors"
          >
            Acknowledge
          </button>
          <button 
            onClick={() => onResolve(alarm.id)}
            className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white text-sm font-medium transition-colors"
          >
            Resolve
          </button>
        </div>
      )}

      {alarm.status === 'ACKNOWLEDGED' && (
        <div className="flex items-center gap-2 text-yellow-400">
          <Clock className="w-4 h-4" />
          <span className="text-sm">Acknowledged - Awaiting Resolution</span>
        </div>
      )}

      {alarm.status === 'RESOLVED' && (
        <div className="flex items-center gap-2 text-green-400">
          <CheckCircle className="w-4 h-4" />
          <span className="text-sm">Resolved</span>
        </div>
      )}
    </div>
  );
};

const DriftChart = ({ data, title, type }: { data: any[], title: string, type: string }) => {
  const getChartColor = () => {
    switch(type) {
      case 'gradual': return '#f59e0b';
      case 'step': return '#ef4444';
      case 'intermittent': return '#8b5cf6';
      default: return '#10b981';
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id={`gradient-${type}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={getChartColor()} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={getChartColor()} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="time" stroke="#9ca3af" />
          <YAxis stroke="#9ca3af" />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
          />
          <ReferenceLine y={850} stroke="#3b82f6" strokeDasharray="3 3" label="Target" />
          <ReferenceLine y={865} stroke="#ef4444" strokeDasharray="3 3" label="UCL" />
          <ReferenceLine y={835} stroke="#ef4444" strokeDasharray="3 3" label="LCL" />
          <Area 
            type="monotone" 
            dataKey="value" 
            stroke={getChartColor()} 
            fill={`url(#gradient-${type})`}
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

const ProcessCapabilityPanel = ({ metrics }: { metrics: any }) => {
  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">Process Capability Metrics</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-gray-900 rounded-lg border border-gray-700">
          <p className="text-sm text-gray-400 mb-1">Cpk</p>
          <p className="text-2xl font-bold text-white">{metrics.cpk}</p>
          <div className="mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-green-500 transition-all"
              style={{ width: `${Math.min((metrics.cpk / 2) * 100, 100)}%` }}
            />
          </div>
        </div>

        <div className="p-4 bg-gray-900 rounded-lg border border-gray-700">
          <p className="text-sm text-gray-400 mb-1">Cp</p>
          <p className="text-2xl font-bold text-white">{metrics.cp}</p>
          <div className="mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-blue-500 transition-all"
              style={{ width: `${Math.min((metrics.cp / 2) * 100, 100)}%` }}
            />
          </div>
        </div>

        <div className="p-4 bg-gray-900 rounded-lg border border-gray-700">
          <p className="text-sm text-gray-400 mb-1">Drift Rate</p>
          <p className="text-2xl font-bold text-yellow-400">{metrics.drift_rate}</p>
          <p className="text-xs text-gray-500 mt-1">σ/hour</p>
        </div>

        <div className="p-4 bg-gray-900 rounded-lg border border-gray-700">
          <p className="text-sm text-gray-400 mb-1">Yield Estimate</p>
          <p className="text-2xl font-bold text-green-400">{metrics.yield_estimate}%</p>
          <p className="text-xs text-gray-500 mt-1">Current</p>
        </div>
      </div>
    </div>
  );
};

const FDCPage: React.FC = () => {
  const { alarms: apiAlarms, cap: processCapability, loading } = useFdc();
  const [alarms, setAlarms] = useState<any[]>([]);
  const [filter, setFilter] = useState('ALL');

  // Initialize alarms from API or use mock
  useEffect(() => {
    if (apiAlarms && apiAlarms.length > 0) {
      setAlarms(apiAlarms);
    } else {
      // Fallback to mock data
      setAlarms([
        {
          id: 'ALM-001',
          timestamp: new Date().toLocaleString(),
          severity: 'HIGH',
          type: 'GRADUAL_DRIFT',
          parameter: 'Temperature',
          current_value: 865.2,
          threshold_value: 850.0,
          sigma_distance: 3.2,
          yield_impact: -4.2,
          status: 'ACTIVE'
        },
        {
          id: 'ALM-002',
          timestamp: new Date(Date.now() - 900000).toLocaleString(),
          severity: 'MEDIUM',
          type: 'STEP_CHANGE',
          parameter: 'Pressure',
          current_value: 2.65,
          threshold_value: 2.50,
          sigma_distance: 2.1,
          yield_impact: -2.1,
          status: 'ACKNOWLEDGED'
        },
        {
          id: 'ALM-003',
          timestamp: new Date(Date.now() - 3600000).toLocaleString(),
          severity: 'CRITICAL',
          type: 'INTERMITTENT',
          parameter: 'RF Power',
          current_value: 1850,
          threshold_value: 1800,
          sigma_distance: 4.5,
          yield_impact: -8.5,
          status: 'ACTIVE'
        }
      ]);
    }
  }, [apiAlarms]);

  const [processMetrics, setProcessMetrics] = useState({
    cpk: 1.24,
    cp: 1.48,
    drift_rate: 0.053,
    yield_estimate: 92.3
  });

  // Update metrics from API if available
  useEffect(() => {
    if (processCapability) {
      setProcessMetrics({
        cpk: processCapability.cpk,
        cp: processCapability.cp,
        drift_rate: processCapability.drift_rate,
        yield_estimate: processCapability.yield_estimate
      });
    }
  }, [processCapability]);

  const gradualData = useMemo(() => generateDriftData('gradual'), []);
  const stepData = useMemo(() => generateDriftData('step'), []);
  const intermittentData = useMemo(() => generateDriftData('intermittent'), []);

  const handleAcknowledge = async (alarmId: string) => {
    try {
      await acknowledgeAlarm(alarmId);
      setAlarms(prev => prev.map(alarm => 
        alarm.id === alarmId ? { ...alarm, status: 'ACKNOWLEDGED' } : alarm
      ));
    } catch (error) {
      console.error('Failed to acknowledge alarm:', error);
    }
  };

  const handleResolve = async (alarmId: string) => {
    try {
      await resolveAlarm(alarmId);
      setAlarms(prev => prev.map(alarm => 
        alarm.id === alarmId ? { ...alarm, status: 'RESOLVED' } : alarm
      ));
    } catch (error) {
      console.error('Failed to resolve alarm:', error);
    }
  };

  const filteredAlarms = filter === 'ALL' 
    ? alarms 
    : alarms.filter(a => a.status === filter);

  const alarmStats = {
    total: alarms.length,
    active: alarms.filter(a => a.status === 'ACTIVE').length,
    acknowledged: alarms.filter(a => a.status === 'ACKNOWLEDGED').length,
    resolved: alarms.filter(a => a.status === 'RESOLVED').length
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="w-8 h-8 text-purple-400" />
            <div>
              <h1 className="text-3xl font-bold text-white">FDC Drift Sentinel</h1>
              <p className="text-gray-400">Real-time Fault Detection & Classification</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <span className="text-sm text-gray-400">Live Monitoring</span>
          </div>
        </div>
      </div>

      {/* Process Capability */}
      <div className="mb-6">
        <ProcessCapabilityPanel metrics={processMetrics} />
      </div>

      {/* Alarm Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-800 border-2 border-gray-700 rounded-xl p-4">
          <p className="text-sm text-gray-400 mb-1">Total Alarms</p>
          <p className="text-3xl font-bold text-white">{alarmStats.total}</p>
        </div>
        <div className="bg-gray-800 border-2 border-red-500/30 rounded-xl p-4">
          <p className="text-sm text-gray-400 mb-1">Active</p>
          <p className="text-3xl font-bold text-red-400">{alarmStats.active}</p>
        </div>
        <div className="bg-gray-800 border-2 border-yellow-500/30 rounded-xl p-4">
          <p className="text-sm text-gray-400 mb-1">Acknowledged</p>
          <p className="text-3xl font-bold text-yellow-400">{alarmStats.acknowledged}</p>
        </div>
        <div className="bg-gray-800 border-2 border-green-500/30 rounded-xl p-4">
          <p className="text-sm text-gray-400 mb-1">Resolved</p>
          <p className="text-3xl font-bold text-green-400">{alarmStats.resolved}</p>
        </div>
      </div>

      {/* Drift Detection Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <DriftChart data={gradualData} title="Gradual Drift Detection" type="gradual" />
        <DriftChart data={stepData} title="Step Change Detection" type="step" />
        <DriftChart data={intermittentData} title="Intermittent Spike Detection" type="intermittent" />
      </div>

      {/* Active Alarms */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-white">Active Alarms</h3>
          <div className="flex gap-2">
            {['ALL', 'ACTIVE', 'ACKNOWLEDGED', 'RESOLVED'].map(status => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                  filter === status 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }`}
              >
                {status}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredAlarms.map(alarm => (
            <AlarmCard 
              key={alarm.id} 
              alarm={alarm}
              onAcknowledge={handleAcknowledge}
              onResolve={handleResolve}
            />
          ))}
        </div>

        {filteredAlarms.length === 0 && (
          <div className="text-center py-12">
            <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
            <p className="text-gray-400">No alarms in this category</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FDCPage;
