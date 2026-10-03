import React from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  GitCompare,
  ArrowLeftRight,
  AlertTriangle,
  Sparkles,
  Building2,
  FileText,
  MessageSquare,
  ShieldCheck,
  Settings,
  Shield,
  User,
  Database,
} from 'lucide-react'
import { cn } from '../../utils/cn'

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/reconciliation', label: 'Reconciliation', icon: GitCompare },
  { path: '/transactions', label: 'Transactions', icon: ArrowLeftRight },
  { path: '/exceptions', label: 'Exceptions', icon: AlertTriangle },
  { path: '/tax-intelligence', label: 'Tax Intelligence', icon: Sparkles },
  { path: '/vendors', label: 'Vendors', icon: Building2 },
  { path: '/reports', label: 'Reports', icon: FileText },
  { path: '/whatsapp', label: 'WhatsApp', icon: MessageSquare },
  { path: '/audit', label: 'Audit', icon: ShieldCheck },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export const AppLayout: React.FC = () => {
  const location = useLocation()

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 select-none">
        {/* Logo / Brand Header */}
        <div className="h-16 flex items-center gap-3 px-5 border-b border-slate-800">
          <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center text-white font-bold text-base shadow-sm">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <div className="text-white font-semibold text-sm tracking-wide leading-none">
              TAXPULSE AI
            </div>
            <div className="text-[11px] text-slate-400 mt-1 leading-none">
              Tax Reconciliation Engine
            </div>
          </div>
        </div>

        {/* 10 Navigation Items */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon
            const isActive =
              location.pathname === item.path ||
              (item.path !== '/dashboard' && location.pathname.startsWith(item.path))

            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/80'
                )}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            )
          })}
        </nav>

        {/* Environment / Tenant Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/40">
          <div className="flex items-center gap-2 px-2 py-1.5 rounded text-xs text-slate-400">
            <Database className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="truncate">TaxPulse Org (Primary)</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Bar */}
        <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0 shadow-sm z-10">
          <div className="flex items-center gap-3">
            <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
              Workspace
            </span>
            <span className="text-sm font-semibold text-slate-800">
              Tax Compliance & Audit
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Engine Online
            </div>

            <div className="h-4 w-px bg-slate-200" />

            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-slate-600">
                <User className="w-4 h-4" />
              </div>
              <span className="text-xs font-medium text-slate-700">Analyst</span>
            </div>
          </div>
        </header>

        {/* Dynamic Route Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
