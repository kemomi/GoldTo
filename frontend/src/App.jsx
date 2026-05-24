import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import SimulatePage from './pages/SimulatePage'
import ReportPage from './pages/ReportPage'
import ChatPage from './pages/ChatPage'
import SettingsPage from './pages/SettingsPage'
import BriefingHistoryPage from './pages/BriefingHistoryPage'
import BriefingDetailPage from './pages/BriefingDetailPage'
import DashboardPage from './pages/DashboardPage'
import AlertHistoryPage from './pages/AlertHistoryPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="simulate/:sessionId" element={<SimulatePage />} />
          <Route path="report/:sessionId" element={<ReportPage />} />
          <Route path="chat/:sessionId" element={<ChatPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="alerts" element={<AlertHistoryPage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="briefings" element={<BriefingHistoryPage />} />
          <Route path="briefing/:briefingId" element={<BriefingDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
