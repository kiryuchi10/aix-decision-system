import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import MLModelComparison from './pages/MLModelComparison'
import Sidebar from './components/Sidebar'

function App() {
  return (
    <Router>
      <div className="flex min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <Sidebar />
        <main className="flex-1 ml-64">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/ml-comparison" element={<MLModelComparison />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App