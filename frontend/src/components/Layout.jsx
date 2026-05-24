import React from 'react'
import { Outlet, NavLink, useParams, useLocation } from 'react-router-dom'
import { Globe, FileText, MessageCircle, Home, Cpu, Zap, Filter, History } from 'lucide-react'

function NavItem({ to, icon: Icon, label, disabled }) {
  return disabled ? (
    <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 cursor-not-allowed opacity-40">
      <Icon size={18} />
      <span className="text-sm font-medium">{label}</span>
    </div>
  ) : (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm font-medium ${
          isActive
            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
            : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
        }`
      }
    >
      <Icon size={18} />
      <span>{label}</span>
    </NavLink>
  )
}

export default function Layout() {
  const location = useLocation()
  // Extract sessionId from any nested route
  const match = location.pathname.match(/\/(simulate|world|report|chat)\/([^/]+)/)
  const sessionId = match?.[2]

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 flex flex-col" style={{ background: 'var(--dark-800)', borderRight: '1px solid var(--border)' }}>
        {/* Logo */}
        <div className="p-5 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center border border-amber-500/30">
            <Zap size={16} className="text-amber-400" />
          </div>
          <div>
            <div className="font-bold text-white text-sm tracking-wide">CTF Radar</div>
            <div className="text-xs text-slate-500">海外战略情报</div>
          </div>
        </div>

        <nav className="flex-1 px-3 pb-4 flex flex-col gap-1">
          <div className="text-xs text-slate-600 uppercase tracking-wider px-3 py-2 mt-2">导航</div>
          <NavItem to="/" icon={Home} label="首页" />
          <NavItem to="/history" icon={History} label="历史会话" />
          <NavItem to="/worldmonitor" icon={Filter} label="WM 情报筛选" />
          <NavItem to={sessionId ? `/simulate/${sessionId}` : '#'} icon={Cpu} label="会商控制台" disabled={!sessionId} />
          <NavItem to={sessionId ? `/world/${sessionId}` : '#'} icon={Globe} label="专家 Agent" disabled={!sessionId} />
          <NavItem to={sessionId ? `/report/${sessionId}` : '#'} icon={FileText} label="战略简报" disabled={!sessionId} />
          <NavItem to={sessionId ? `/chat/${sessionId}` : '#'} icon={MessageCircle} label="追问验证" disabled={!sessionId} />
        </nav>

        {/* Footer */}
        <div className="p-4 border-t" style={{ borderColor: 'var(--border)' }}>
          {sessionId && (
            <div className="text-xs text-slate-500">
              <div className="text-amber-500/60 mb-1">当前会话</div>
              <div className="font-mono text-slate-400">{sessionId}</div>
            </div>
          )}
          <div className="text-xs text-slate-600 mt-2">v1.0.0</div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto dot-grid">
        <Outlet />
      </main>
    </div>
  )
}
