import React, { useState, useEffect } from 'react'
import { Activity, TrendingUp, Clock, Target, Zap, FlaskConical } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import axios from 'axios'

interface KPIData {
  overall_health: number
  process_cpk: number
  drift_rate: number
  avg_recovery_time: number
  yield_gain: number
  experiment_reduction: number
}

interface SensorData {
  timestamp: string
  temperature: number
  pressure: number
  gas_flow: number
  power: number
}

interface Alarm {
  id: string
  timestamp: string
  severity: string
  type: string
  parameter: string
  current_value: number
  threshold_value: number
  sigma_distance: number
  yield_impact: number
  status: string
}

interface Recommendation {
  id: string
  type: string
  priority: string
  title: string
  description: string
  confidence: number
  expected_improvement: number
  risk_level: string
  requires_approval: boolean
  status: string
}

const Dashboard: React.FC = () => {
  const [kpiData, setKpiData] = useState<KPIData>({
    overall_health: 94.2,
    process_cpk: 1.33,
    drift_rate: 0.05,
    avg_recovery_time: 18,
    yield_gain: 4.2,
    experiment_reduction: 35
  })
  
  const [sensorHistory, setSensorHistory] = useState<SensorData[]>([])
  const [currentSensor, setCurrentSensor] = useState<SensorData | null>(null)
  const [alarms, setAlarms] = useState<Alarm[]>([])
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [timeRange, setTimeRange] = useState('1h')
  const [wsConnected, setWsConnected] = useState(false)

  useEffect(() => {
    // Load initial data
    loadAlarms()
    loadRecommendations()
    generateMockSensorHistory()
    
    // Setup WebSocket connection
    setupWebSocket()
    
    return () => {
      // Cleanup WebSocket on unmount
    }
  }, [])

  const setupWebSocket = () => {
    const ws = new WebSocket('ws://localhost:8000/ws')
    
    ws.onopen = () => {
      setWsConnected(true)
      console.log('WebSocket connected')
    }
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      if (message.type === 'sensor_data') {
        setCurrentSensor(message.data)
        // Add to history (keep last 100 points)
        setSensorHistory(prev => [...prev.slice(-99), message.data])
      }
    }
    
    ws.onclose = () => {
      setWsConnected(false)
      console.log('WebSocket disconnected')
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setWsConnected(false)
    }
  }

  const loadAlarms = async () => {
    try {
      const response = await axios.get('/api/v1/fdc/alarms/active')
      setAlarms(response.data)
    } catch (error) {
      console.error('Failed to load alarms:', error)
    }
  }

  const loadRecommendations = async () => {
    try {
      const response = await axios.get('/api/v1/recommendations/active')
      setRecommendations(response.data)
    } catch (error) {
      console.error('Failed to load recommendations:', error)
    }
  }

  const generateMockSensorHistory = () => {
    const history = []
    const now = new Date()
    
    for (let i = 59; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * 60000) // 1 minute intervals
      history.push({
        timestamp: timestamp.toISOString(),
        temperature: 850 + Math.sin(i * 0.1) * 5 + Math.random() * 2,
        pressure: 2.5 + Math.sin(i * 0.15) * 0.1 + Math.random() * 0.05,
        gas_flow: 100 + Math.random() * 10,
        power: 1500 + Math.random() * 100
      })
    }
    
    setSensorHistory(history)
    setCurrentSensor(history[history.length - 1])
  }

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'text-red-400 bg-red-900/20 border-red-700/50'
      case 'high': return 'text-orange-400 bg-orange-900/20 border-orange-700/50'
      case 'medium': return 'text-yellow-400 bg-yellow-900/20 border-yellow-700/50'
      case 'low': return 'text-blue-400 bg-blue-900/20 border-blue-700/50'
      default: return 'text-slate-400 bg-slate-900/20 border-slate-700/50'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'urgent': return 'text-red-400'
      case 'high': return 'text-orange-400'
      case 'medium': return 'text-yellow-400'
      case 'low': return 'text-blue-400'
      default: return 'text-slate-400'
    }
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold">AiX Decision System</h1>
            <p className="text-slate-400 mt-2">Real-time Process Monitoring & AI-Driven Optimization</p>
          </div>
          <div className="flex items-center gap-4">
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
              wsConnected ? 'bg-green-900/20 border border-green-700/50' : 'bg-red-900/20 border border-red-700/50'
            }`}>
              <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
              <span className="text-sm">{wsConnected ? 'Live' : 'Disconnected'}</span>
            </div>
            <div className="text-sm text-slate-400">
              Last Update: {currentSensor ? formatTime(currentSensor.timestamp) : '--:--'}
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-6 gap-6 mb-8">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Overall Health</p>
              <p className="text-2xl font-bold text-green-400">{kpiData.overall_health}%</p>
            </div>
            <Activity className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Process Cpk</p>
              <p className="text-2xl font-bold text-blue-400">{kpiData.process_cpk}</p>
            </div>
            <Target className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Drift Rate</p>
              <p className="text-2xl font-bold text-yellow-400">{kpiData.drift_rate}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-yellow-400" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Avg Recovery</p>
              <p className="text-2xl font-bold text-purple-400">{kpiData.avg_recovery_time}min</p>
            </div>
            <Clock className="w-8 h-8 text-purple-400" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Yield Gain</p>
              <p className="text-2xl font-bold text-green-400">+{kpiData.yield_gain}%</p>
            </div>
            <Zap className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Exp. Reduction</p>
              <p className="text-2xl font-bold text-cyan-400">{kpiData.experiment_reduction}%</p>
            </div>
            <FlaskConical className="w-8 h-8 text-cyan-400" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Sensor Monitoring */}
        <div className="col-span-2 space-y-6">
          {/* Real-time Charts */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Real-time Sensor Data</h2>
              <div className="flex gap-2">
                {['1h', '6h', '24h'].map(range => (
                  <button
                    key={range}
                    onClick={() => setTimeRange(range)}
                    className={`px-3 py-1 text-sm rounded ${
                      timeRange === range 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {range}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-slate-700/30 rounded-lg p-3">
                <div className="text-sm text-slate-400">Temperature</div>
                <div className="text-lg font-bold text-orange-400">
                  {currentSensor?.temperature.toFixed(1)}°C
                </div>
              </div>
              <div className="bg-slate-700/30 rounded-lg p-3">
                <div className="text-sm text-slate-400">Pressure</div>
                <div className="text-lg font-bold text-blue-400">
                  {currentSensor?.pressure.toFixed(2)} Torr
                </div>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={sensorHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis 
                  dataKey="timestamp" 
                  stroke="#94a3b8"
                  tickFormatter={formatTime}
                />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px'
                  }}
                  labelFormatter={(value) => `Time: ${formatTime(value)}`}
                />
                <Area
                  type="monotone"
                  dataKey="temperature"
                  stroke="#f97316"
                  fill="#f97316"
                  fillOpacity={0.3}
                  name="Temperature (°C)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right Panel */}
        <div className="space-y-6">
          {/* Active Alarms */}
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Active Alarms</h2>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {alarms.map(alarm => (
                <div key={alarm.id} className={`border rounded-lg p-3 ${getSeverityColor(alarm.severity)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-sm">{alarm.parameter}</span>
                    <span className="text-xs px-2 py-1 bg-current/20 rounded">{alarm.severity}</span>
                  </div>
                  <div className="text-xs space-y-1">
                    <div>Current: {alarm.current_value.toFixed(2)}</div>
                    <div>Distance: {alarm.sigma_distance.toFixed(1)}σ</div>
                    <div>Impact: {alarm.yield_impact.toFixed(1)}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Recommendations */}
          <div className="card">
            <h2 className="text-xl font-bold mb-4">AI Recommendations</h2>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {recommendations.map(rec => (
                <div key={rec.id} className="border border-slate-600 rounded-lg p-3 bg-slate-700/30">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`font-semibold text-sm ${getPriorityColor(rec.priority)}`}>
                      {rec.title}
                    </span>
                    <span className="text-xs px-2 py-1 bg-slate-600 rounded">{rec.type}</span>
                  </div>
                  <div className="text-xs text-slate-400 mb-2">{rec.description}</div>
                  <div className="flex items-center justify-between text-xs">
                    <span>Confidence: {(rec.confidence * 100).toFixed(0)}%</span>
                    <span>Improvement: +{rec.expected_improvement.toFixed(1)}%</span>
                  </div>
                  {rec.requires_approval && (
                    <div className="mt-2 flex gap-2">
                      <button className="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs py-1 px-2 rounded">
                        Approve
                      </button>
                      <button className="flex-1 bg-red-600 hover:bg-red-700 text-white text-xs py-1 px-2 rounded">
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard