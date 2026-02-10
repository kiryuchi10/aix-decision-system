import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';

// Pages
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import Papers from './pages/Papers';
import Datasets from './pages/Datasets';
import Generator from './pages/Generator';
import Chat from './pages/Chat';
import MLModelComparison from './pages/MLModelComparison';
import DoEPlanner from './pages/DoEPlanner';
import SPCPage from './pages/SPC';
import FDCPage from './pages/FDC';
import CouplingPage from './pages/Coupling';
import InterlockPage from './pages/Interlock';
import SettingsPage from './pages/Settings';
import ProfilePage from './pages/Profile';
import ProcessAnalysisPage from './pages/ProcessAnalysis';
import MLPipelinePage from './pages/MLPipeline';
import VizAutomationPage from './pages/VizAutomation';
import ProcessWindowPage from './pages/ProcessWindow';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          {/* Protected Routes with Layout */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

const AppLayout: React.FC = () => {
  return (
    <div className="flex min-h-screen bg-slate-900">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col">
        <TopBar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/spc" element={<SPCPage />} />
            <Route path="/fdc" element={<FDCPage />} />
            <Route path="/coupling" element={<CouplingPage />} />
            <Route path="/interlock" element={<InterlockPage />} />
            <Route path="/process-analysis" element={<ProcessAnalysisPage />} />
            <Route path="/ml-pipeline" element={<MLPipelinePage />} />
            <Route path="/viz-automation" element={<VizAutomationPage />} />
            <Route path="/papers" element={<Papers />} />
            <Route path="/datasets" element={<Datasets />} />
            <Route path="/generator" element={<Generator />} />
            <Route path="/data-generator" element={<Generator />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/window" element={<ProcessWindowPage />} />
            <Route path="/doe" element={<DoEPlanner />} />
            <Route path="/ml-comparison" element={<MLModelComparison />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export default App;
