import React, { useState, useEffect } from 'react'
import { Brain, Play, CheckCircle, AlertCircle, BarChart3, Layers } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'
import axios from 'axios'

interface AvailableModel {
  name: string
  type: string
  provides_uncertainty: boolean
  description: string
}

interface ModelComparison {
  combination: string[]
  score: number
  r2: number
  mae: number
  rmse: number
  strategy: string
  has_uncertainty: boolean
}

const MLModelComparison: React.FC = () => {
  const [availableModels, setAvailableModels] = useState<AvailableModel[]>([])
  //const [selectedModels] = useState<string[]>([])
  const [experimentId, setExperimentId] = useState('EXP-TEST001')
  const [pipelineId, setPipelineId] = useState<string | null>(null)
  const [pipelineStatus, setPipelineStatus] = useState<string>('idle')
  const [comparisons, setComparisons] = useState<ModelComparison[]>([])
  const [selectedComparison, setSelectedComparison] = useState<ModelComparison | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadAvailableModels()
  }, [])

  useEffect(() => {
    if (pipelineId && pipelineStatus === 'running') {
      const interval = setInterval(() => {
        checkPipelineStatus()
      }, 3000)
      return () => clearInterval(interval)
    }
  }, [pipelineId, pipelineStatus])

  const loadAvailableModels = async () => {
    try {
      const response = await axios.get('/api/v1/ml-pipeline/available-models')
      setAvailableModels(response.data.models)
    } catch (error) {
      console.error('Failed to load models:', error)
    }
  }

  const runAutomatedPipeline = async () => {
    setLoading(true)
    try {
      const response = await axios.post('/api/v1/ml-pipeline/run-automated-pipeline', {
        experiment_id: experimentId,
        min_models: 2,
        max_models: 4
      })
      
      setPipelineId(response.data.pipeline_id)
      setPipelineStatus('running')
      alert(`Pipeline started: ${response.data.pipeline_id}`)
    } catch (error: any) {
      alert(`Failed to start pipeline: ${error.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const checkPipelineStatus = async () => {
    if (!pipelineId) return

    try {
      const response = await axios.get(`/api/v1/ml-pipeline/pipeline-status/${pipelineId}`)
      const status = response.data.status
      
      setPipelineStatus(status)
      
      if (status === 'completed') {
        loadPipelineResults()
      }
    } catch (error) {
      console.error('Failed to check pipeline status:', error)
    }
  }

  const loadPipelineResults = async () => {
    if (!pipelineId) return

    try {
      const response = await axios.get(`/api/v1/ml-pipeline/pipeline-results/${pipelineId}`)
      const results = response.data
      
      // Extract comparisons
      const comparisonData = results.ranked_results.map((r: any) => ({
        combination: r.combination,
        score: r.score,
        r2: r.ensemble_r2,
        mae: r.ensemble_mae,
        rmse: r.ensemble_rmse,
        strategy: r.best_ensemble_strategy,
        has_uncertainty: r.has_uncertainty
      }))
      
      setComparisons(comparisonData)
      setSelectedComparison(comparisonData[0])
    } catch (error) {
      console.error('Failed to load results:', error)
    }
  }

  const selectBestCombination = async () => {
    if (!pipelineId) return

    try {
      const response = await axios.post(`/api/v1/ml-pipeline/select-best-combination/${pipelineId}`)
      alert(`Model saved: ${response.data.model_id}\nCombination: ${response.data.combination.join(', ')}`)
    } catch (error: any) {
      alert(`Failed to select combination: ${error.response?.data?.detail || error.message}`)
    }
  }

  const getModelTypeColor = (type: string) => {
    switch (type) {
      case 'probabilistic': return 'bg-purple-500/20 border-purple-500/30 text-purple-400'
      case 'ensemble': return 'bg-green-500/20 border-green-500/30 text-green-400'
      case 'boosting': return 'bg-blue-500/20 border-blue-500/30 text-blue-400'
      default: return 'bg-slate-500/20 border-slate-500/30 text-slate-400'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-400'
    if (score >= 0.6) return 'text-yellow-400'
    return 'text-red-400'
  }

  // Prepare radar chart data
  const prepareRadarData = () => {
    if (!selectedComparison) return []

    return [
      { metric: 'R² Score', value: selectedComparison.r2 * 100 },
      { metric: 'Low MAE', value: Math.max(0, 100 - selectedComparison.mae * 20) },
      { metric: 'Low RMSE', value: Math.max(0, 100 - selectedComparison.rmse * 15) },
      { metric: 'Overall Score', value: selectedComparison.score * 100 },
      { metric: 'Uncertainty', value: selectedComparison.has_uncertainty ? 100 : 0 }
    ]
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold flex items-center gap-3">
          <Brain className="w-10 h-10 text-purple-400" />
          ML Model Comparison & Ensemble
        </h1>
        <p className="text-slate-400 mt-2">
          자동화된 모델 조합 생성 및 성능 비교
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left Panel: Configuration */}
        <div className="col-span-1 space-y-6">
          {/* Experiment Selection */}
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Configuration</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Experiment ID
                </label>
                <input
                  type="text"
                  value={experimentId}
                  onChange={(e) => setExperimentId(e.target.value)}
                  className="input-field w-full"
                  placeholder="EXP-ABC12345"
                />
              </div>

              <button
                onClick={runAutomatedPipeline}
                disabled={loading || pipelineStatus === 'running'}
                className="w-full flex items-center justify-center gap-2 btn-primary disabled:bg-purple-800"
              >
                <Play className="w-5 h-5" />
                {loading ? 'Starting...' : pipelineStatus === 'running' ? 'Running...' : 'Run Automated Pipeline'}
              </button>

              {pipelineId && (
                <div className="mt-4 p-3 bg-slate-700/50 rounded-lg text-sm">
                  <div className="flex items-center gap-2 mb-2">
                    {pipelineStatus === 'running' && (
                      <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-purple-500"></div>
                    )}
                    {pipelineStatus === 'completed' && <CheckCircle className="w-4 h-4 text-green-500" />}
                    {pipelineStatus === 'failed' && <AlertCircle className="w-4 h-4 text-red-500" />}
                    <span className="font-semibold">Status: {pipelineStatus}</span>
                  </div>
                  <div className="text-xs text-slate-400">Pipeline ID: {pipelineId}</div>
                </div>
              )}
            </div>
          </div>

          {/* Available Models */}
          <div className="card">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Layers className="w-5 h-5 text-cyan-400" />
              Available Models
            </h2>
            
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {availableModels.map(model => (
                <div
                  key={model.name}
                  className={`border rounded-lg p-3 ${getModelTypeColor(model.type)}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold text-sm">{model.name.replace(/_/g, ' ').toUpperCase()}</div>
                    {model.provides_uncertainty && (
                      <span className="text-xs px-2 py-1 bg-purple-600 text-white rounded">
                        Uncertainty
                      </span>
                    )}
                  </div>
                  <div className="text-xs opacity-90">{model.description}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Middle Panel: Comparisons */}
        <div className="col-span-2 space-y-6">
          {comparisons.length === 0 ? (
            <div className="card p-12 text-center">
              <Brain className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <div className="text-xl text-slate-400 mb-2">No Comparisons Yet</div>
              <div className="text-sm text-slate-500">
                Run the automated pipeline to generate model combinations and compare their performance
              </div>
            </div>
          ) : (
            <>
              {/* Performance Comparison Chart */}
              <div className="card">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-cyan-400" />
                  Performance Comparison
                </h2>

                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={comparisons.slice(0, 5)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis 
                      dataKey="combination"
                      stroke="#94a3b8"
                      tick={{fontSize: 10}}
                      angle={-45}
                      textAnchor="end"
                      height={100}
                      tickFormatter={(value) => value.slice(0, 2).join('+')}
                    />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '8px'
                      }}
                      formatter={(value: any) => value.toFixed(3)}
                    />
                    <Legend />
                    <Bar dataKey="r2" fill="#60a5fa" name="R² Score" />
                    <Bar dataKey="score" fill="#a78bfa" name="Overall Score" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Comparison Table */}
              <div className="card">
                <h2 className="text-xl font-bold mb-4">Ranked Combinations</h2>
                
                <div className="space-y-3">
                  {comparisons.map((comp, index) => (
                    <div
                      key={index}
                      onClick={() => setSelectedComparison(comp)}
                      className={`border rounded-lg p-4 cursor-pointer transition-all ${
                        selectedComparison === comp
                          ? 'bg-slate-700 border-purple-500'
                          : 'bg-slate-700/30 border-slate-600 hover:border-slate-500'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                            index === 0 ? 'bg-yellow-500 text-black' :
                            index === 1 ? 'bg-slate-400 text-black' :
                            index === 2 ? 'bg-orange-600 text-white' :
                            'bg-slate-600 text-slate-300'
                          }`}>
                            {index + 1}
                          </div>
                          <div>
                            <div className="font-semibold">
                              {comp.combination.map(m => m.replace('_', ' ')).join(' + ')}
                            </div>
                            <div className="text-xs text-slate-400 mt-1">
                              Strategy: {comp.strategy.replace('_', ' ')}
                            </div>
                          </div>
                        </div>
                        {comp.has_uncertainty && (
                          <span className="text-xs px-2 py-1 bg-purple-600 text-white rounded">
                            Uncertainty
                          </span>
                        )}
                      </div>

                      <div className="grid grid-cols-4 gap-4 text-sm">
                        <div>
                          <div className="text-slate-400 text-xs">Score</div>
                          <div className={`font-bold text-lg ${getScoreColor(comp.score)}`}>
                            {comp.score.toFixed(3)}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-400 text-xs">R²</div>
                          <div className="font-bold text-lg text-cyan-400">
                            {comp.r2.toFixed(3)}
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-400 text-xs">MAE</div>
                          <div className="font-bold text-lg text-green-400">
                            {comp.mae.toFixed(2)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-slate-400 text-xs">RMSE</div>
                          <div className="font-bold text-lg text-blue-400">
                            {comp.rmse.toFixed(2)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {selectedComparison && (
                  <button
                    onClick={selectBestCombination}
                    className="w-full mt-6 flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-semibold transition-colors"
                  >
                    <CheckCircle className="w-5 h-5" />
                    Select Best Combination & Deploy
                  </button>
                )}
              </div>

              {/* Radar Chart */}
              {selectedComparison && (
                <div className="card">
                  <h2 className="text-xl font-bold mb-4">Selected Model Performance Profile</h2>
                  
                  <ResponsiveContainer width="100%" height={400}>
                    <RadarChart data={prepareRadarData()}>
                      <PolarGrid stroke="#334155" />
                      <PolarAngleAxis dataKey="metric" stroke="#94a3b8" />
                      <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#94a3b8" />
                      <Radar
                        name="Performance"
                        dataKey="value"
                        stroke="#a78bfa"
                        fill="#a78bfa"
                        fillOpacity={0.6}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1e293b',
                          border: '1px solid #334155',
                          borderRadius: '8px'
                        }}
                      />
                    </RadarChart>
                  </ResponsiveContainer>

                  <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                    <div className="bg-slate-700/50 rounded p-3">
                      <div className="text-slate-400 mb-1">Ensemble Strategy</div>
                      <div className="font-semibold">{selectedComparison.strategy.replace('_', ' ')}</div>
                    </div>
                    <div className="bg-slate-700/50 rounded p-3">
                      <div className="text-slate-400 mb-1">Model Count</div>
                      <div className="font-semibold">{selectedComparison.combination.length}</div>
                    </div>
                    <div className="bg-slate-700/50 rounded p-3">
                      <div className="text-slate-400 mb-1">Confidence</div>
                      <div className={`font-semibold ${getScoreColor(selectedComparison.score)}`}>
                        {selectedComparison.score >= 0.8 ? 'High' : selectedComparison.score >= 0.6 ? 'Medium' : 'Low'}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default MLModelComparison