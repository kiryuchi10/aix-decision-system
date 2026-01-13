import React, { useState, useEffect } from 'react';
import { Link as LinkIcon, Power, Sliders, Shield, CheckCircle, XCircle, FileText } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface CouplingStatus {
  is_active: boolean;
  mode: string;
  last_action?: string;
  last_action_time?: string;
}

interface CouplingAction {
  id: string;
  trigger_type: string;
  action_type: string;
  parameters: any;
  confidence: number;
  requires_approval: boolean;
  status: string;
}

const CouplingPage: React.FC = () => {
  const [status, setStatus] = useState<CouplingStatus | null>(null);
  const [pendingActions, setPendingActions] = useState<CouplingAction[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStatus();
    loadPendingActions();
    const interval = setInterval(() => {
      loadStatus();
      loadPendingActions();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/coupling/status`);
      setStatus(response.data);
    } catch (error) {
      console.error('Failed to load coupling status:', error);
    }
  };

  const loadPendingActions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/coupling/actions/pending`);
      setPendingActions(response.data);
    } catch (error) {
      console.error('Failed to load pending actions:', error);
    }
  };

  const handleModeChange = async (mode: string) => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/api/v1/coupling/mode`, { mode });
      loadStatus();
    } catch (error) {
      console.error('Failed to change mode:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (actionId: string) => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/api/v1/coupling/actions/${actionId}/approve`);
      loadPendingActions();
    } catch (error) {
      console.error('Failed to approve action:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (actionId: string) => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/api/v1/coupling/actions/${actionId}/reject`, { reason: 'User rejected' });
      loadPendingActions();
    } catch (error) {
      console.error('Failed to reject action:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <LinkIcon className="w-8 h-8" />
            Coupling Control
          </h1>
          <p className="text-slate-400 mt-1">FDC-DoE Integration - Closed-loop Decision Making</p>
        </div>
        {status && (
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Mode:</span>
              <button
                onClick={() => handleModeChange(status.mode === 'FULL_AUTO' ? 'SEMI_AUTO' : 'FULL_AUTO')}
                disabled={loading}
                className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                  status.mode === 'FULL_AUTO'
                    ? 'bg-green-600 text-white'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                <Power className="w-4 h-4 inline mr-2" />
                {status.mode === 'FULL_AUTO' ? 'Closed-loop' : 'Open-loop'}
              </button>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
              status.is_active ? 'bg-green-500/20 text-green-400' : 'bg-slate-500/20 text-slate-400'
            }`}>
              {status.is_active ? 'Active' : 'Inactive'}
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Adjustable Variables */}
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Sliders className="w-5 h-5" />
            Adjustable Variables
          </h2>
          <div className="space-y-4">
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <div className="font-semibold text-white">Temperature</div>
                  <div className="text-sm text-slate-400">Current: 852.3°C</div>
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-yellow-400" />
                  <span className="text-xs text-yellow-400">Guardrail: 840-860°C</span>
                </div>
              </div>
              <input
                type="range"
                min="840"
                max="860"
                defaultValue="852"
                className="w-full mt-2"
              />
              <div className="flex justify-between text-xs text-slate-400 mt-1">
                <span>840</span>
                <span>Recommended: 850°C</span>
                <span>860</span>
              </div>
            </div>
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <div className="font-semibold text-white">Pressure</div>
                  <div className="text-sm text-slate-400">Current: 2.48 Torr</div>
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-yellow-400" />
                  <span className="text-xs text-yellow-400">Guardrail: 2.3-2.7 Torr</span>
                </div>
              </div>
              <input
                type="range"
                min="2.3"
                max="2.7"
                step="0.01"
                defaultValue="2.48"
                className="w-full mt-2"
              />
              <div className="flex justify-between text-xs text-slate-400 mt-1">
                <span>2.3</span>
                <span>Recommended: 2.5 Torr</span>
                <span>2.7</span>
              </div>
            </div>
          </div>
        </div>

        {/* Approval Workflow */}
        <div className="card">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Pending Actions ({pendingActions.length})
          </h2>
          {pendingActions.length > 0 ? (
            <div className="space-y-3">
              {pendingActions.map((action) => (
                <div key={action.id} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="font-semibold text-white">{action.action_type.replace('_', ' ')}</div>
                      <div className="text-sm text-slate-400">Trigger: {action.trigger_type.replace('_', ' ')}</div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      action.requires_approval ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'
                    }`}>
                      {action.requires_approval ? 'Requires Approval' : 'Auto'}
                    </span>
                  </div>
                  <div className="text-sm text-slate-300 mb-3">
                    Confidence: {(action.confidence * 100).toFixed(1)}%
                  </div>
                  {action.requires_approval && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleApprove(action.id)}
                        disabled={loading}
                        className="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 rounded text-sm font-semibold flex items-center justify-center gap-1"
                      >
                        <CheckCircle className="w-4 h-4" />
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(action.id)}
                        disabled={loading}
                        className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 rounded text-sm font-semibold flex items-center justify-center gap-1"
                      >
                        <XCircle className="w-4 h-4" />
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400">
              <CheckCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No pending actions</p>
            </div>
          )}
        </div>
      </div>

      {/* Audit Log Placeholder */}
      <div className="card">
        <h2 className="text-xl font-bold text-white mb-4">Audit Log</h2>
        <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
          <div className="text-slate-400 text-sm">Audit log table (to be implemented)</div>
        </div>
      </div>
    </div>
  );
};

export default CouplingPage;
