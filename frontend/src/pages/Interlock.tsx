import React, { useState } from 'react';
import { Shield, Play, CheckCircle, XCircle, FileText, RefreshCw } from 'lucide-react';
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

type Decision = 'NORMAL' | 'RELEASE' | 'STOP';

interface DecisionResult {
  decision: Decision;
  confidence: number;
  reason_ko?: string;
  reason_en?: string;
  suggested_action_ko?: string;
  suggested_action_en?: string;
  timestamp: string;
}

interface InterlockStatus {
  events_24h: number;
  release_count: number;
  stop_count: number;
  downtime_saved_hr: number;
  last_decision_at?: string;
}

const InterlockPage: React.FC = () => {
  const [decision, setDecision] = useState<DecisionResult | null>(null);
  const [status, setStatus] = useState<InterlockStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [reportPath, setReportPath] = useState<string | null>(null);

  const runDecision = async () => {
    setLoading(true);
    setDecision(null); // clear default so user sees "Running..."
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE}/api/v1/interlock/decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          interlock_detected: true,
          sensor_snapshot: { temp: 852, pressure: 2.6, rf_power: 1800 },
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data: DecisionResult = await res.json();
      setDecision(data);
      loadStatus();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE}/api/v1/interlock/status`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data: InterlockStatus = await res.json();
        setStatus(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const generateReport = async () => {
    setReportPath(null);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE}/api/v1/interlock/reports/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ title: 'Interlock Response Report', time_window: '24h' }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setReportPath(data.filepath || null);
    } catch (e) {
      console.error(e);
    }
  };

  React.useEffect(() => {
    loadStatus();
  }, []);

  const DecisionBadge = ({ d }: { d: Decision }) => {
    if (d === 'NORMAL')
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-slate-500/20 text-slate-300">
          <CheckCircle className="w-4 h-4" /> NORMAL
        </span>
      );
    if (d === 'RELEASE')
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-green-500/20 text-green-400">
          <CheckCircle className="w-4 h-4" /> Release (간단 점검 후)
        </span>
      );
    return (
      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-red-500/20 text-red-400">
        <XCircle className="w-4 h-4" /> STOP (설비 수리)
      </span>
    );
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
            <Shield className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">STOP/Release 판정 AI</h1>
            <p className="text-sm text-slate-400">Interlock 대응 · 설비 유실 시간 감축</p>
          </div>
        </div>
        <button
          onClick={loadStatus}
          className="p-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Status KPI */}
      {status && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="text-xs text-slate-400">Interlock (24h)</div>
            <div className="text-xl font-semibold text-white">{status.events_24h}</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="text-xs text-slate-400">Release</div>
            <div className="text-xl font-semibold text-green-400">{status.release_count}</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="text-xs text-slate-400">STOP</div>
            <div className="text-xl font-semibold text-red-400">{status.stop_count}</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="text-xs text-slate-400">Downtime saved (hr)</div>
            <div className="text-xl font-semibold text-blue-400">{status.downtime_saved_hr.toFixed(1)}</div>
          </div>
        </div>
      )}

      {/* Run decision */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 mb-6">
        <h2 className="text-lg font-semibold text-white mb-4">Run STOP/Release Decision (Stub)</h2>
        <p className="text-sm text-slate-400 mb-4">
          FDC 센서 데이터 → AI 판정 → Release (간단한 점검 후) / STOP (설비 수리)
        </p>
        <button
          onClick={runDecision}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg"
        >
          {loading ? (
            <span className="animate-pulse">Running...</span>
          ) : (
            <>
              <Play className="w-4 h-4" /> Run decision
            </>
          )}
        </button>

        {decision && (
          <div className="mt-6 p-4 bg-slate-900 rounded-lg border border-slate-600">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-slate-400">Decision</span>
              <DecisionBadge d={decision.decision} />
              <span className="text-slate-500 text-sm">confidence {(decision.confidence * 100).toFixed(0)}%</span>
            </div>
            {decision.reason_ko && (
              <p className="text-sm text-slate-300"><strong>KO:</strong> {decision.reason_ko}</p>
            )}
            {decision.reason_en && (
              <p className="text-sm text-slate-400"><strong>EN:</strong> {decision.reason_en}</p>
            )}
            {decision.suggested_action_ko && (
              <p className="text-sm text-blue-300 mt-2">권장: {decision.suggested_action_ko}</p>
            )}
          </div>
        )}
      </div>

      {/* Report */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
        <h2 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
          <FileText className="w-5 h-5" /> Interlock Report
        </h2>
        <p className="text-sm text-slate-400 mb-4">
          Generate HTML report with figures + KPI tables (Jinja2 template).
        </p>
        <button
          onClick={generateReport}
          className="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg"
        >
          <FileText className="w-4 h-4" /> Generate report
        </button>
        {reportPath && (
          <p className="mt-3 text-sm text-slate-400">Saved: {reportPath}</p>
        )}
      </div>
    </div>
  );
};

export default InterlockPage;
