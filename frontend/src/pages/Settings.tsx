import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save } from 'lucide-react';
import { useProcessWindow } from '../features/settings/useProcessWindow';
import { saveProcessWindow, saveAlarmThresholds, getAlarmThresholds } from '../features/settings/settings.api';

const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('process-window');
  const { rows: processWindowRows, loading: pwLoading } = useProcessWindow();
  const [processWindow, setProcessWindow] = useState(processWindowRows || []);
  const [alarmThresholds, setAlarmThresholds] = useState({
    enableWeco: true,
    sigmaThreshold: 3.0,
    ewmaLambda: 0.2,
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (processWindowRows) {
      setProcessWindow(processWindowRows);
    }
  }, [processWindowRows]);

  useEffect(() => {
    getAlarmThresholds()
      .then((data) => {
        setAlarmThresholds({
          enableWeco: data.enableWeco,
          sigmaThreshold: data.sigmaThreshold,
          ewmaLambda: data.ewmaLambda,
        });
      })
      .catch((err) => console.error('Failed to load alarm thresholds:', err));
  }, []);

  const handleSaveProcessWindow = async () => {
    setSaving(true);
    try {
      await saveProcessWindow({ rows: processWindow });
      alert('Process window saved successfully');
    } catch (error: any) {
      console.error('Failed to save:', error);
      alert(error.message || 'Failed to save process window');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAlarmThresholds = async () => {
    setSaving(true);
    try {
      await saveAlarmThresholds(alarmThresholds);
      alert('Alarm thresholds saved successfully');
    } catch (error: any) {
      console.error('Failed to save:', error);
      alert(error.message || 'Failed to save alarm thresholds');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <SettingsIcon className="w-8 h-8" />
            System Settings
          </h1>
          <p className="text-slate-400 mt-1">Guardrails, thresholds, and system configuration</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-700">
        {[
          { id: 'process-window', label: 'Process Window' },
          { id: 'alarms', label: 'Alarm Thresholds' },
          { id: 'integrations', label: 'Integrations' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 font-semibold transition-colors ${
              activeTab === tab.id
                ? 'border-b-2 border-cyan-600 text-cyan-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Process Window Tab */}
      {activeTab === 'process-window' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">Guardrail Process Window</h2>
            <button
              onClick={handleSaveProcessWindow}
              disabled={saving || pwLoading}
              className="btn-primary flex items-center gap-2 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
          <div className="space-y-4">
            {processWindow.map((pw, idx) => (
              <div key={idx} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Variable</label>
                    <input
                      type="text"
                      value={pw.key}
                      readOnly
                      className="w-full input-field bg-slate-900"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Unit</label>
                    <input
                      type="text"
                      value={pw.unit}
                      readOnly
                      className="w-full input-field bg-slate-900"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Hard Min</label>
                    <input
                      type="number"
                      value={pw.hardMin}
                      onChange={(e) => {
                        const updated = [...processWindow];
                        updated[idx].hardMin = parseFloat(e.target.value);
                        setProcessWindow(updated);
                      }}
                      className="w-full input-field"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Hard Max</label>
                    <input
                      type="number"
                      value={pw.hardMax}
                      onChange={(e) => {
                        const updated = [...processWindow];
                        updated[idx].hardMax = parseFloat(e.target.value);
                        setProcessWindow(updated);
                      }}
                      className="w-full input-field"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Alarm Thresholds Tab */}
      {activeTab === 'alarms' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">Alarm Thresholds</h2>
            <button
              onClick={handleSaveAlarmThresholds}
              disabled={saving}
              className="btn-primary flex items-center gap-2 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-white">Enable WECO/Nelson Rules</div>
                <div className="text-sm text-slate-400">Statistical process control rules</div>
              </div>
              <input
                type="checkbox"
                checked={alarmThresholds.enableWeco}
                onChange={(e) => setAlarmThresholds({ ...alarmThresholds, enableWeco: e.target.checked })}
                className="w-5 h-5"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">FDC Sigma Threshold</label>
              <input
                type="number"
                step="0.1"
                value={alarmThresholds.sigmaThreshold}
                onChange={(e) => setAlarmThresholds({ ...alarmThresholds, sigmaThreshold: parseFloat(e.target.value) || 0 })}
                className="w-full input-field"
                placeholder="e.g., 3.0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">EWMA Lambda</label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={alarmThresholds.ewmaLambda}
                onChange={(e) => setAlarmThresholds({ ...alarmThresholds, ewmaLambda: parseFloat(e.target.value) || 0 })}
                className="w-full input-field"
                placeholder="e.g., 0.2"
              />
            </div>
          </div>
        </div>
      )}

      {/* Integrations Tab */}
      {activeTab === 'integrations' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { name: 'Database', desc: 'MySQL / Postgres connection' },
            { name: 'Streaming', desc: 'WebSocket / Kafka / MQTT' },
            { name: 'Storage', desc: 'S3/GCS for reports and datasets' },
            { name: 'Notifications', desc: 'Email/Slack for alarms' },
          ].map((integration) => (
            <div key={integration.name} className="card">
              <h3 className="font-bold text-white mb-2">{integration.name}</h3>
              <p className="text-sm text-slate-400 mb-4">{integration.desc}</p>
              <button className="btn-secondary">Configure</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
