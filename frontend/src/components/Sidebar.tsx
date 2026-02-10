import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Brain, 
  Settings, 
  BarChart3,
  FileText,
  Database,
  Sparkles,
  MessageSquare,
  AlertTriangle,
  Image,
  Link as LinkIcon,
  Shield
} from 'lucide-react'

const Sidebar: React.FC = () => {
  const location = useLocation()
  
  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'SPC Center', href: '/spc', icon: BarChart3 },
    { name: 'FDC Sentinel', href: '/fdc', icon: AlertTriangle },
    { name: 'Process Analysis', href: '/process-analysis', icon: Database },
    { name: 'ML Pipeline', href: '/ml-pipeline', icon: Brain },
    { name: 'Coupling Control', href: '/coupling', icon: LinkIcon },
    { name: 'STOP/Release AI', href: '/interlock', icon: Shield },
    { name: 'Viz Automation', href: '/viz-automation', icon: Image },
    { name: 'Data Generator', href: '/data-generator', icon: Sparkles },
    { name: 'Process Window', href: '/window', icon: LayoutDashboard },
    { name: 'DoE Planner', href: '/doe', icon: BarChart3 },
    { name: 'Papers', href: '/papers', icon: FileText },
    { name: 'Datasets', href: '/datasets', icon: Database },
    { name: 'Chat', href: '/chat', icon: MessageSquare },
    { name: 'Settings', href: '/settings', icon: Settings },
  ]
  
  return (
    <div className="fixed inset-y-0 left-0 z-50 w-64 bg-slate-900/95 backdrop-blur border-r border-slate-700">
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="flex items-center px-6 py-4 border-b border-slate-700">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AiX</span>
            </div>
            <div className="ml-3">
              <h1 className="text-lg font-bold text-white">AiX Decision</h1>
              <p className="text-xs text-slate-400">System v1.0</p>
            </div>
          </div>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </Link>
            )
          })}
        </nav>
        
        {/* Status */}
        <div className="px-4 py-4 border-t border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="ml-2 text-xs text-slate-400">System Online</span>
            </div>
            <span className="text-xs text-slate-500">v1.0.0</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Sidebar