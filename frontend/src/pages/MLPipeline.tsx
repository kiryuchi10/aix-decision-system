import React, { useState } from 'react';
import { Cpu, Play, CheckCircle, Clock, Award, TrendingUp, Zap } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

const ModelCard = ({ model, isSelected, onSelect, isBest }: { 
  model: any, 
  isSelected: boolean, 
  onSelect: () => void, 
  isBest: boolean 
}) => {
  const statusColors: Record<string, { bg: string, border: string, text: string }> = {
    trained: { bg: 'bg-green-500/10', border: 'border-green-500', text: 'text-green-400' },
    training: { bg: 'bg-yellow-500/10', border: 'border-yellow-500', text: 'text-yellow-400' },
    pending: { bg: 'bg-gray-500/10', border: 'border-gray-500', text: 'text-gray-400' }
  };

  const config = statusColors[model.status] || statusColors.pending;

  return (
    <div 
      className={`relative bg-gray-800 rounded-xl p-6 border-2 cursor-pointer transition-all hover:scale-[1.02] ${
        isSelected ? 'border-blue-500' : 'border-gray-700'
      } ${isBest ? 'ring-2 ring-yellow-500' : ''}`}
      onClick={onSelect}
    >
      {isBest && (
        <div className="absolute -top-3 -right-3 bg-yellow-500 text-gray-900 p-2 rounded-full">
          <Award className="w-5 h-5" />
        </div>
      )}

      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-white">{model.name}</h3>
          <p className="text-sm text-gray-400">{model.algorithm}</p>
        </div>
        <span className={`px-3 py-1 rounded-lg text-xs font-medium ${config.bg} ${config.text} border ${config.border}`}>
          {model.status}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-400">Accuracy</p>
          <p className="text-2xl font-bold text-white">{(model.metrics.accuracy * 100).toFixed(1)}%</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">F1 Score</p>
          <p className="text-2xl font-bold text-white">{(model.metrics.f1 * 100).toFixed(1)}%</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Precision</p>
          <p className="text-xl font-semibold text-blue-400">{(model.metrics.precision * 100).toFixed(1)}%</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Recall</p>
          <p className="text-xl font-semibold text-green-400">{(model.metrics.recall * 100).toFixed(1)}%</p>
        </div>
      </div>

      <div className="pt-4 border-t border-gray-700">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Training Time</span>
          <span className="text-white font-medium">{model.training_time}s</span>
        </div>
        <div className="flex items-center justify-between text-sm mt-2">
          <span className="text-gray-400">Cross-Val Score</span>
          <span className="text-white font-medium">{(model.cv_score * 100).toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
};

const EnsembleCard = ({ ensemble, onSelect }: { ensemble: any, onSelect: () => void }) => {
  return (
    <div className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 rounded-xl p-6 border-2 border-purple-500/30 hover:border-purple-500 transition-all cursor-pointer"
         onClick={onSelect}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-white">{ensemble.name}</h3>
          <p className="text-sm text-gray-400">{ensemble.method} Ensemble</p>
        </div>
        <Zap className="w-6 h-6 text-purple-400" />
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-400">Accuracy</p>
          <p className="text-2xl font-bold text-purple-400">{(ensemble.accuracy * 100).toFixed(1)}%</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Models</p>
          <p className="text-2xl font-bold text-white">{ensemble.models.length}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Improvement</p>
          <p className="text-2xl font-bold text-green-400">+{ensemble.improvement.toFixed(1)}%</p>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
        <p className="text-xs text-gray-400 mb-2">Component Models:</p>
        <div className="flex flex-wrap gap-2">
          {ensemble.models.map((model: string, idx: number) => (
            <span key={idx} className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs">
              {model}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

const PerformanceComparison = ({ models }: { models: any[] }) => {
  const data = models.map(m => ({
    name: m.algorithm.split(' ')[0],
    accuracy: m.metrics.accuracy * 100,
    precision: m.metrics.precision * 100,
    recall: m.metrics.recall * 100,
    f1: m.metrics.f1 * 100
  }));

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">Model Performance Comparison</h3>
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="name" stroke="#9ca3af" />
          <YAxis stroke="#9ca3af" domain={[0, 100]} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
          />
          <Legend />
          <Bar dataKey="accuracy" fill="#3b82f6" />
          <Bar dataKey="precision" fill="#10b981" />
          <Bar dataKey="recall" fill="#f59e0b" />
          <Bar dataKey="f1" fill="#8b5cf6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

const RadarComparison = ({ models, selectedModelId }: { models: any[], selectedModelId: number }) => {
  const selectedModel = models.find(m => m.id === selectedModelId);
  if (!selectedModel) return null;

  const data = [
    { metric: 'Accuracy', value: selectedModel.metrics.accuracy * 100 },
    { metric: 'Precision', value: selectedModel.metrics.precision * 100 },
    { metric: 'Recall', value: selectedModel.metrics.recall * 100 },
    { metric: 'F1 Score', value: selectedModel.metrics.f1 * 100 },
    { metric: 'Speed', value: (100 - selectedModel.training_time / 10) },
  ];

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">
        {selectedModel.name} - Performance Radar
      </h3>
      <ResponsiveContainer width="100%" height={350}>
        <RadarChart data={data}>
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis dataKey="metric" stroke="#9ca3af" />
          <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#9ca3af" />
          <Radar 
            name={selectedModel.name}
            dataKey="value" 
            stroke="#3b82f6" 
            fill="#3b82f6" 
            fillOpacity={0.3}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

const PipelineStatus = ({ status }: { status: string }) => {
  const stages = [
    { name: 'Data Preparation', status: 'completed', duration: '2.3s' },
    { name: 'Model Training', status: status === 'training' ? 'active' : 'completed', duration: '45.2s' },
    { name: 'Validation', status: status === 'training' ? 'pending' : 'completed', duration: '8.1s' },
    { name: 'Ensemble Creation', status: status === 'training' ? 'pending' : 'completed', duration: '12.5s' },
    { name: 'Deployment', status: 'pending', duration: '-' }
  ];

  const getStatusIcon = (s: string) => {
    if (s === 'completed') return <CheckCircle className="w-5 h-5 text-green-400" />;
    if (s === 'active') return <Clock className="w-5 h-5 text-yellow-400 animate-spin" />;
    return <Clock className="w-5 h-5 text-gray-500" />;
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">Pipeline Status</h3>
      <div className="space-y-3">
        {stages.map((stage, idx) => (
          <div key={idx} className="flex items-center gap-4">
            {getStatusIcon(stage.status)}
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="text-white font-medium">{stage.name}</span>
                <span className="text-sm text-gray-400">{stage.duration}</span>
              </div>
              {stage.status === 'active' && (
                <div className="mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div className="h-full bg-yellow-500 animate-pulse" style={{ width: '60%' }}></div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const MLPipelinePage: React.FC = () => {
  const [selectedModelId, setSelectedModelId] = useState(1);
  const [pipelineStatus, setPipelineStatus] = useState('idle'); // idle, training, completed

  const models = [
    {
      id: 1,
      name: 'Model-RF-001',
      algorithm: 'Random Forest',
      status: 'trained',
      metrics: { accuracy: 0.962, precision: 0.958, recall: 0.965, f1: 0.961 },
      training_time: 45.2,
      cv_score: 0.955
    },
    {
      id: 2,
      name: 'Model-XGB-001',
      algorithm: 'XGBoost',
      status: 'trained',
      metrics: { accuracy: 0.971, precision: 0.968, recall: 0.973, f1: 0.970 },
      training_time: 62.8,
      cv_score: 0.967
    },
    {
      id: 3,
      name: 'Model-SVM-001',
      algorithm: 'Support Vector Machine',
      status: 'trained',
      metrics: { accuracy: 0.948, precision: 0.945, recall: 0.951, f1: 0.948 },
      training_time: 128.5,
      cv_score: 0.942
    },
    {
      id: 4,
      name: 'Model-NN-001',
      algorithm: 'Neural Network',
      status: 'training',
      metrics: { accuracy: 0.955, precision: 0.952, recall: 0.958, f1: 0.955 },
      training_time: 89.3,
      cv_score: 0.951
    }
  ];

  const ensembles = [
    {
      id: 1,
      name: 'Ensemble-Voting-001',
      method: 'Voting',
      accuracy: 0.978,
      improvement: 2.1,
      models: ['Random Forest', 'XGBoost', 'Neural Network']
    },
    {
      id: 2,
      name: 'Ensemble-Stacking-001',
      method: 'Stacking',
      accuracy: 0.982,
      improvement: 3.4,
      models: ['Random Forest', 'XGBoost', 'SVM', 'Neural Network']
    }
  ];

  const bestModel = models.reduce((best, model) => 
    model.metrics.accuracy > best.metrics.accuracy ? model : best
  );

  const handleStartTraining = () => {
    setPipelineStatus('training');
    setTimeout(() => setPipelineStatus('completed'), 5000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Cpu className="w-8 h-8 text-orange-400" />
            <div>
              <h1 className="text-3xl font-bold text-white">ML Pipeline Optimization</h1>
              <p className="text-gray-400">Automated model training, comparison & selection</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button 
              onClick={handleStartTraining}
              disabled={pipelineStatus === 'training'}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-colors flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Start Training
            </button>
            <button className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white font-medium transition-colors">
              Deploy Best Model
            </button>
          </div>
        </div>
      </div>

      {/* Pipeline Status */}
      <div className="mb-6">
        <PipelineStatus status={pipelineStatus} />
      </div>

      {/* Model Cards Grid */}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-white mb-4">Individual Models</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {models.map(model => (
            <ModelCard 
              key={model.id}
              model={model}
              isSelected={selectedModelId === model.id}
              onSelect={() => setSelectedModelId(model.id)}
              isBest={model.id === bestModel.id}
            />
          ))}
        </div>
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <PerformanceComparison models={models} />
        <RadarComparison models={models} selectedModelId={selectedModelId} />
      </div>

      {/* Ensemble Models */}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-white mb-4">Ensemble Models</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {ensembles.map(ensemble => (
            <EnsembleCard key={ensemble.id} ensemble={ensemble} onSelect={() => {}} />
          ))}
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 rounded-xl p-6 border border-blue-500/30">
        <div className="flex items-start gap-4">
          <TrendingUp className="w-6 h-6 text-blue-400 mt-1" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white mb-2">Recommendation</h3>
            <p className="text-gray-300 mb-4">
              Based on performance metrics, <span className="text-blue-400 font-semibold">Ensemble-Stacking-001</span> is 
              recommended for deployment with 98.2% accuracy and 3.4% improvement over the best individual model.
            </p>
            <div className="flex gap-3">
              <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm font-medium transition-colors">
                Deploy Ensemble
              </button>
              <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white text-sm font-medium transition-colors">
                View Details
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MLPipelinePage;
