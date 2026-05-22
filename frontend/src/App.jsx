import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import SimulatePage from './pages/SimulatePage'
import WorldPage from './pages/WorldPage'
import ReportPage from './pages/ReportPage'
import ChatPage from './pages/ChatPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="simulate/:sessionId" element={<SimulatePage />} />
          <Route path="world/:sessionId" element={<WorldPage />} />
          <Route path="report/:sessionId" element={<ReportPage />} />
          <Route path="chat/:sessionId" element={<ChatPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
